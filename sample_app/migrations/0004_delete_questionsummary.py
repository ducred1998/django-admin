# Generated by Django 4.0.10 on 2023-08-24 09:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sample_app', '0003_questionsummary_authorclone'),
    ]

    operations = [
        migrations.DeleteModel(
            name='QuestionSummary',
        ),
    ]