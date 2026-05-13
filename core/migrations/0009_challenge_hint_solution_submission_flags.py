from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_lti_token_to_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='hint',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='challenge',
            name='solution_explanation',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='submission',
            name='hint_used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='submission',
            name='solution_revealed',
            field=models.BooleanField(default=False),
        ),
    ]
