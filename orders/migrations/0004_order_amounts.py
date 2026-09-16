from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_migrate_razorpay_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]