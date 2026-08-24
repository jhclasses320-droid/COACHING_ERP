from django.db import migrations


def repair_exam_fields(apps, schema_editor):

    connection = schema_editor.connection

    with connection.cursor() as cursor:

        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                "students_exam"
            )
        }

        if "status" not in columns:
            schema_editor.execute(
                """
                ALTER TABLE students_exam
                ADD COLUMN status varchar(10) NOT NULL DEFAULT 'DRAFT'
                """
            )

        if "published_at" not in columns:
            schema_editor.execute(
                """
                ALTER TABLE students_exam
                ADD COLUMN published_at datetime NULL
                """
            )


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0020_exam_published_at_exam_status"),
    ]

    operations = [
        migrations.RunPython(
            repair_exam_fields,
            migrations.RunPython.noop,
        ),
    ]