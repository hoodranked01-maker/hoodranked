from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_receiver_address_code_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="shipping_fee",
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipping_courier",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipbubble_request_token",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipbubble_service_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipbubble_courier_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="tracking_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="tracking_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipbubble_status",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
