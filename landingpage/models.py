from django.core.exceptions import ValidationError
from django.db import models                          # Base module for all Django model fields and classes
from django.db.models import Q
from django.contrib.auth.models import AbstractUser   # Django's built-in user model we extend with custom fields


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    Used as AUTH_USER_MODEL so all auth features (login, sessions, permissions) work with our extra fields.
    """

    # Allowed values for the role field
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    # Allowed values for the year_level field
    YEAR_CHOICES = [
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('Summer', 'Summer'),
    ]

    # Determines whether the user is a student or an admin; defaults to student on registration
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    # Unique student ID number used for student login; nullable so admin accounts don't need one
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Optional middle name field not present in AbstractUser
    middle_name = models.CharField(max_length=100, blank=True)

    # Optional profile photo stored in MEDIA_ROOT/profile_pictures/
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    # Foreign key to the student's enrolled course; SET_NULL so deleting a course doesn't delete the user
    course = models.ForeignKey(
        'admindash.Course',
        on_delete=models.SET_NULL,   # If the course is deleted, set this field to NULL instead of deleting the user
        null=True,
        blank=True,
        related_name='students'      # Allows Course.students.all() to get all users in that course
    )

    # The student's current year level (e.g. "1st Semester", "Summer")
    year_level = models.CharField(max_length=15, choices=YEAR_CHOICES, blank=True)

    @property
    def is_super_admin(self):
        return self.is_superuser

    def clean(self):
        super().clean()
        if self.is_superuser:
            other_super_admins = CustomUser.objects.filter(is_superuser=True)
            if self.pk:
                other_super_admins = other_super_admins.exclude(pk=self.pk)
            if other_super_admins.exists():
                raise ValidationError('Only one super-admin account is allowed.')

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        # Human-readable representation: "Juan Dela Cruz (2024-001)" or "admin_user (admin)"
        return f"{self.get_full_name()} ({self.id_number or self.username})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['is_superuser'],
                condition=Q(is_superuser=True),
                name='only_one_super_admin',
            ),
        ]


class AdminRegistrationRequest(models.Model):
    """
    Tracks pending requests from users who want to become admins.
    An admin must approve or reject each request from the dashboard.
    """

    # Allowed values for the status field
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # One-to-one link to the user who submitted the request; CASCADE deletes the request if the user is deleted
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='admin_registration_request'  # Allows user.admin_registration_request to access the request
    )

    # Current state of the request: pending (awaiting review), approved, or rejected
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Timestamp automatically set when the request is first created
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Human-readable representation for the Django admin and shell
        return f"AdminRequest({self.user.username}, {self.status})"

    class Meta:
        # Show the most recently submitted requests first in querysets
        ordering = ['-requested_at']
