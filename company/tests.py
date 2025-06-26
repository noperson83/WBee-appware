from django.test import TestCase

from .models import Company, Department, CompanyPartnership


class DepartmentModelTests(TestCase):
    """Tests for the Department model."""

    def test_full_department_path_handles_cycles(self):
        """full_department_path should not recurse infinitely on cycles."""
        company = Company.objects.create(company_name="ACME")
        dept = Department.objects.create(company=company, name="Ops")
        # Introduce a cycle where the department is its own parent
        dept.parent_department = dept
        dept.save()

        # Accessing full_department_path should not raise RecursionError
        try:
            path = dept.full_department_path
        except RecursionError:
            self.fail("full_department_path raised RecursionError with a cycle")

        self.assertIn("Ops", path)


class CompanyPartnershipTests(TestCase):
    """Tests for company partnership relationships."""

    def test_partner_companies_relation(self):
        c1 = Company.objects.create(company_name="Alpha")
        c2 = Company.objects.create(company_name="Beta")

        CompanyPartnership.objects.create(from_company=c1, to_company=c2)

        self.assertIn(c2, c1.partner_companies.all())
        self.assertNotIn(c1, c2.partner_companies.all())
