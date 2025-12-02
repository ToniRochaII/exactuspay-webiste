# accounts/migrations/0002_notification_usercompany_and_more.py
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(choices=[('SYSTEM', 'System Notification'), ('PAYROLL', 'Payroll Update'), ('APPROVAL', 'Approval Required'), ('DEADLINE', 'Deadline Reminder'), ('EMPLOYEE', 'Employee Action'), ('COMPLIANCE', 'Compliance Alert'), ('SECURITY', 'Security Alert'), ('BILLING', 'Billing Update'), ('SUPPORT', 'Support Response')], default='SYSTEM', max_length=20)),
                ('priority', models.CharField(choices=[('CRITICAL', 'Critical'), ('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low'), ('INFO', 'Informational')], default='INFO', max_length=20)),
                ('action_url', models.URLField(blank=True, null=True)),
                ('action_label', models.CharField(blank=True, max_length=100)),
                ('reference_model', models.CharField(blank=True, max_length=50)),
                ('reference_id', models.IntegerField(blank=True, null=True)),
                ('read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('archived', models.BooleanField(default=False)),
                ('email_sent', models.BooleanField(default=False)),
                ('email_sent_at', models.DateTimeField(blank=True, null=True)),
                ('sms_sent', models.BooleanField(default=False)),
                ('sms_sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='company.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_notifications', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'accounts_notification',
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserCompany',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('OWNER', 'Owner'), ('ADMIN', 'Company Administrator'), ('PAYROLL_MANAGER', 'Payroll Manager'), ('HR_MANAGER', 'HR Manager'), ('FINANCE', 'Finance Team'), ('MANAGER', 'Department Manager'), ('VIEWER', 'Viewer'), ('EMPLOYEE', 'Employee (Self-Service)')], default='VIEWER', max_length=50)),
                ('permissions', models.JSONField(blank=True, default=dict, help_text='Additional permissions specific to this user-company relationship')),
                ('is_active', models.BooleanField(default=True)),
                ('access_granted_at', models.DateTimeField(auto_now_add=True)),
                ('access_revoked_at', models.DateTimeField(blank=True, null=True)),
                ('last_access_at', models.DateTimeField(blank=True, null=True)),
                ('access_granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_access', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authorized_users', to='company.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_access', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'accounts_user_company',
                'verbose_name': 'User Company Access',
                'verbose_name_plural': 'User Company Access',
                'unique_together': {('user', 'company')},
            },
        ),
        migrations.AddField(
            model_name='auditlog',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='company.company'),
        ),
    ]