from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Sum


def attach_existing_payments_to_invoices(apps, schema_editor):
    Invoice = apps.get_model("payments", "Invoice")
    Payment = apps.get_model("payments", "Payment")
    Subscription = apps.get_model("subscriptions", "Subscription")
    database = schema_editor.connection.alias

    for subscription in Subscription.objects.using(database).all().iterator():
        payments = Payment.objects.using(database).filter(
            subscription_id=subscription.pk,
        )
        paid_total = payments.filter(status="completed").aggregate(
            total=Sum("amount"),
        )["total"] or Decimal("0.00")

        if paid_total >= subscription.price:
            status = "PAID"
        elif paid_total > 0:
            status = "PARTIALLY_PAID"
        else:
            status = "UNPAID"

        invoice = Invoice.objects.using(database).create(
            gym_id=subscription.gym_id,
            member_id=subscription.member_id,
            subscription_id=subscription.pk,
            number=f"LEGACY-{subscription.pk}",
            total=subscription.price,
            status=status,
            issued_on=subscription.start_date,
        )
        payments.update(invoice_id=invoice.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0007_invoice"),
        ("subscriptions", "0005_alter_subscription_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="invoice",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payments",
                to="payments.invoice",
            ),
        ),
        migrations.RunPython(attach_existing_payments_to_invoices, migrations.RunPython.noop),
    ]
