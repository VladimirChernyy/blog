# Generated by Django 2.2.16 on 2023-10-23 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата публикации'),
        ),
    ]