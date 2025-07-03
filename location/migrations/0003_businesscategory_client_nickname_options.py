from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("location", "0002_businesscategory_client_nickname_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscategory",
            name="client_nickname_options",
            field=models.JSONField(
                default=list,
                blank=True,
                help_text="Optional alternate names for clients (Bar, Restaurant, etc.)",
            ),
        ),
    ]
