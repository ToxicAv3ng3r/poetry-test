# Generated by Django 2.2.16 on 2022-04-20 15:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_auto_20220420_1838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='likes',
            name='comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='posts.Comment', verbose_name='Понравившийся комментарий'),
        ),
        migrations.AlterField(
            model_name='likes',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='posts.Post', verbose_name='Понравившийся пост'),
        ),
    ]
