import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gyms", "0001_initial"),
        ("members", "0001_initial"),
        ("payments", "0006_remove_unique_completed_payment_per_subscription"),
        ("subscriptions", "0005_alter_subscription_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(max_length=30)),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("status", models.CharField(choices=[("UNPAID", "Unpaid"), ("PARTIALLY_PAID", "Partially paid"), ("PAID", "Paid"), ("VOID", "Void")], default="UNPAID", max_length=20)),
                ("issued_on", models.DateField(default=django.utils.timezone.localdate)),
                ("due_on", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("gym", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to="gyms.gym")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to="members.member")),
                ("subscription", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="invoice", to="subscriptions.subscription")),
            ],
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(fields=("gym", "number"), name="unique_invoice_number_per_gym"),
        ),
    ]
