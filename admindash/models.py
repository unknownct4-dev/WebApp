from django.db import models                                          # Base module for all Django model fields
from django.core.validators import MinValueValidator, MaxValueValidator  # Validators that enforce numeric range constraints


class Course(models.Model):
    """
    Represents an academic program (e.g. Master of Arts in Educational Management).
    Managed by admins from the dashboard.
    """

    # The full name of the course; must be unique across all courses
    name = models.CharField(max_length=200, unique=True)

    # Automatically set to the current date/time when the record is first created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Used in the Django admin, shell, and dropdowns
        return self.name

    class Meta:
        # Return courses in alphabetical order by default
        ordering = ['name']


class Subject(models.Model):
    """
    Represents an individual academic unit belonging to a Course.
    Has both a year level (1st Year / 2nd Year) and a semester (1st Semester / 2nd Semester / Summer).
    Students see only subjects matching their selected year and semester when enrolling.
    """

    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
    ]

    SEMESTER_CHOICES = [
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('Summer', 'Summer'),
    ]

    # The course this subject belongs to; CASCADE means deleting a course also deletes its subjects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')

    # Short unique identifier for the subject (e.g. "MAEM101")
    code = models.CharField(max_length=20, unique=True)

    # Full name or description of the subject
    description = models.CharField(max_length=200)

    # Number of academic units; must be between 1 and 9 inclusive
    units = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(9)])

    # The year level this subject belongs to (1st Year or 2nd Year)
    year_level = models.CharField(max_length=15, choices=YEAR_CHOICES, default='1st Year')

    # The semester this subject is offered in
    semester = models.CharField(max_length=15, choices=SEMESTER_CHOICES, default='1st Semester')

    def __str__(self):
        return f"{self.code} - {self.description}"

    class Meta:
        ordering = ['code']
