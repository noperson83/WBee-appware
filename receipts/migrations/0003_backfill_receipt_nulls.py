from django.db import migrations


def set_nulls(apps, schema_editor):
    Receipt = apps.get_model('receipts', 'Receipt')
    Receipt.objects.filter(service_location__isnull=True).update(service_location=None)
    Receipt.objects.filter(trip__isnull=True).update(trip=None)


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0002_receipt_service_location_receipt_trip_and_more'),
    ]

    operations = [
        migrations.RunPython(set_nulls, migrations.RunPython.noop),
    ]
