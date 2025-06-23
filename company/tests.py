from django.test import TestCase

from .models import Company, Department


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
