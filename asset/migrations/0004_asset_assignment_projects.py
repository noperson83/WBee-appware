from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("asset", "0003_initial"),
        ("project", "0001_initial"),
        ("location", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="projects",
            field=models.ManyToManyField(
                blank=True,
                related_name="assets",
                through="asset.AssetAssignment",
                through_fields=("asset", "assigned_to_project"),
                to="project.project",
            ),
        ),
        migrations.AddField(
            model_name="assetassignment",
            name="assigned_location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_assignments",
                to="location.location",
            ),
        ),
        migrations.AddField(
            model_name="assetassignment",
            name="status",
            field=models.CharField(default="active", max_length=20),
        ),
    ]
