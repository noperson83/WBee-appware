from django.contrib.auth.mixins import UserPassesTestMixin, PermissionRequiredMixin


class ProjectAccessMixin(UserPassesTestMixin):
    """Object-level access checks for Project views."""

    def test_func(self):
        user = self.request.user

        # Allow all active users to view pages with safe methods
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return user.is_authenticated and user.is_active

        if not hasattr(self, "get_object"):
            return user.is_authenticated

        try:
            project = self.get_object()

            if user.is_superuser:
                return True

            if hasattr(user, "business_category") and project.business_category:
                if user.business_category != project.business_category:
                    return False

            if user.role == "admin":
                return True
            elif user.role == "project_manager":
                return (
                    project.project_manager == user
                    or project.estimator == user
                    or user in project.team_leads.all()
                )
            elif user.role == "supervisor":
                return (
                    project.supervisor == user
                    or user in project.team_leads.all()
                    or user in project.team_members.all()
                )
            elif user.role == "worker":
                return user in project.team_members.all()
            elif user.role == "staff":
                return True
            elif user.role == "client":
                return (
                    hasattr(user, "client")
                    and project.primary_location.client == user.client
                )

            return False
        except (AttributeError, TypeError):
            return self.request.user.is_authenticated


class ProjectPermissionMixin(PermissionRequiredMixin):
    """Permission mixin for project-level operations."""

    def has_permission(self):
        if not super().has_permission():
            return False

        if hasattr(self, "get_object"):
            try:
                project = self.get_object()
            except Exception:
                return False

            user = self.request.user
            return user.is_superuser or project.project_manager == user

        return True


__all__ = ["ProjectAccessMixin", "ProjectPermissionMixin"]
