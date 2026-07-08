# products/migrations/0001_initial.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        # Explicit dependency on the last known state of the old app
        ('store', '0003_order_service_fee'), 
    ]

    state_operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='collections/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name'], 'verbose_name': 'Collection', 'verbose_name_plural': 'Collections'},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('is_available', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(choices=[('hoodies', 'Hoodies'), ('tees', 'T-Shirts'), ('accessories', 'Accessories'), ('limited', 'Limited Drops'), ('other', 'Other')], db_index=True, default='other', max_length=50)),
                ('collection', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='products.collection')),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/images/')),
                ('alt_text', models.CharField(blank=True, null=True, max_length=255)),
                ('is_primary', models.BooleanField(blank=True, default=False, null=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.product')),
            ],
            options={'ordering': ['order', 'id'], 'verbose_name': 'Product Image', 'verbose_name_plural': 'Product Images'},
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField(max_length=50)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('additional_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.product')),
            ],
            options={'verbose_name': 'Size Variant', 'verbose_name_plural': 'Size Variants', 'unique_together': {('product', 'size')}},
        ),
    ]

    operations = [
        # Tells Django: Update state tracker, but leave database tables untouched
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
