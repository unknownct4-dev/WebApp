from django.shortcuts import render, redirect                    # render() builds an HTML response; redirect() sends the browser to a new URL
from django.views import View                                    # Base class for class-based views
from django.views.generic import TemplateView                    # Convenience view that just renders a template
from django.contrib.auth import authenticate, login, logout      # Django's auth helpers: verify credentials, start/end a session
from django.contrib.auth import get_user_model                   # Returns the active user model (CustomUser)

from .forms import StudentRegistrationForm, AdminRegistrationForm  # Registration forms defined in this app
from .models import AdminRegistrationRequest                       # Model for pending admin account requests

# Cache the user model at module load time to avoid repeated lookups
UserModel = get_user_model()


class IndexView(TemplateView):
    """
    Landing page — renders the login and registration page.
    No authentication required; anyone can visit this page.
    """
    template_name = 'landingpage/index.html'

    def get_context_data(self, **kwargs):
        """Pass empty registration forms to the template so they render on first visit."""
        context = super().get_context_data(**kwargs)
        # setdefault keeps any form already in context (e.g. after a failed registration)
        context.setdefault('student_form', StudentRegistrationForm())
        context.setdefault('admin_form', AdminRegistrationForm())
        return context


class StudentLoginView(View):
    """
    POST-only login view for students.
    Only authenticates via StudentBackend (id_number + password).
    Rejects the attempt if the matched account is not a student,
    preventing admins from logging in through the student form.
    """

    def post(self, request):
        # Read the submitted credentials from the POST body
        id_number = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Only try the StudentBackend — passes id_number so ModelBackend is skipped
        user = authenticate(request, id_number=id_number, password=password)

        if user is not None and user.role == 'student':
            # Valid student credentials — create a session and redirect to the home page
            login(request, user)
            return redirect('studenthome:index')
        else:
            # Authentication failed or the account is not a student
            return render(request, 'landingpage/index.html', {
                'error': 'Invalid student credentials. Please try again.',
                'login_type': 'student',             # Tell the template to re-open the student login panel
                'student_form': StudentRegistrationForm(),
                'admin_form': AdminRegistrationForm(),
            })

    def get(self, request):
        # GET requests are not supported; redirect to the landing page
        return redirect('landingpage:index')


class AdminLoginView(View):
    """
    POST-only login view for admins.
    Only authenticates via ModelBackend (username + password).
    Rejects the attempt if the matched account is not an admin,
    preventing students from logging in through the admin form.
    """

    def post(self, request):
        # Read the submitted credentials from the POST body
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Only try the ModelBackend — passes username so StudentBackend is skipped
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == 'admin':
            # Valid admin credentials — create a session and redirect to the dashboard
            login(request, user)
            return redirect('admindash:index')
        else:
            # Authentication failed or the account is not an admin
            return render(request, 'landingpage/index.html', {
                'error': 'Invalid admin credentials. Please try again.',
                'login_type': 'admin',               # Tell the template to re-open the admin login panel
                'student_form': StudentRegistrationForm(),
                'admin_form': AdminRegistrationForm(),
            })

    def get(self, request):
        # GET requests are not supported; redirect to the landing page
        return redirect('landingpage:index')


class LogoutView(View):
    """POST-only logout view. Ends the user's session and redirects to the landing page."""

    def post(self, request):
        logout(request)                      # Destroy the session and clear the auth cookie
        return redirect('landingpage:index') # Send the user back to the landing page

    def get(self, request):
        # GET requests to /logout/ are not supported; redirect to the landing page
        return redirect('landingpage:index')


class RegisterStudentView(View):
    """
    POST-only student registration view.
    Creates a new CustomUser with role='student' if the form is valid.
    """

    def post(self, request):
        form = StudentRegistrationForm(request.POST)  # Bind the submitted data to the form
        if form.is_valid():
            data = form.cleaned_data  # Validated and cleaned field values
            # Create the student user; id_number is also used as the username for uniqueness
            user = UserModel.objects.create_user(
                username=data['id_number'],          # Use id_number as the Django username field
                email=data['email'],
                password=data['password'],           # create_user() hashes the password automatically
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_name=data.get('middle_name', ''),
                id_number=data['id_number'],
                role='student',                      # Explicitly set role to student
            )
            return redirect('landingpage:index')     # Registration successful — go back to the landing page
        else:
            # Form has errors — re-render with the invalid form so errors are displayed
            return render(request, 'landingpage/index.html', {
                'student_form': form,                # Pass the form with errors back to the template
                'admin_form': AdminRegistrationForm(),
                'show_student_register': True,       # Tell the template to show the student registration panel
                'show_register': True,               # Keep the registration section open
            })

    def get(self, request):
        return redirect('landingpage:index')


class RegisterAdminView(View):
    """
    POST-only admin registration view.
    Creates a new user with role='student' and a pending AdminRegistrationRequest.
    The account stays as 'student' until an existing admin approves it from the dashboard.
    """

    def post(self, request):
        form = AdminRegistrationForm(request.POST)  # Bind the submitted data to the form
        if form.is_valid():
            data = form.cleaned_data
            # Create the user account; role starts as 'student' pending admin approval
            user = UserModel.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_name=data.get('middle_name', ''),
                role='student',   # Role stays student until an admin approves the request
                is_active=True,   # Account is active so the user can log in once approved
            )
            # Create the pending admin registration request linked to this user
            AdminRegistrationRequest.objects.create(user=user, status='pending')
            return redirect('landingpage:index')  # Registration submitted — go back to the landing page
        else:
            # Form has errors — re-render with the invalid form
            return render(request, 'landingpage/index.html', {
                'student_form': StudentRegistrationForm(),
                'admin_form': form,                  # Pass the form with errors back to the template
                'show_admin_register': True,         # Tell the template to show the admin registration panel
                'show_register': True,               # Keep the registration section open
            })

    def get(self, request):
        return redirect('landingpage:index')
