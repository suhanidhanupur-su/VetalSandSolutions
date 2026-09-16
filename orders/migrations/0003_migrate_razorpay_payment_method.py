from django.db import migrations, models


def migrate_razorpay_payment_method(apps, schema_editor):
	Order = apps.get_model('orders', 'Order')
	Order.objects.filter(payment_method='razorpay').update(payment_method='online')


class Migration(migrations.Migration):

	dependencies = [
		('orders', '0002_order_payment_method'),
	]

	operations = [
		migrations.RunPython(migrate_razorpay_payment_method, migrations.RunPython.noop),
		migrations.AlterField(
			model_name='order',
			name='payment_method',
			field=models.CharField(
				choices=[('cod', 'Cash on Delivery'), ('online', 'Online Payment')],
				default='cod',
				max_length=20,
			),
		),
	]