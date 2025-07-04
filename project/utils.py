"""Utility functions for the project app."""

from typing import Optional, Dict, Any

from .models import Project


def generate_job_number(business_category: Optional["BusinessCategory"] = None) -> str:
    """Return a unique job number.

    If ``business_category`` is provided, the sequence is scoped to
    that category. Job numbers are numeric and zero padded.
    """
    qs = Project.objects.all()
    if business_category:
        qs = qs.filter(locations__business_category=business_category)

    last_project = qs.order_by("-job_number").first()
    last_number = 0
    if last_project and last_project.job_number.isdigit():
        last_number = int(last_project.job_number)

    new_number = last_number + 1
    return f"{new_number:04d}"


def calculate_project_metrics(project: Project) -> Dict[str, Any]:
    """Calculate basic metrics for a project."""
    return {
        "profit_margin": project.profit_margin,
        "outstanding_balance": project.outstanding_balance,
        "revenue_to_date": project.revenue_to_date,
        "days_until_due": project.days_until_due,
        "is_overdue": project.is_overdue,
    }
