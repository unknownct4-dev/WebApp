from django.db import models    # Base module for all Django model fields
from django.conf import settings  # Access AUTH_USER_MODEL without a hard import


class BookClaim(models.Model):
    """
    Records a student's request to claim a textbook.
    Submitted via the book claim form at /books/claim/.
    """

    # The student who submitted the claim; CASCADE deletes the claim if the student is deleted
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='book_claims'
    )

    course_name = models.CharField(max_length=200)
    book_title = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    phone = models.CharField(max_length=20, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BookClaim({self.student}, {self.book_title}, qty={self.quantity})"

    class Meta:
        ordering = ['-submitted_at']


class BookSubmission(models.Model):
    """
    A student submits exactly 6 book titles for processing by the admin.
    The admin moves the submission through a lifecycle:
      pending → received → processing → claimable → claimed
    """

    STATUS_CHOICES = [
        ('pending',    'Pending'),           # Student submitted, awaiting admin acknowledgement
        ('received',   'Received'),          # Admin confirmed receipt of the physical books
        ('processing', 'Processing Books'),  # Admin is working on the books
        ('claimable',  'Ready to Claim'),    # Admin notified student that books are ready
        ('claimed',    'Claimed'),           # Admin confirmed student collected the books
    ]

    # The student who submitted the books
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='book_submissions'
    )

    # Current lifecycle status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"BookSubmission({self.student}, {self.status}, {self.submitted_at.date()})"

    class Meta:
        ordering = ['-submitted_at']


class SubmittedBook(models.Model):
    """
    One of the 6 book titles in a BookSubmission.
    """

    # The submission this book belongs to
    submission = models.ForeignKey(
        BookSubmission,
        on_delete=models.CASCADE,
        related_name='books'
    )

    # The title of the book as entered by the student
    title = models.CharField(max_length=300)

    def __str__(self):
        return f"Book: {self.title} (submission #{self.submission_id})"
