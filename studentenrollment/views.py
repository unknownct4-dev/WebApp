import logging

from django.shortcuts import render, redirect  # render() builds an HTML response; redirect() sends the browser to a new URL
from django.views import View                  # Base class for class-based views
from django.views.generic import TemplateView  # Convenience view that just renders a template
from django.http import JsonResponse           # Returns a JSON-encoded HTTP response
from django.db import transaction

from landingpage.mixins import StudentRequiredMixin  # Restricts access to authenticated students only
from admindash.models import Course, Subject          # Course and Subject models from the admin app
from .models import EnrollmentRequest, EnrollmentReceipt  # Enrollment models defined in this app
from .forms import EnrollmentForm, validate_receipt_files  # Form and receipt validation utility

logger = logging.getLogger(__name__)


class EnrollmentView(StudentRequiredMixin, View):
    """
    GET  /enrollment/ — Renders the enrollment form with all available courses.
    POST /enrollment/ — Validates the form, saves receipt files, creates the
                        EnrollmentRequest record, and redirects to the confirmation page.
    """
    template_name = 'studentenrollment/enrollment.html'

    def get(self, request):
        """Render the empty enrollment form with all courses for the dropdown."""
        form = EnrollmentForm()
        courses = Course.objects.all()  # Fetch all courses to populate the course dropdown
        return render(request, self.template_name, {
            'form': form,
            'courses': courses,
        })

    def post(self, request):
        course_id = request.POST.get('course')
        year_level = request.POST.get('year_level', '').strip()
        semester = request.POST.get('semester', '').strip()
        form = EnrollmentForm(request.POST, course_id=course_id, year_level=year_level, semester=semester)
        courses = Course.objects.all()

        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'courses': courses})

        receipt_files = request.FILES.getlist('receipts')
        valid_files, errors = validate_receipt_files(receipt_files)

        if errors:
            return render(request, self.template_name, {'form': form, 'courses': courses, 'receipt_errors': errors})

        if not valid_files:
            return render(request, self.template_name, {
                'form': form, 'courses': courses,
                'receipt_errors': ['No valid files were uploaded. Please try again.'],
            })

        with transaction.atomic():
            enrollment_request = EnrollmentRequest.objects.create(
                student=request.user,
                course=form.cleaned_data['course'],
                year_level=form.cleaned_data['year_level'],
                semester=form.cleaned_data['semester'],
                status='pending',
            )
            enrollment_request.subjects.set(form.cleaned_data['subjects'])

        for receipt_file in valid_files:
            try:
                EnrollmentReceipt.create_from_upload(enrollment_request, receipt_file)
            except Exception:
                logger.exception(
                    'Failed to save receipt for enrollment request %s.',
                    enrollment_request.pk,
                )

        if not enrollment_request.receipts.exists():
            logger.warning(
                'Enrollment request %s was saved without receipt records.',
                enrollment_request.pk,
            )

        request.session['enrollment_request_id'] = enrollment_request.pk
        return redirect('studentenrollment:confirmation')


class SubjectsJsonView(StudentRequiredMixin, View):
    """
    GET /enrollment/subjects/<course_code>/
    Returns a JSON list of subjects for the given course.
    Called by the enrollment form's JavaScript when the student selects a course.
    """

    def get(self, request, course_code):
        # course_code can be either a numeric database ID or a course name string
        try:
            course_id = int(course_code)
            subjects = Subject.objects.filter(course_id=course_id)
        except ValueError:
            subjects = Subject.objects.filter(course__name__icontains=course_code)

        # Filter by year_level and semester if provided as query params
        year_level = request.GET.get('year_level', '').strip()
        semester = request.GET.get('semester', '').strip()
        if year_level:
            subjects = subjects.filter(year_level=year_level)
        if semester:
            subjects = subjects.filter(semester=semester)

        data = {
            'subjects': [
                {
                    'id': s.pk,
                    'code': s.code,
                    'description': s.description,
                    'units': s.units,
                    'year_level': s.year_level,
                    'semester': s.semester,
                }
                for s in subjects
            ]
        }
        return JsonResponse(data)


class ConfirmationView(StudentRequiredMixin, TemplateView):
    """
    GET /enrollment/confirmation/
    Reads the enrollment_request_id stored in the session by EnrollmentView,
    fetches the EnrollmentRequest, and renders the confirmation page.
    """
    template_name = 'studentenrollment/confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the enrollment request ID saved in the session after a successful submission
        enrollment_request_id = self.request.session.get('enrollment_request_id')
        enrollment_request = None

        if enrollment_request_id:
            try:
                # Fetch the enrollment request, pre-loading subjects and course to avoid extra queries
                enrollment_request = EnrollmentRequest.objects.prefetch_related(
                    'subjects', 'course'
                ).get(pk=enrollment_request_id, student=self.request.user)
            except EnrollmentRequest.DoesNotExist:
                pass  # Session ID is stale or belongs to a different user — show empty confirmation

        context['enrollment_request'] = enrollment_request

        # Calculate total units for display on the confirmation page
        if enrollment_request:
            context['total_units'] = sum(
                s.units for s in enrollment_request.subjects.all()
            )
        return context
