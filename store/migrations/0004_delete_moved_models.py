# store/migrations/0004_delete_moved_models.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_order_service_fee'),
        ('orders', '0001_initial'), # Ensures new states are initialized first
    ]

    state_operations = [
        migrations.DeleteModel(name='Collection'),
        migrations.DeleteModel(name='Order'),
        migrations.DeleteModel(name='OrderItem'),
        migrations.DeleteModel(name='Variant'),
        migrations.DeleteModel(name='Product'),
        migrations.DeleteModel(name='ProductImage'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
