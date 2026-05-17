from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db import transaction

from landingpage.mixins import StudentRequiredMixin, AdminRequiredMixin
from bookmanagement.models import BookClaim, BookSubmission, SubmittedBook
from bookmanagement.forms import BookClaimForm
from studentenrollment.models import EnrollmentRequest


class ClaimBookView(StudentRequiredMixin, View):
    """GET/POST /books/claim/ — old book claim form (kept for backward compatibility)."""

    template_name = 'bookmanagement/claim.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': BookClaimForm()})

    def post(self, request, *args, **kwargs):
        form = BookClaimForm(request.POST)
        if form.is_valid():
            BookClaim.objects.create(
                student=request.user,
                course_name=form.cleaned_data['course_name'],
                book_title=form.cleaned_data['book_title'],
                quantity=form.cleaned_data['quantity'],
                phone=form.cleaned_data.get('phone', ''),
            )
            return render(request, self.template_name, {'form': BookClaimForm(), 'success': True})
        return render(request, self.template_name, {'form': form})


class ClaimedBooksView(StudentRequiredMixin, TemplateView):
    """GET /books/claimed/ — list all old BookClaim records for the student."""

    template_name = 'bookmanagement/claimed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claims'] = BookClaim.objects.filter(
            student=self.request.user
        ).order_by('-submitted_at')
        return context


class EnrollmentSummaryView(StudentRequiredMixin, TemplateView):
    """GET /books/enrollment/ — student's most recent enrollment request."""

    template_name = 'bookmanagement/enrollment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment'] = (
            EnrollmentRequest.objects
            .filter(student=self.request.user)
            .order_by('-submitted_at')
            .first()
        )
        return context


# ── New Book Submission views ──────────────────────────────────────────────────

class SubmitBooksView(StudentRequiredMixin, View):
    """
    POST /books/submit/
    Student submits exactly 6 book titles.
    Returns JSON so the student home page can handle it via AJAX.
    """

    def post(self, request, *args, **kwargs):
        # Collect the single title field
        titles = [request.POST.get('title_1', '').strip()]
        errors = []

        # Validate: the title must be non-empty
        if not titles[0]:
            errors.append('Please enter a book title before submitting.')

        # Validate: student must not already have a pending/active submission
        active_statuses = ['pending', 'received', 'processing', 'claimable']
        if BookSubmission.objects.filter(student=request.user, status__in=active_statuses).exists():
            errors.append('You already have an active book submission. Please wait for it to be completed before submitting again.')

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        # Create the submission and its 6 book records atomically
        with transaction.atomic():
            submission = BookSubmission.objects.create(student=request.user, status='pending')
            for title in titles:
                SubmittedBook.objects.create(submission=submission, title=title)

        return JsonResponse({'status': 'ok', 'message': 'Books submitted successfully.'})

    def get(self, request, *args, **kwargs):
        return redirect('studenthome:index')


class StudentBookStatusView(StudentRequiredMixin, View):
    """
    GET /books/status/ — returns JSON of the student's book submissions for AJAX polling.
    """

    def get(self, request, *args, **kwargs):
        submissions = (
            BookSubmission.objects
            .filter(student=request.user)
            .prefetch_related('books')
            .order_by('-submitted_at')
        )
        data = []
        for sub in submissions:
            data.append({
                'id': sub.pk,
                'status': sub.status,
                'status_display': sub.get_status_display(),
                'submitted_at': sub.submitted_at.strftime('%Y-%m-%d'),
                'books': [b.title for b in sub.books.all()],
            })
        return JsonResponse({'submissions': data})


# ── Admin book management views ────────────────────────────────────────────────

class AdminMarkReceivedView(AdminRequiredMixin, View):
    """
    POST /books/admin/<pk>/received/
    Admin confirms physical books received AND immediately starts processing.
    Skips the intermediate 'received' status — goes pending → processing in one click.
    """

    def post(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(BookSubmission, pk=pk)
        if submission.status == 'pending':
            # Jump straight to processing — no need for a separate "received" step
            submission.status = 'processing'
            submission.save(update_fields=['status'])
        return redirect('admindash:index')


class AdminMarkProcessingView(AdminRequiredMixin, View):
    """POST /books/admin/<pk>/processing/ — admin marks books as being processed."""

    def post(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(BookSubmission, pk=pk)
        if submission.status == 'received':
            submission.status = 'processing'
            submission.save(update_fields=['status'])
        return redirect('admindash:index')


class AdminMarkClaimableView(AdminRequiredMixin, View):
    """POST /books/admin/<pk>/claimable/ — admin notifies student books are ready to claim."""

    def post(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(BookSubmission, pk=pk)
        if submission.status == 'processing':
            submission.status = 'claimable'
            submission.save(update_fields=['status'])
        return redirect('admindash:index')


class AdminMarkClaimedView(AdminRequiredMixin, View):
    """POST /books/admin/<pk>/claimed/ — admin confirms student collected the books."""

    def post(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(BookSubmission, pk=pk)
        if submission.status == 'claimable':
            submission.status = 'claimed'
            submission.save(update_fields=['status'])
        return redirect('admindash:index')
