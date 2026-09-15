# Manual migration: preserve existing Question topic relationships
# by renaming the field instead of removing and re-adding it.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0025_alter_exam_topic'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='topic',
            new_name='chapter',
        ),

        migrations.AlterField(
            model_name='question',
            name='chapter',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='questions_as_chapter',
                to='students.topic',
                verbose_name='Chapter',
            ),
        ),
    ]

