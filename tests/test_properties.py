"""
Property-Based Tests for the University of Bohol Graduate School Portal.

Uses hypothesis + pytest-django to verify the 8 correctness properties
defined in the design document (Section 9).

**Validates: Requirements 2, 4, 5, 7, 8, 9**

NOTE: Each test uses @pytest.mark.django_db with transaction=True so that
hypothesis can run multiple examples within a single test function without
DB state leaking between examples. We use a module-level counter to generate
unique usernames/IDs across all examples within a test run.
"""

import io
import uuid
import pytest
from django.test import Client
from django.db import IntegrityError, transaction
from django.urls import reverse

from hypothesis import given, assume, settings as hyp_settings
from hypothesis import strategies as st

from landingpage.models import CustomUser, AdminRegistrationRequest
from admindash.models import Course, Subject
from studentenrollment.models import EnrollmentRequest, EnrollmentReceipt
from bookmanagement.forms import BookClaimForm


# ---------------------------------------------------------------------------
# Helpers — use uuid4 short tokens to guarantee uniqueness across examples
# ---------------------------------------------------------------------------

def uid():
    """Return a short unique string safe for use in usernames/IDs."""
    return uuid.uuid4().hex[:12]


def make_student(prefix="stu", id_number=None, password="testpass123"):
    """Create a student CustomUser with a guaranteed-unique username."""
    token = uid()
    uname = f"{prefix}_{token}"
    id_num = id_number if id_number is not None else token
    return CustomUser.objects.create_user(
        username=uname,
        password=password,
        role="student",
        id_number=id_num,
        first_name="Test",
        last_name="Student",
    )


def make_admin(prefix="adm", password="adminpass123"):
    """Create an admin CustomUser with a guaranteed-unique username."""
    token = uid()
    uname = f"{prefix}_{token}"
    return CustomUser.objects.create_user(
        username=uname,
        password=password,
        role="admin",
        first_name="Test",
        last_name="Admin",
    )


def make_super_admin(prefix="super", password="superpass123"):
    """Create the single super-admin account."""
    token = uid()
    uname = f"{prefix}_{token}"
    return CustomUser.objects.create_superuser(
        username=uname,
        password=password,
        first_name="Test",
        last_name="SuperAdmin",
    )


def make_course(name=None):
    """Create (or get) a Course."""
    name = name or f"Course_{uid()}"
    return Course.objects.create(name=name)


def make_subject(course, units=3, year_level="1st Year"):
    """Create a Subject with a guaranteed-unique code."""
    code = f"S{uid()}"
    return Subject.objects.create(
        course=course,
        code=code,
        description=f"Subject {code}",
        units=units,
        year_level=year_level,
    )


# ---------------------------------------------------------------------------
# P1 — Enrollment Unit Cap
# **Validates: Requirements 4.7, 5.6, 9.3**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.lists(st.integers(min_value=1, max_value=9), min_size=1, max_size=9))
def test_p1_enrollment_unit_cap(unit_list):
    """
    Property: For any EnrollmentRequest persisted in the database, the sum of
    units across all associated Subject records is always ≤ 9.

    **Validates: Requirements 4.7, 5.6**
    """
    total = sum(unit_list)

    course = make_course()
    student = make_student()

    # Create subjects with the given unit values
    subjects = [make_subject(course, units=u) for u in unit_list]

    if total <= 9:
        # Valid: EnrollmentRequest should be created successfully
        enrollment = EnrollmentRequest.objects.create(
            student=student,
            course=course,
            year_level="1st Year",
            status="pending",
        )
        enrollment.subjects.set(subjects)

        # Verify the invariant: persisted total units ≤ 9
        persisted_total = sum(s.units for s in enrollment.subjects.all())
        assert persisted_total <= 9, (
            f"Persisted enrollment has {persisted_total} units, expected ≤ 9"
        )
    else:
        # Invalid: form validation should reject it
        from studentenrollment.forms import EnrollmentForm

        post_data = {
            "course": course.pk,
            "year_level": "1st Year",
            "subjects": [s.pk for s in subjects],
        }
        form = EnrollmentForm(post_data, course_id=course.pk)
        # Override the subjects queryset to include our subjects
        form.fields["subjects"].queryset = Subject.objects.filter(
            pk__in=[s.pk for s in subjects]
        )
        assert not form.is_valid(), (
            f"Form should be invalid for total units={total} > 9"
        )
        assert "subjects" in form.errors, (
            f"Form should have a 'subjects' error for total units={total}"
        )


# ---------------------------------------------------------------------------
# P2 — Duplicate ID Number Rejection
# **Validates: Requirements 3.4, 9.1**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    )
)
def test_p2_duplicate_id_rejection(id_number):
    """
    Property: For any two CustomUser records with role='student', their
    id_number values are always distinct (no two students share an ID number).

    **Validates: Requirements 3.4, 9.1**
    """
    from landingpage.forms import StudentRegistrationForm

    # Create the first student with this id_number (use unique username)
    token = uid()
    CustomUser.objects.create_user(
        username=f"p2_first_{token}",
        password="testpass123",
        role="student",
        id_number=id_number,
        first_name="First",
        last_name="Student",
    )

    # Attempt to register a second student with the same id_number via the form
    form_data = {
        "last_name": "Second",
        "first_name": "Student",
        "middle_name": "",
        "id_number": id_number,
        "email": f"second_{token}@test.com",
        "password": "testpass123",
        "confirm_password": "testpass123",
    }
    form = StudentRegistrationForm(form_data)

    # The form should be invalid due to duplicate id_number
    assert not form.is_valid(), (
        f"Form should reject duplicate id_number='{id_number}'"
    )
    assert "id_number" in form.errors, (
        f"Form should have an 'id_number' error for duplicate id_number='{id_number}'"
    )

    # Only one CustomUser should exist with this id_number
    count = CustomUser.objects.filter(id_number=id_number).count()
    assert count == 1, (
        f"Expected exactly 1 user with id_number='{id_number}', found {count}"
    )


# ---------------------------------------------------------------------------
# P3 — Role-Based Access Invariant
# **Validates: Requirements 2.6, 2.7**
# ---------------------------------------------------------------------------

STUDENT_ONLY_URLS = [
    "/home/",
    "/enrollment/",
    "/profile/",
    "/books/claim/",
    "/books/claimed/",
    "/books/enrollment/",
]

ADMIN_ONLY_URLS = [
    "/admin-dashboard/",
]


@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.sampled_from(STUDENT_ONLY_URLS))
def test_p3_role_based_access_admin_blocked_from_student_urls(url):
    """
    Property: For any HTTP request to a student-only URL made by a user with
    role='admin', the response status code is always 403.

    **Validates: Requirements 2.7**
    """
    admin_user = make_admin()
    client = Client()
    client.force_login(admin_user)

    response = client.get(url)
    assert response.status_code == 403, (
        f"Admin user should get 403 on student-only URL '{url}', "
        f"got {response.status_code}"
    )


@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.sampled_from(ADMIN_ONLY_URLS))
def test_p3_role_based_access_student_blocked_from_admin_urls(url):
    """
    Property: For any HTTP request to an admin-only URL made by a user with
    role='student', the response status code is always 403.

    **Validates: Requirements 2.6**
    """
    student_user = make_student()
    client = Client()
    client.force_login(student_user)

    response = client.get(url)
    assert response.status_code == 403, (
        f"Student user should get 403 on admin-only URL '{url}', "
        f"got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# P4 — Enrollment Status Transition Validity
# **Validates: Requirements 8.8, 8.9**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(
    st.sampled_from([
        # (initial_status, action, expected_success)
        ("pending", "verify", True),
        ("pending", "reject", True),
        ("verified", "reject", True),
        ("rejected", "reject", False),   # already rejected — no change
        ("verified", "verify", False),   # already verified — no change
        ("rejected", "verify", False),   # rejected cannot be verified
    ])
)
def test_p4_enrollment_status_transitions(transition):
    """
    Property: An EnrollmentRequest status can only transition as follows:
    pending→verified, pending→rejected, verified→rejected.
    Invalid transitions return errors and leave status unchanged.

    **Validates: Requirements 8.8, 8.9**
    """
    initial_status, action, expected_success = transition

    course = make_course()
    student = make_student()
    admin_user = make_admin()

    enrollment = EnrollmentRequest.objects.create(
        student=student,
        course=course,
        year_level="1st Year",
        status=initial_status,
    )

    client = Client()
    client.force_login(admin_user)

    if action == "verify":
        url = reverse("admindash:verify_enrollment", kwargs={"pk": enrollment.pk})
    else:
        url = reverse("admindash:reject_enrollment", kwargs={"pk": enrollment.pk})

    response = client.post(url)

    # Both success and error cases redirect back to the dashboard
    assert response.status_code == 302, (
        f"Expected redirect (302), got {response.status_code}"
    )

    enrollment.refresh_from_db()

    if expected_success:
        if action == "verify":
            assert enrollment.status == "verified", (
                f"Expected status 'verified' after verify from '{initial_status}', "
                f"got '{enrollment.status}'"
            )
        else:
            assert enrollment.status == "rejected", (
                f"Expected status 'rejected' after reject from '{initial_status}', "
                f"got '{enrollment.status}'"
            )
    else:
        # Status should remain unchanged on invalid transition
        assert enrollment.status == initial_status, (
            f"Status should remain '{initial_status}' after invalid {action} action, "
            f"got '{enrollment.status}'"
        )


# ---------------------------------------------------------------------------
# P5 — Receipt Count Invariant
# **Validates: Requirements 5.6, 5.7**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.integers(min_value=0, max_value=6))
def test_p5_receipt_count_invariant(receipt_count):
    """
    Property: For any EnrollmentRequest created through the enrollment form,
    the number of associated EnrollmentReceipt records is always between 1 and 3.
    Submissions with 0 receipts are rejected; >3 receipts are rejected.

    **Validates: Requirements 5.6, 5.7**
    """
    from studentenrollment.forms import validate_receipt_files

    # Build mock in-memory file objects
    mock_files = []
    for i in range(receipt_count):
        content = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG header bytes
        mock_file = io.BytesIO(content)
        mock_file.name = f"receipt_{i}.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = len(content)
        mock_files.append(mock_file)

    valid_files, errors = validate_receipt_files(mock_files)

    if receipt_count == 0:
        # Must be rejected: no receipts
        assert len(errors) > 0, "0 receipts should produce validation errors"
        assert len(valid_files) == 0, "0 receipts should yield no valid files"
    elif 1 <= receipt_count <= 3:
        # Must be accepted
        assert len(errors) == 0, (
            f"{receipt_count} receipts should be valid, got errors: {errors}"
        )
        assert len(valid_files) == receipt_count, (
            f"Expected {receipt_count} valid files, got {len(valid_files)}"
        )
    else:
        # receipt_count > 3: must be rejected
        assert len(errors) > 0, (
            f"{receipt_count} receipts (>3) should produce validation errors"
        )
        assert len(valid_files) == 0, (
            f"{receipt_count} receipts (>3) should yield no valid files"
        )


# ---------------------------------------------------------------------------
# P6 — Book Claim Quantity Positivity
# **Validates: Requirements 7.2, 7.3, 9.6**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.integers(max_value=0))
def test_p6_book_claim_quantity_invalid(quantity):
    """
    Property: BookClaimForm rejects quantity ≤ 0.

    **Validates: Requirements 7.2, 7.3, 9.6**
    """
    form_data = {
        "course_name": "Master of Arts",
        "book_title": "Test Book",
        "quantity": quantity,
        "phone": "",
    }
    form = BookClaimForm(form_data)
    assert not form.is_valid(), (
        f"BookClaimForm should reject quantity={quantity} (≤ 0)"
    )
    assert "quantity" in form.errors, (
        f"BookClaimForm should have a 'quantity' error for quantity={quantity}"
    )


@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.integers(min_value=1))
def test_p6_book_claim_quantity_valid(quantity):
    """
    Property: BookClaimForm accepts any quantity ≥ 1.

    **Validates: Requirements 7.2, 9.6**
    """
    form_data = {
        "course_name": "Master of Arts",
        "book_title": "Test Book",
        "quantity": quantity,
        "phone": "",
    }
    form = BookClaimForm(form_data)
    assert form.is_valid(), (
        f"BookClaimForm should accept quantity={quantity} (≥ 1), "
        f"errors: {form.errors}"
    )


# ---------------------------------------------------------------------------
# P7 — Admin Registration Request Uniqueness
# **Validates: Requirements 9.7**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.integers(min_value=1, max_value=100))
def test_p7_admin_request_uniqueness(seed):
    """
    Property: For any CustomUser, there exists at most one AdminRegistrationRequest
    record (enforced by the OneToOneField).

    **Validates: Requirements 9.7**
    """
    from django.db import transaction

    # Each example gets a unique user via uid()
    user = CustomUser.objects.create_user(
        username=f"p7_{uid()}",
        password="testpass123",
        role="student",
    )

    # First request should succeed
    AdminRegistrationRequest.objects.create(user=user, status="pending")

    # Second request for the same user must raise IntegrityError.
    # Use a savepoint so the outer transaction is not aborted.
    integrity_error_raised = False
    try:
        with transaction.atomic():
            AdminRegistrationRequest.objects.create(user=user, status="pending")
    except IntegrityError:
        integrity_error_raised = True

    assert integrity_error_raised, (
        "Creating a second AdminRegistrationRequest for the same user "
        "should raise IntegrityError (OneToOne constraint)"
    )

    # Confirm only one record exists
    count = AdminRegistrationRequest.objects.filter(user=user).count()
    assert count == 1, (
        f"Expected exactly 1 AdminRegistrationRequest for user, found {count}"
    )


# ---------------------------------------------------------------------------
# P8 — Course Deletion Guard
# **Validates: Requirements 8.5**
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@hyp_settings(max_examples=100, deadline=None)
@given(st.integers(min_value=1, max_value=5))
def test_p8_course_deletion_guard(num_enrollments):
    """
    Property: A Course that has at least one associated EnrollmentRequest
    (via EnrollmentRequest.course) is never deleted from the database.

    **Validates: Requirements 8.5**
    """
    course = make_course()
    admin_user = make_admin()

    # Create the specified number of enrollment requests for this course
    for _ in range(num_enrollments):
        student = make_student()
        EnrollmentRequest.objects.create(
            student=student,
            course=course,
            year_level="1st Year",
            status="pending",
        )

    client = Client()
    client.force_login(admin_user)

    url = reverse("admindash:remove_course", kwargs={"pk": course.pk})
    response = client.post(url)

    # Should redirect (with an error stored in session), not delete
    assert response.status_code == 302, (
        f"Expected redirect (302), got {response.status_code}"
    )

    # The course must still exist in the database
    assert Course.objects.filter(pk=course.pk).exists(), (
        f"Course with {num_enrollments} enrollment request(s) should NOT be deleted"
    )


# ---------------------------------------------------------------------------
# Super-admin access control
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_super_admin_is_the_only_user_who_sees_manage_admin_panel():
    normal_admin = make_admin()
    client = Client()
    client.force_login(normal_admin)

    response = client.get(reverse("admindash:index"))

    assert response.status_code == 200
    assert b'data-target="admin-account-panel"' not in response.content
    assert b'id="admin-account-panel"' not in response.content


@pytest.mark.django_db
def test_normal_admin_cannot_approve_admin_request():
    normal_admin = make_admin()
    requested_user = make_student(prefix="pending_admin")
    admin_request = AdminRegistrationRequest.objects.create(
        user=requested_user,
        status="pending",
    )

    client = Client()
    client.force_login(normal_admin)
    response = client.post(
        reverse("admindash:approve_admin", kwargs={"pk": admin_request.pk})
    )

    assert response.status_code == 403
    admin_request.refresh_from_db()
    requested_user.refresh_from_db()
    assert admin_request.status == "pending"
    assert requested_user.role == "student"


@pytest.mark.django_db
def test_super_admin_can_approve_and_revoke_admin_access():
    super_admin = make_super_admin()
    requested_user = make_student(prefix="pending_admin")
    admin_request = AdminRegistrationRequest.objects.create(
        user=requested_user,
        status="pending",
    )

    client = Client()
    client.force_login(super_admin)
    approve_response = client.post(
        reverse("admindash:approve_admin", kwargs={"pk": admin_request.pk})
    )

    assert approve_response.status_code == 302
    admin_request.refresh_from_db()
    requested_user.refresh_from_db()
    assert admin_request.status == "approved"
    assert requested_user.role == "admin"
    assert requested_user.is_staff is True

    revoke_response = client.post(
        reverse("admindash:revoke_admin", kwargs={"pk": requested_user.pk})
    )

    assert revoke_response.status_code == 302
    requested_user.refresh_from_db()
    assert requested_user.role == "student"
    assert requested_user.is_staff is False


@pytest.mark.django_db
def test_only_one_super_admin_can_exist():
    make_super_admin()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_super_admin(prefix="second_super")


@pytest.mark.django_db
def test_normal_admin_cannot_transfer_super_admin_role():
    normal_admin = make_admin(prefix="normal")
    target_admin = make_admin(prefix="target")

    client = Client()
    client.force_login(normal_admin)
    response = client.post(
        reverse("admindash:transfer_super_admin", kwargs={"pk": target_admin.pk})
    )

    assert response.status_code == 403
    normal_admin.refresh_from_db()
    target_admin.refresh_from_db()
    assert normal_admin.is_superuser is False
    assert target_admin.is_superuser is False


@pytest.mark.django_db
def test_super_admin_can_transfer_role_to_another_admin():
    super_admin = make_super_admin()
    target_admin = make_admin(prefix="target")

    client = Client()
    client.force_login(super_admin)
    response = client.post(
        reverse("admindash:transfer_super_admin", kwargs={"pk": target_admin.pk})
    )

    assert response.status_code == 302
    super_admin.refresh_from_db()
    target_admin.refresh_from_db()
    assert super_admin.role == "admin"
    assert super_admin.is_staff is True
    assert super_admin.is_superuser is False
    assert target_admin.role == "admin"
    assert target_admin.is_staff is True
    assert target_admin.is_superuser is True
    assert CustomUser.objects.filter(is_superuser=True).count() == 1
