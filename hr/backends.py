from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmployeeAuthBackend(ModelBackend):
    """Authenticate only active workers flagged as employees."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and user.is_active and getattr(user, "is_employee", False):
            return user
        return None

    def user_can_authenticate(self, user):
        return user.is_active and getattr(user, "is_employee", False)
