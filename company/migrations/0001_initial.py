# Generated by Django 5.2 on 2025-06-20 04:04

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("location", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "company_name",
                    models.CharField(
                        db_index=True,
                        help_text="Company/Organization name",
                        max_length=200,
                    ),
                ),
                (
                    "legal_name",
                    models.CharField(
                        blank=True,
                        help_text="Legal business name if different from display name",
                        max_length=200,
                    ),
                ),
                (
                    "company_url",
                    models.URLField(blank=True, help_text="Company website"),
                ),
                (
                    "logo",
                    models.ImageField(
                        blank=True,
                        help_text="Company logo",
                        null=True,
                        upload_to="uploads/company/logos/%Y/%m/%d/",
                    ),
                ),
                (
                    "button_image",
                    models.ImageField(
                        blank=True,
                        help_text="Button/icon image",
                        null=True,
                        upload_to="uploads/company/buttons/%Y/%m/%d/",
                    ),
                ),
                (
                    "brand_colors",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Brand colors (primary, secondary, etc.)",
                    ),
                ),
                (
                    "business_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("corporation", "Corporation"),
                            ("llc", "LLC"),
                            ("partnership", "Partnership"),
                            ("sole_prop", "Sole Proprietorship"),
                            ("non_profit", "Non-Profit"),
                            ("government", "Government Agency"),
                        ],
                        help_text="Legal business structure",
                        max_length=20,
                    ),
                ),
                (
                    "tax_id",
                    models.CharField(
                        blank=True, help_text="EIN or Tax ID number", max_length=20
                    ),
                ),
                (
                    "business_license",
                    models.CharField(
                        blank=True, help_text="Business license number", max_length=100
                    ),
                ),
                (
                    "primary_contact_name",
                    models.CharField(
                        help_text="Primary contact person", max_length=200
                    ),
                ),
                (
                    "primary_contact_title",
                    models.CharField(
                        blank=True, help_text="Title of primary contact", max_length=100
                    ),
                ),
                (
                    "primary_phone",
                    models.CharField(
                        blank=True,
                        help_text="Primary phone number",
                        max_length=17,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                                regex="^\\+?1?\\d{9,15}$",
                            )
                        ],
                    ),
                ),
                (
                    "primary_email",
                    models.EmailField(
                        blank=True, help_text="Primary business email", max_length=254
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Company description and overview",
                        max_length=2000,
                    ),
                ),
                (
                    "mission_statement",
                    models.TextField(
                        blank=True,
                        help_text="Company mission statement",
                        max_length=1000,
                    ),
                ),
                (
                    "founded_date",
                    models.DateField(
                        blank=True, help_text="Date company was founded", null=True
                    ),
                ),
                (
                    "current_year_revenue",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Current year revenue",
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "previous_year_revenue",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Previous year revenue",
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "timezone",
                    models.CharField(
                        choices=[
                            ("US/Eastern", "Eastern Time"),
                            ("US/Central", "Central Time"),
                            ("US/Mountain", "Mountain Time"),
                            ("US/Pacific", "Pacific Time"),
                            ("US/Alaska", "Alaska Time"),
                            ("US/Hawaii", "Hawaii Time"),
                        ],
                        default="US/Pacific",
                        help_text="Company timezone",
                        max_length=20,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[
                            ("USD", "US Dollar ($)"),
                            ("CAD", "Canadian Dollar (C$)"),
                            ("EUR", "Euro (€)"),
                            ("GBP", "British Pound (£)"),
                        ],
                        default="USD",
                        help_text="Primary currency",
                        max_length=3,
                    ),
                ),
                (
                    "fiscal_year_start",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Fiscal year start month (1=January, 4=April, etc.)",
                    ),
                ),
                (
                    "default_payment_terms",
                    models.CharField(
                        default="Net 30",
                        help_text="Default payment terms for invoices",
                        max_length=50,
                    ),
                ),
                (
                    "is_multi_location",
                    models.BooleanField(
                        default=False,
                        help_text="Does this company have multiple locations?",
                    ),
                ),
                (
                    "custom_fields",
                    models.JSONField(
                        blank=True, default=dict, help_text="Custom company data"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Is company active?"),
                ),
                (
                    "business_category",
                    models.ForeignKey(
                        blank=True,
                        help_text="Primary business category",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="location.businesscategory",
                    ),
                ),
                (
                    "parent_company",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent company if this is a subsidiary",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subsidiaries",
                        to="company.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "Company",
                "verbose_name_plural": "Companies",
                "ordering": ["company_name"],
            },
        ),
        migrations.CreateModel(
            name="CompanySettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "invoice_prefix",
                    models.CharField(
                        default="INV",
                        help_text="Prefix for invoice numbers",
                        max_length=10,
                    ),
                ),
                (
                    "next_invoice_number",
                    models.PositiveIntegerField(
                        default=1000, help_text="Next invoice number to use"
                    ),
                ),
                (
                    "project_prefix",
                    models.CharField(
                        default="P",
                        help_text="Prefix for project numbers",
                        max_length=10,
                    ),
                ),
                (
                    "next_project_number",
                    models.PositiveIntegerField(
                        default=1000, help_text="Next project number to use"
                    ),
                ),
                ("smtp_server", models.CharField(blank=True, max_length=200)),
                ("smtp_port", models.PositiveIntegerField(default=587)),
                ("smtp_username", models.CharField(blank=True, max_length=200)),
                ("smtp_use_tls", models.BooleanField(default=True)),
                (
                    "date_format",
                    models.CharField(
                        default="MM/DD/YYYY",
                        help_text="Preferred date format",
                        max_length=20,
                    ),
                ),
                (
                    "notification_settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Email and notification preferences",
                    ),
                ),
                (
                    "integrations",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Third-party integration settings",
                    ),
                ),
                (
                    "company",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="settings",
                        to="company.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "Company Settings",
                "verbose_name_plural": "Company Settings",
            },
        ),
        migrations.CreateModel(
            name="Office",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "office_name",
                    models.CharField(
                        help_text="Office name (Tucson, Phoenix, Headquarters, etc.)",
                        max_length=200,
                    ),
                ),
                (
                    "office_code",
                    models.CharField(
                        blank=True,
                        help_text="Short code for this office (TUC, PHX, HQ)",
                        max_length=10,
                    ),
                ),
                (
                    "office_type",
                    models.CharField(
                        choices=[
                            ("headquarters", "Headquarters"),
                            ("branch", "Branch Office"),
                            ("warehouse", "Warehouse"),
                            ("retail", "Retail Location"),
                            ("field_office", "Field Office"),
                            ("remote", "Remote Office"),
                        ],
                        default="branch",
                        max_length=20,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Office description and details",
                        max_length=1000,
                    ),
                ),
                (
                    "employee_capacity",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum number of employees", null=True
                    ),
                ),
                (
                    "square_footage",
                    models.PositiveIntegerField(
                        blank=True, help_text="Office size in square feet", null=True
                    ),
                ),
                (
                    "office_manager",
                    models.CharField(
                        blank=True, help_text="Office manager name", max_length=200
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True, help_text="Office phone number", max_length=17
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, help_text="Office email address", max_length=254
                    ),
                ),
                (
                    "operating_hours",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Operating hours by day of week",
                    ),
                ),
                (
                    "opened_date",
                    models.DateField(
                        blank=True, help_text="Date office opened", null=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        help_text="Company this office belongs to",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offices",
                        to="company.company",
                    ),
                ),
            ],
            options={
                "ordering": ["company", "office_name"],
            },
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(help_text="Department name", max_length=100)),
                (
                    "department_code",
                    models.CharField(
                        blank=True,
                        help_text="Short code for department (SALES, IT, HR)",
                        max_length=10,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Department description and responsibilities",
                        max_length=1000,
                    ),
                ),
                (
                    "department_head",
                    models.CharField(
                        blank=True,
                        help_text="Department head/manager name",
                        max_length=200,
                    ),
                ),
                (
                    "annual_budget",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Annual department budget",
                        max_digits=15,
                        null=True,
                    ),
                ),
                (
                    "cost_center_code",
                    models.CharField(
                        blank=True,
                        help_text="Cost center code for accounting",
                        max_length=20,
                    ),
                ),
                (
                    "is_billable",
                    models.BooleanField(
                        default=True,
                        help_text="Can this department bill time to clients?",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        help_text="Company this department belongs to",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="departments",
                        to="company.company",
                    ),
                ),
                (
                    "parent_department",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent department if this is a sub-department",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_departments",
                        to="company.department",
                    ),
                ),
                (
                    "primary_office",
                    models.ForeignKey(
                        blank=True,
                        help_text="Primary office for this department",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="primary_departments",
                        to="company.office",
                    ),
                ),
            ],
            options={
                "ordering": ["company", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(
                fields=["company_name"], name="company_com_company_949344_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(
                fields=["business_category"], name="company_com_busines_8d17dd_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(
                fields=["is_active"], name="company_com_is_acti_985080_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="office",
            index=models.Index(
                fields=["company", "is_active"], name="company_off_company_dfaecc_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="office",
            index=models.Index(
                fields=["office_type"], name="company_off_office__bcf09a_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="office",
            unique_together={("company", "office_name")},
        ),
        migrations.AddIndex(
            model_name="department",
            index=models.Index(
                fields=["company", "is_active"], name="company_dep_company_683ad7_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="department",
            index=models.Index(
                fields=["parent_department"], name="company_dep_parent__d9e2e6_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="department",
            unique_together={("company", "name")},
        ),
    ]
