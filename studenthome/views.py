import json
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse

from landingpage.mixins import StudentRequiredMixin
from admindash.models import Course
from studentenrollment.models import EnrollmentRequest, EnrollmentReceipt
from bookmanagement.models import BookSubmission
from .forms import HomeEnrollmentForm


class HomeView(StudentRequiredMixin, TemplateView):
    """
    GET /home/
    Student home page with tabs: Overview, Programs, Updates, Enrollment, Books.
    """
    template_name = 'studenthome/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['courses'] = Course.objects.prefetch_related('subjects').all()

        context['enrollment_requests'] = EnrollmentRequest.objects.filter(
            student=self.request.user
        ).order_by('-submitted_at')

        # Fetch the student's book submissions for the Overview notifications panel
        context['book_submissions'] = BookSubmission.objects.filter(
            student=self.request.user
        ).prefetch_related('books').order_by('-submitted_at')

        context['enrollment_form'] = HomeEnrollmentForm()
        return context


class EnrollView(StudentRequiredMixin, View):
    """
    POST /home/enroll/
    Handles enrollment form submission from the student home page Enrollment tab.
    Returns a JSON response so the page can update without a full reload (AJAX).
    """

    def post(self, request):
        # Block re-enrollment if the student already has a verified enrollment
        if EnrollmentRequest.objects.filter(
            student=request.user, status='verified'
        ).exists():
            return JsonResponse({
                'status': 'error',
                'errors': ['You are already enrolled. You cannot submit a new enrollment request.']
            }, status=400)

        course_id = request.POST.get('course')
        year_level = request.POST.get('year_level', '').strip()
        semester = request.POST.get('semester', '').strip()
        form = HomeEnrollmentForm(request.POST, course_id=course_id, year_level=year_level, semester=semester)

        # If the form has validation errors, return them as JSON
        if not form.is_valid():
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)  # Flatten all field errors into a single list
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        # Validate that at least one receipt file was uploaded
        receipts = request.FILES.getlist('receipts')  # Get all files uploaded with the name 'receipts'
        if not receipts:
            return JsonResponse({
                'status': 'error',
                'errors': ['Please upload at least one proof of payment.']
            }, status=400)

        # Enforce the maximum of 3 receipt files
        if len(receipts) > 3:
            return JsonResponse({
                'status': 'error',
                'errors': ['You can upload a maximum of 3 proof of payment images.']
            }, status=400)

        enrollment_request = EnrollmentRequest.objects.create(
            student=request.user,
            course=form.cleaned_data['course'],
            year_level=form.cleaned_data['year_level'],
            semester=form.cleaned_data['semester'],
            status='pending',
        )
        # Set the many-to-many subjects relationship
        enrollment_request.subjects.set(form.cleaned_data['subjects'])

        # Save each receipt file as an EnrollmentReceipt record
        saved_count = 0
        for receipt_file in receipts:
            try:
                EnrollmentReceipt.objects.create(
                    enrollment_request=enrollment_request,
                    image=receipt_file,  # Django saves the file to MEDIA_ROOT/receipts/ automatically
                )
                saved_count += 1
            except Exception:
                pass  # Skip files that fail to save (e.g. disk error)

        # If no receipts were saved at all, roll back the enrollment request
        if saved_count == 0:
            enrollment_request.delete()  # Remove the incomplete enrollment request
            return JsonResponse({
                'status': 'error',
                'errors': ['Failed to save proof of payment. Please try again.']
            }, status=400)

        # All records saved successfully — return a success response
        return JsonResponse({
            'status': 'ok',
            'message': 'Enrollment request submitted successfully.'
        })

    def get(self, request):
        # GET requests to /home/enroll/ are not supported; redirect to the home page
        return redirect('studenthome:index')
