from django.db import migrations, models
import django.contrib.auth.models

class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0002_alter_worker_company'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='Groups this worker belongs to', related_name='worker_set', to='auth.group'),
        ),
        migrations.AddField(
            model_name='worker',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this worker', related_name='worker_set', to='auth.permission'),
        ),
    ]
