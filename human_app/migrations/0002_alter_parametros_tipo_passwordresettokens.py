# Generated by Django 5.0.3 on 2024-06-24 17:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('human_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='parametros',
            name='tipo',
            field=models.CharField(choices=[('DATE', 'DATE'), ('TEXT', 'TEXT'), ('INTEGER', 'INTEGER'), ('FLOAT', 'FLOAT'), ('BOOLEAN', 'BOOLEAN')], default='TEXT', max_length=255),
        ),
        migrations.CreateModel(
            name='PasswordResetTokens',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_in', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'password_reset',
            },
        ),
    ]
