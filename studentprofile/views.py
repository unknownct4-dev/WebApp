import os  # Used to build file paths and create directories

from django.conf import settings          # Access MEDIA_ROOT for file storage
from django.shortcuts import render, redirect  # render() builds an HTML response; redirect() sends the browser to a new URL
from django.views import View             # Base class for class-based views
from django.views.generic import TemplateView  # Convenience view that just renders a template
from django.urls import reverse           # Resolves a named URL to a string path

from landingpage.mixins import StudentRequiredMixin  # Restricts access to authenticated students only
from studentenrollment.models import EnrollmentRequest  # Used to fetch the student's verified enrollment
from .forms import ProfileEditForm, ProfilePhotoForm    # Forms defined in this app


class ProfileView(StudentRequiredMixin, TemplateView):
    """
    GET /profile/
    Displays the authenticated student's profile page.

    Fetches the current user (with related course) and the most recent
    verified EnrollmentRequest (with its subjects) to populate the Enrollment tab.
    Shows a warning if the student's email address is empty.
    """
    template_name = 'studentprofile/profile.html'

    def get_context_data(self, **kwargs):
        """Build the template context with user data and enrollment information."""
        context = super().get_context_data(**kwargs)
        user = self.request.user  # The currently logged-in student

        # Fetch the most recent verified enrollment request with subjects pre-loaded
        latest_enrollment = (
            EnrollmentRequest.objects
            .filter(student=user, status='verified')  # Only verified enrollments
            .prefetch_related('subjects')              # Pre-load subjects to avoid extra queries
            .order_by('-submitted_at')                 # Most recent first
            .first()                                   # Get only the latest one
        )

        context['user'] = user
        context['latest_enrollment'] = latest_enrollment
        # Warn the student if their email field is empty (shown as a notification banner)
        context['email_missing'] = not user.email

        return context


class EditProfileView(StudentRequiredMixin, View):
    """
    GET  /profile/edit/ — Renders the profile edit form pre-filled with the current user's data.
    POST /profile/edit/ — Validates ProfileEditForm; on success saves and redirects to
                          studentprofile:index; on failure re-renders with per-field errors.
    """
    template_name = 'studentprofile/profile.html'

    def get(self, request, *args, **kwargs):
        """Render the edit form pre-filled with the student's current data."""
        user = request.user
        # Pre-fill the form with the student's existing values
        initial = {
            'id_number': user.id_number or '',
            'last_name': user.last_name,
            'first_name': user.first_name,
            'middle_name': user.middle_name,
            'email': user.email,
        }
        # Pass the current user to the form so it can exclude them from the uniqueness check
        form = ProfileEditForm(initial=initial, user=user)
        return render(request, self.template_name, {
            'edit_form': form,
            'show_edit': True,       # Tell the template to show the edit panel
            'user': user,
            'email_missing': not user.email,
        })

    def post(self, request, *args, **kwargs):
        """Process the submitted profile edit form."""
        user = request.user
        # Bind the submitted data to the form, passing the current user for uniqueness checks
        form = ProfileEditForm(request.POST, user=user)

        if form.is_valid():
            # Update the user's fields with the validated data
            user.id_number = form.cleaned_data['id_number']
            user.last_name = form.cleaned_data['last_name']
            user.first_name = form.cleaned_data['first_name']
            user.middle_name = form.cleaned_data.get('middle_name', '')
            user.email = form.cleaned_data.get('email', '')
            user.save()  # Persist all changes to the database
            return redirect(reverse('studentprofile:index'))  # Redirect to the profile page

        # Form has errors — re-render the edit panel with validation messages
        return render(request, self.template_name, {
            'edit_form': form,
            'show_edit': True,
            'user': user,
            'email_missing': not user.email,
        })


class UploadPhotoView(StudentRequiredMixin, View):
    """
    POST /profile/photo/
    Validates the uploaded photo (JPEG/PNG/GIF, ≤ 2 MB).
    Saves the file to MEDIA_ROOT/profile_pictures/ and updates the
    user's profile_picture field.

    On validation failure, stores an error message in the session and
    redirects back to the profile page.
    """

    def get(self, request, *args, **kwargs):
        # GET requests are not supported for this endpoint; redirect to the profile page
        return redirect(reverse('studentprofile:index'))

    def post(self, request, *args, **kwargs):
        # Bind the uploaded file to the form for validation
        form = ProfilePhotoForm(request.POST, request.FILES)

        if form.is_valid():
            photo = form.cleaned_data['photo']  # The validated InMemoryUploadedFile object

            # Build the destination directory path inside MEDIA_ROOT
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pictures')
            os.makedirs(upload_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Use a unique filename to avoid overwriting other students' photos
            filename = f"{request.user.pk}_{photo.name}"
            file_path = os.path.join(upload_dir, filename)

            # Write the uploaded file to disk in chunks (handles large files efficiently)
            with open(file_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)

            # Store the relative path (relative to MEDIA_ROOT) on the user model
            # Django's ImageField stores paths relative to MEDIA_ROOT
            relative_path = os.path.join('profile_pictures', filename)
            request.user.profile_picture = relative_path
            request.user.save()  # Persist the updated profile_picture field

            return redirect(reverse('studentprofile:index'))

        # Validation failed — extract the first error message and store it in the session
        errors = form.errors.get('photo', [])
        error_message = errors[0] if errors else 'Invalid photo upload.'
        request.session['photo_upload_error'] = error_message  # Template reads this on the next GET
        return redirect(reverse('studentprofile:index'))
