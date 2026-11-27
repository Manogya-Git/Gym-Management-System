from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.subscriptions.models import Subscription
from .models import Invoice, Payment


def _get_or_create_invoice(*, subscription, plan):
    invoice = Invoice.objects.select_for_update().filter(
        subscription=subscription
    ).first()
    if invoice is not None:
        return invoice

    today = timezone.localdate()
    return Invoice.objects.create(
        gym=subscription.gym,
        member=subscription.member,
        subscription=subscription,
        number=f"INV-{today.year}-{subscription.pk:06d}",
        total=plan.price,
        issued_on=today,
    )


def _sync_invoice_status(invoice):
    paid_total = invoice.payments.filter(
        status=Payment.Status.COMPLETED,
    ).aggregate(total=Sum("amount"))["total"] or 0

    if paid_total >= invoice.total:
        invoice.status = Invoice.Status.PAID
    elif paid_total > 0:
        invoice.status = Invoice.Status.PARTIALLY_PAID
    else:
        invoice.status = Invoice.Status.UNPAID
    invoice.save(update_fields=["status", "updated_at"])


def _activate_or_renew_subscription(*, subscription, explicit_plan=None):
    """Sync subscription status and dates when a payment completes."""
    today = timezone.localdate()
    effective_plan = explicit_plan or subscription.plan

    if subscription.status != Subscription.Status.ACTIVE or subscription.end_date < today:
        has_other_active = Subscription.objects.filter(
            gym=subscription.gym,
            member=subscription.member,
            status=Subscription.Status.ACTIVE,
        ).exclude(pk=subscription.pk).exists()
        if has_other_active:
            raise ValidationError("This member already has an active subscription.")

        subscription.start_date = today
        subscription.end_date = today + timedelta(days=effective_plan.duration_days)
        subscription.status = Subscription.Status.ACTIVE
        subscription.plan = effective_plan
        subscription.price = effective_plan.price
        subscription.save(
            update_fields=["start_date", "end_date", "status", "plan", "price", "updated_at"]
        )
        return

    if explicit_plan is not None and explicit_plan.pk != subscription.plan_id:
        subscription.end_date = subscription.end_date + timedelta(
            days=explicit_plan.duration_days
        )
        subscription.plan = explicit_plan
        subscription.price = explicit_plan.price
        subscription.save(update_fields=["end_date", "plan", "price", "updated_at"])


@transaction.atomic
def create_payment(*, gym, member, subscription, payment_method, plan=None):
    """Create a validated cash payment and update the subscription lifecycle."""
    try:
        locked_subscription = Subscription.objects.select_for_update().get(
            id=subscription.id,
            gym=gym,
        )
    except Subscription.DoesNotExist:
        raise ValidationError("This subscription does not belong to your gym.")

    if locked_subscription.member_id != member.id:
        raise ValidationError("This subscription does not belong to this member.")

    if Payment.objects.filter(
        gym=gym,
        member=locked_subscription.member,
        status=Payment.Status.PENDING,
    ).exists():
        raise ValidationError("This member already has a pending renewal payment.")

    if Payment.objects.filter(
        subscription=locked_subscription,
        status=Payment.Status.COMPLETED,
    ).exists():
        raise ValidationError("This subscription already has a completed payment.")

    if payment_method != Payment.PaymentMethod.CASH:
        raise ValidationError("Only cash payments are allowed.")

    effective_plan = plan or locked_subscription.plan
    if effective_plan is not None and not effective_plan.is_active:
        raise ValidationError("Cannot use an inactive plan.")

    invoice = _get_or_create_invoice(
        subscription=locked_subscription,
        plan=effective_plan,
    )
    amount = effective_plan.price if effective_plan else locked_subscription.price

    payment = Payment.objects.create(
        gym=gym,
        member=locked_subscription.member,
        subscription=locked_subscription,
        invoice=invoice,
        plan=effective_plan,
        amount=amount,
        payment_method=payment_method,
        status=Payment.Status.COMPLETED,
        paid_at=timezone.now(),
    )

    _sync_invoice_status(invoice)
    if invoice.status == Invoice.Status.PAID:
        _activate_or_renew_subscription(subscription=locked_subscription, explicit_plan=plan)

    return payment


@transaction.atomic
def update_payment_status(*, payment, new_status):
    """Transition payment status and sync the linked subscription."""
    locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
    locked_subscription = Subscription.objects.select_for_update().get(
        pk=locked_payment.subscription_id
    )
    invoice = locked_payment.invoice or _get_or_create_invoice(
        subscription=locked_subscription,
        plan=locked_payment.plan or locked_subscription.plan,
    )
    if locked_payment.invoice_id is None:
        locked_payment.invoice = invoice

    if new_status == Payment.Status.COMPLETED:
        locked_payment.status = Payment.Status.COMPLETED
        locked_payment.paid_at = timezone.now()
        locked_payment.save(update_fields=["invoice", "status", "paid_at", "updated_at"])

        _sync_invoice_status(invoice)
        if invoice.status == Invoice.Status.PAID:
            _activate_or_renew_subscription(
                subscription=locked_subscription,
                explicit_plan=locked_payment.plan,
            )
    elif new_status == Payment.Status.REFUNDED:
        locked_payment.status = Payment.Status.REFUNDED
        locked_payment.save(update_fields=["invoice", "status", "updated_at"])
        _sync_invoice_status(invoice)

        if locked_subscription.status == Subscription.Status.ACTIVE:
            locked_subscription.status = Subscription.Status.CANCELLED
            locked_subscription.save(update_fields=["status", "updated_at"])
    else:
        locked_payment.status = new_status
        locked_payment.save(update_fields=["invoice", "status", "updated_at"])
        _sync_invoice_status(invoice)

    return locked_payment
