import mimetypes

from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.http import Http404, HttpResponse

from landingpage.mixins import AdminRequiredMixin, SuperAdminRequiredMixin
from landingpage.models import CustomUser, AdminRegistrationRequest
from studentenrollment.models import (
    EnrollmentRequest,
    EnrollmentReceipt,
    receipt_database_image_fields_ready,
)
from bookmanagement.models import BookSubmission

from .models import Course, Subject
from .forms import CourseForm, SubjectForm


def format_form_errors(form):
    """Return form validation errors without Django's raw bullet formatting."""
    return ' '.join(
        str(error)
        for errors in form.errors.values()
        for error in errors
    )


class DashboardView(AdminRequiredMixin, TemplateView):
    """
    GET /admin-dashboard/
    Main admin dashboard. Renders all panels:
      - Courses with their subjects
      - Enrollment requests (filterable by name, ID, or status via GET params)
      - Pending admin registration requests
      - Active admin accounts
      - Empty add-course and add-subject forms
      - Error messages passed back from POST views via the session
    """
    template_name = 'admindash/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch all courses and their subjects in a single query (avoids N+1 queries)
        context['courses'] = Course.objects.prefetch_related('subjects').all()

        can_show_receipts = receipt_database_image_fields_ready()

        # Start with all enrollment requests, joining student, course, and subjects data
        qs = EnrollmentRequest.objects.select_related('student', 'course').prefetch_related('subjects').all()
        if can_show_receipts:
            qs = qs.prefetch_related('receipts')

        # Read optional filter parameters from the query string (e.g. ?name=Juan&status=pending)
        search_name = self.request.GET.get('name', '').strip()
        search_id = self.request.GET.get('id', '').strip()
        search_status = self.request.GET.get('status', '').strip()

        # Apply name filter: match against first name OR last name (case-insensitive)
        if search_name:
            qs = qs.filter(
                Q(student__first_name__icontains=search_name) |
                Q(student__last_name__icontains=search_name)
            )
        # Apply ID number filter (case-insensitive partial match)
        if search_id:
            qs = qs.filter(student__id_number__icontains=search_id)
        # Apply status filter (exact match: 'pending', 'verified', or 'rejected')
        if search_status:
            qs = qs.filter(status=search_status)

        context['enrollment_requests'] = qs
        context['can_show_receipts'] = can_show_receipts

        # Count only pending enrollment requests for the notification badge
        context['pending_enrollment_count'] = qs.filter(status='pending').count()

        # Fetch pending admin registration requests with their associated user data
        context['pending_admin_requests'] = AdminRegistrationRequest.objects.filter(
            status='pending'
        ).select_related('user')

        # Fetch all users with the admin role for the "Active Admins" list
        context['admin_accounts'] = CustomUser.objects.filter(role='admin').order_by(
            '-is_superuser', 'last_name', 'first_name', 'username'
        )
        context['can_manage_admins'] = self.request.user.is_super_admin

        # Empty forms for the "Add Course" and "Add Subject" panels
        context['course_form'] = CourseForm()
        context['subject_form'] = SubjectForm()

        # Fetch all book submissions with student and book data pre-loaded
        book_qs = (
            BookSubmission.objects
            .select_related('student')
            .prefetch_related('books')
            .all()
        )
        context['book_submissions'] = book_qs
        # Count only pending book submissions for the notification badge
        context['pending_books_count'] = book_qs.filter(status='pending').count()
        # Count claimable submissions (notified but student hasn't collected yet)
        context['claimable_books_count'] = book_qs.filter(status='claimable').count()

        # Pop error messages stored in the session by the POST views (consumed once, then cleared)
        context['course_error'] = self.request.session.pop('course_error', None)
        context['subject_error'] = self.request.session.pop('subject_error', None)
        context['active_panel'] = self.request.session.pop('active_admin_panel', 'courses-panel')

        return context


class EnrolledRecordsPrintView(AdminRequiredMixin, TemplateView):
    """
    GET /admin-dashboard/students/enrolled-records/print/
    Print-friendly report of verified enrollment records grouped by course and year.
    """
    template_name = 'admindash/enrolled_records_print.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment_records'] = (
            EnrollmentRequest.objects
            .filter(status='verified')
            .select_related('student', 'course')
            .prefetch_related('subjects')
            .order_by(
                'course__name',
                'year_level',
                'student__last_name',
                'student__first_name',
                'student__username',
            )
        )
        context['generated_at'] = timezone.localtime()
        return context


class ReceiptImageView(AdminRequiredMixin, View):
    """
    GET /admin-dashboard/receipts/<pk>/image/
    Streams a proof-of-payment receipt to admins without embedding image bytes in
    the dashboard HTML.
    """

    def get(self, request, pk, *args, **kwargs):
        if not receipt_database_image_fields_ready():
            raise Http404('Receipt image storage is not ready.')

        receipt = get_object_or_404(EnrollmentReceipt, pk=pk)

        if receipt.image_data:
            content_type = receipt.content_type or 'image/jpeg'
            return HttpResponse(bytes(receipt.image_data), content_type=content_type)

        if receipt.image:
            try:
                receipt.image.open('rb')
                content = receipt.image.read()
            except Exception as exc:
                raise Http404('Receipt image is unavailable.') from exc
            finally:
                try:
                    receipt.image.close()
                except Exception:
                    pass

            content_type = (
                receipt.content_type
                or mimetypes.guess_type(receipt.image.name)[0]
                or 'application/octet-stream'
            )
            return HttpResponse(content, content_type=content_type)

        raise Http404('Receipt image is unavailable.')


class AddCourseView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/courses/add/
    Validates the CourseForm and creates a new Course record.
    On failure, stores the error in the session and redirects back to the dashboard.
    """

    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST)  # Bind submitted data to the form
        if form.is_valid():
            form.save()  # Save the new Course to the database
            messages.success(request, 'Course added successfully.')
        else:
            # Store clean form errors for display on the next dashboard load
            # The dashboard view will read and display this error on the next GET
            errors = format_form_errors(form)
            request.session['course_error'] = errors
        return redirect('admindash:index')  # Always redirect back to the dashboard


class RemoveCourseView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/courses/<pk>/remove/
    Deletes the Course (and its Subjects via CASCADE) only if no EnrollmentRequests
    reference it. If enrollment requests exist, stores an error in the session instead.
    """

    def post(self, request, pk, *args, **kwargs):
        # Fetch the course or return 404 if it doesn't exist
        course = get_object_or_404(Course, pk=pk)

        # Guard: refuse deletion if any enrollment request references this course
        if EnrollmentRequest.objects.filter(course=course).exists():
            request.session['course_error'] = (
                f'Cannot remove "{course.name}": it has associated enrollment requests.'
            )
        else:
            course.delete()  # Deleting the course also deletes its subjects (CASCADE)
            messages.success(request, f'Course "{course.name}" removed.')
        return redirect('admindash:index')


class AddSubjectView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/subjects/add/
    Validates the SubjectForm and creates a new Subject record.
    On failure, stores the error in the session.
    """

    def post(self, request, *args, **kwargs):
        form = SubjectForm(request.POST)  # Bind submitted data to the form
        if form.is_valid():
            form.save()  # Save the new Subject to the database
            messages.success(request, 'Subject added successfully.')
        else:
            # Store form errors in the session for display on the next GET
            errors = format_form_errors(form)
            request.session['subject_error'] = errors
        return redirect('admindash:index')


class RemoveSubjectView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/subjects/<pk>/remove/
    Deletes the Subject identified by pk.
    """

    def post(self, request, pk, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=pk)  # Fetch or 404
        subject.delete()  # Remove the subject from the database
        messages.success(request, f'Subject "{subject.code}" removed.')
        return redirect('admindash:index')


class VerifyEnrollmentView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/enrollment/<pk>/verify/
    Sets the EnrollmentRequest status to 'verified', but only if it is currently 'pending'.
    Prevents verifying an already-verified or rejected request.
    """

    def post(self, request, pk, *args, **kwargs):
        request.session['active_admin_panel'] = 'students-panel'
        enrollment = get_object_or_404(EnrollmentRequest, pk=pk)  # Fetch or 404

        if enrollment.status == 'pending':
            enrollment.status = 'verified'
            # Only update the status column in the enrollment record
            enrollment.save(update_fields=['status'])

            # Copy course and year_level from the enrollment onto the student's profile
            # so the profile page shows the correct values after verification
            student = enrollment.student
            student.course = enrollment.course
            student.year_level = enrollment.year_level
            student.save(update_fields=['course', 'year_level'])

            messages.success(request, 'Enrollment request verified.')
        elif enrollment.status == 'verified':
            messages.success(request, 'Enrollment request is already verified.')
        else:
            messages.info(request, 'Enrollment request was already rejected.')
        return redirect('admindash:index')


class RejectEnrollmentView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/enrollment/<pk>/reject/
    Sets the EnrollmentRequest status to 'rejected', unless it is already 'rejected'.
    """

    def post(self, request, pk, *args, **kwargs):
        request.session['active_admin_panel'] = 'students-panel'
        enrollment = get_object_or_404(EnrollmentRequest, pk=pk)  # Fetch or 404

        if enrollment.status != 'rejected':
            enrollment.status = 'rejected'
            enrollment.save(update_fields=['status'])  # Only update the status column
            messages.success(request, 'Enrollment request rejected.')
        else:
            messages.success(request, 'Enrollment request is already rejected.')
        return redirect('admindash:index')


class ApproveAdminView(SuperAdminRequiredMixin, View):
    """
    POST /admin-dashboard/admin-requests/<pk>/approve/
    Approves a pending admin registration request:
      1. Sets AdminRegistrationRequest.status to 'approved'.
      2. Sets the requesting user's role to 'admin'.
    """

    def post(self, request, pk, *args, **kwargs):
        admin_request = get_object_or_404(AdminRegistrationRequest, pk=pk)
        if admin_request.status != 'pending':
            messages.info(
                request,
                f'Admin request for '
                f'"{admin_request.user.get_full_name() or admin_request.user.username}" '
                f'was already {admin_request.get_status_display().lower()}.'
            )
            return redirect('admindash:index')

        # Mark the registration request as approved
        admin_request.status = 'approved'
        admin_request.save(update_fields=['status'])

        # Promote the user's role from 'student' to 'admin'
        user = admin_request.user
        user.role = 'admin'
        user.is_staff = True
        user.save(update_fields=['role', 'is_staff'])

        messages.success(
            request,
            f'Admin request for "{user.get_full_name() or user.username}" approved.'
        )
        return redirect('admindash:index')


class RejectAdminView(SuperAdminRequiredMixin, View):
    """
    POST /admin-dashboard/admin-requests/<pk>/reject/
    Rejects a pending admin registration request.
    The requesting user's role remains 'student' — they do not gain admin access.
    """

    def post(self, request, pk, *args, **kwargs):
        admin_request = get_object_or_404(AdminRegistrationRequest, pk=pk)
        if admin_request.status != 'pending':
            messages.info(
                request,
                f'Admin request for '
                f'"{admin_request.user.get_full_name() or admin_request.user.username}" '
                f'was already {admin_request.get_status_display().lower()}.'
            )
            return redirect('admindash:index')

        # Mark the registration request as rejected; user role is unchanged
        admin_request.status = 'rejected'
        admin_request.save(update_fields=['status'])

        messages.success(
            request,
            f'Admin request for '
            f'"{admin_request.user.get_full_name() or admin_request.user.username}" rejected.'
        )
        return redirect('admindash:index')


class DeleteStudentView(AdminRequiredMixin, View):
    """
    POST /admin-dashboard/students/<pk>/delete/
    Permanently deletes a student account and all related records (CASCADE).
    Refuses to delete admin accounts.
    """

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(CustomUser, pk=pk, role='student')
        name = student.get_full_name() or student.username
        student.delete()  # CASCADE removes enrollment requests, book claims, etc.
        messages.success(request, f'Student account "{name}" has been deleted.')
        return redirect('admindash:index')


class RevokeAdminView(SuperAdminRequiredMixin, View):
    """
    POST /admin-dashboard/admins/<pk>/revoke/
    Removes admin access from an active admin account by setting their role back to 'student'.
    An admin cannot revoke their own access.
    """

    def post(self, request, pk, *args, **kwargs):
        # Fetch the target admin user or return 404
        target_user = get_object_or_404(CustomUser, pk=pk, role='admin')

        # Prevent an admin from revoking their own access
        if target_user == request.user:
            messages.error(request, 'You cannot remove your own admin access.')
            return redirect('admindash:index')

        if target_user.is_super_admin:
            messages.error(request, 'The super-admin account cannot be downgraded.')
            return redirect('admindash:index')

        # Downgrade the user's role from 'admin' to 'student'
        target_user.role = 'student'
        target_user.is_staff = False
        target_user.save(update_fields=['role', 'is_staff'])

        messages.success(
            request,
            f'Admin access removed for "{target_user.get_full_name() or target_user.username}".'
        )
        return redirect('admindash:index')


class TransferSuperAdminView(SuperAdminRequiredMixin, View):
    """
    POST /admin-dashboard/admins/<pk>/make-super-admin/
    Transfers the single super-admin role from the current user to another admin.
    """

    def post(self, request, pk, *args, **kwargs):
        target_user = get_object_or_404(CustomUser, pk=pk, role='admin')

        if target_user == request.user:
            messages.error(request, 'You are already the super-admin.')
            return redirect('admindash:index')

        with transaction.atomic():
            current_super_admin = CustomUser.objects.select_for_update().get(
                pk=request.user.pk
            )
            target_user = CustomUser.objects.select_for_update().get(
                pk=target_user.pk,
                role='admin',
            )

            current_super_admin.is_superuser = False
            current_super_admin.is_staff = True
            current_super_admin.role = 'admin'
            current_super_admin.save(update_fields=['is_superuser', 'is_staff', 'role'])

            target_user.is_superuser = True
            target_user.is_staff = True
            target_user.role = 'admin'
            target_user.save(update_fields=['is_superuser', 'is_staff', 'role'])

        messages.success(
            request,
            f'Super-admin role transferred to '
            f'"{target_user.get_full_name() or target_user.username}".'
        )
        return redirect('admindash:index')
