import base64
from functools import lru_cache

from django.db import connection, models    # Base module for all Django model fields
from django.conf import settings  # Access AUTH_USER_MODEL without a hard import


@lru_cache(maxsize=1)
def receipt_database_image_fields_ready():
    """
    Return True when the production database has the columns needed for
    database-backed receipt images.
    """
    try:
        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor,
                    EnrollmentReceipt._meta.db_table,
                )
            }
    except Exception:
        return False

    return {'image_data', 'content_type', 'original_filename'}.issubset(columns)


class EnrollmentRequest(models.Model):
    """
    Represents a student's enrollment submission.
    Contains the chosen course, year level, selected subjects, and current status.
    An admin reviews each request and sets it to 'verified' or 'rejected'.
    """

    # Allowed status values for the enrollment request lifecycle
    STATUS_CHOICES = [
        ('pending', 'Pending'),    # Submitted but not yet reviewed by an admin
        ('verified', 'Verified'),  # Approved by an admin
        ('rejected', 'Rejected'),  # Denied by an admin
    ]

    # Allowed year level values
    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
    ]

    SEMESTER_CHOICES = [
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('Summer', 'Summer'),
    ]

    # The student who submitted this request; CASCADE deletes the request if the student is deleted
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # References CustomUser without a hard import
        on_delete=models.CASCADE,
        related_name='enrollment_requests'  # Allows user.enrollment_requests.all()
    )

    # The course the student is enrolling in; SET_NULL so deleting a course doesn't delete the request
    course = models.ForeignKey(
        'admindash.Course',
        on_delete=models.SET_NULL,  # If the course is deleted, set this field to NULL
        null=True,
        blank=True
    )

    # The year level the student is enrolling in
    year_level = models.CharField(max_length=15, choices=YEAR_CHOICES)

    # The semester the student is enrolling in
    semester = models.CharField(max_length=15, choices=SEMESTER_CHOICES, default='1st Semester')

    # The subjects the student selected; many-to-many because one request can include multiple subjects
    subjects = models.ManyToManyField('admindash.Subject', blank=True)

    # Current review status; defaults to 'pending' when first created
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Automatically set to the current date/time when the record is first created
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Human-readable representation for the Django admin and shell
        return f"EnrollmentRequest({self.student}, {self.status}, {self.submitted_at.date()})"

    @property
    def total_units(self):
        """Sum of units across all selected subjects for this enrollment request."""
        return sum(s.units for s in self.subjects.all())

    class Meta:
        # Return the most recently submitted requests first
        ordering = ['-submitted_at']


class EnrollmentReceipt(models.Model):
    """
    Stores a single proof-of-payment image uploaded with an EnrollmentRequest.
    One request can have 1–3 receipts.
    """

    # The enrollment request this receipt belongs to; CASCADE deletes receipts if the request is deleted
    enrollment_request = models.ForeignKey(
        EnrollmentRequest,
        on_delete=models.CASCADE,
        related_name='receipts'  # Allows enrollment_request.receipts.all()
    )

    # The uploaded image file; stored in MEDIA_ROOT/receipts/
    # Older receipts may still use MEDIA_ROOT/receipts/. New uploads are stored
    # in the database so they work on serverless hosts without persistent media.
    image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    image_data = models.BinaryField(null=True, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    # Validation: JPEG/PNG only, max 5 MB — enforced in the form clean() method

    @classmethod
    def create_from_upload(cls, enrollment_request, uploaded_file):
        if not receipt_database_image_fields_ready():
            return None

        return cls.objects.create(
            enrollment_request=enrollment_request,
            image_data=uploaded_file.read(),
            content_type=getattr(uploaded_file, 'content_type', '') or '',
            original_filename=getattr(uploaded_file, 'name', '')[:255],
        )

    @property
    def display_url(self):
        if self.image_data:
            encoded = base64.b64encode(bytes(self.image_data)).decode('ascii')
            content_type = self.content_type or 'image/jpeg'
            return f'data:{content_type};base64,{encoded}'

        if self.image:
            try:
                return self.image.url
            except Exception:
                return ''

        return ''

    def __str__(self):
        return f"Receipt for {self.enrollment_request}"
