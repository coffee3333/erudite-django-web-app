import uuid
from django.db import migrations, models
from django.db import connection


def populate_lti_tokens(apps, schema_editor):
    Course = apps.get_model('core', 'Course')
    for course in Course.objects.filter(lti_token=None):
        course.lti_token = uuid.uuid4()
        course.save(update_fields=['lti_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_course_status_courseenrollment'),
    ]

    operations = [
        # Step 1: add nullable (no unique constraint yet)
        migrations.AddField(
            model_name='course',
            name='lti_token',
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: populate unique UUIDs for existing rows (works on both SQLite and PostgreSQL)
        migrations.RunPython(populate_lti_tokens, migrations.RunPython.noop),
        # Step 3: make it non-nullable and unique
        migrations.AlterField(
            model_name='course',
            name='lti_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
