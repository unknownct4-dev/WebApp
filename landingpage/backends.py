from django.contrib.auth.backends import BaseBackend  # Base class for custom authentication backends
from django.contrib.auth import get_user_model         # Returns the active user model (CustomUser in this project)

# Get the custom user model defined in settings.AUTH_USER_MODEL
UserModel = get_user_model()


class StudentBackend(BaseBackend):
    """
    Custom authentication backend that allows students to log in
    using their id_number and password instead of a username.

    Registered in settings.AUTHENTICATION_BACKENDS so Django tries it
    before the default ModelBackend.
    """

    def authenticate(self, request, id_number=None, password=None, **kwargs):
        """
        Try to find a student with the given id_number and verify their password.
        Returns the user object on success, or None if authentication fails.
        """
        # If either credential is missing, this backend cannot authenticate
        if id_number is None or password is None:
            return None

        try:
            # Look up the student by their unique ID number
            user = UserModel.objects.get(id_number=id_number, role='student')
        except UserModel.DoesNotExist:
            # Run the default password hasher anyway to prevent timing attacks
            # (an attacker cannot tell whether the id_number exists based on response time)
            UserModel().set_password(password)
            return None

        # Verify the submitted password against the stored hash
        if user.check_password(password) and self.user_can_authenticate(user):
            return user  # Authentication succeeded

        return None  # Password did not match

    def get_user(self, user_id):
        """
        Retrieve a user by their primary key.
        Called by Django's session framework to reload the user on each request.
        """
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None  # User no longer exists in the database

        # Only return the user if their account is active
        return user if self.user_can_authenticate(user) else None

    def user_can_authenticate(self, user):
        """
        Return True if the user is allowed to log in.
        Rejects users whose is_active flag is explicitly set to False.
        """
        is_active = getattr(user, 'is_active', None)
        # Allow login if is_active is True or not set (None means no restriction)
        return is_active or is_active is None
