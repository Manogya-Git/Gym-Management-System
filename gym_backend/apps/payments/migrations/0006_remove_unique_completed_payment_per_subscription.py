from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0005_payment_unique_completed_payment_per_subscription"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="payment",
            name="unique_completed_payment_per_subscription",
        ),
    ]
