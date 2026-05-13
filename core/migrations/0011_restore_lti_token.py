import uuid
from django.db import migrations, models


def populate_lti_tokens(apps, schema_editor):
    Course = apps.get_model('core', 'Course')
    for course in Course.objects.all():
        course.lti_token = uuid.uuid4()
        course.save(update_fields=['lti_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_course_lti_token_courseenrollment_lti_source'),
    ]

    operations = [
        # Step 1: add nullable (no unique yet)
        migrations.AddField(
            model_name='course',
            name='lti_token',
            field=models.UUIDField(null=True, blank=True, editable=False,
                                   help_text='Unique token used by Moodle to identify this course in LTI custom parameters.'),
        ),
        # Step 2: populate unique UUIDs for existing rows
        migrations.RunPython(populate_lti_tokens, migrations.RunPython.noop),
        # Step 3: make it non-nullable and unique
        migrations.AlterField(
            model_name='course',
            name='lti_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                                   help_text='Unique token used by Moodle to identify this course in LTI custom parameters.'),
        ),
    ]
