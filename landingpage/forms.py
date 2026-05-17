from django import forms                        # Django's form framework
from django.contrib.auth import get_user_model  # Returns the active user model (CustomUser)

# Get the custom user model so we can query it for uniqueness checks
UserModel = get_user_model()


class StudentRegistrationForm(forms.Form):
    """
    Registration form for new student accounts.

    Fields: last_name, first_name, middle_name, id_number, email, password, confirm_password.
    Validates: unique id_number, unique email, password match.
    """

    last_name = forms.CharField(max_length=150, label='Last Name')
    first_name = forms.CharField(max_length=150, label='First Name')
    middle_name = forms.CharField(max_length=100, required=False, label='Middle Name')  # Optional field
    id_number = forms.CharField(max_length=20, label='ID Number')
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')           # Renders as a password input
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean_id_number(self):
        """Reject the form if the id_number is already taken by another user."""
        id_number = self.cleaned_data.get('id_number')
        if UserModel.objects.filter(id_number=id_number).exists():
            raise forms.ValidationError('A user with this ID number already exists.')
        return id_number

    def clean_email(self):
        """Reject the form if the email address is already registered."""
        email = self.cleaned_data.get('email')
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email address already exists.')
        return email

    def clean(self):
        """Cross-field validation: ensure both password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        # Only compare if both fields passed their individual validation
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class AdminRegistrationForm(forms.Form):
    """
    Registration form for admin account requests.

    Fields: last_name, first_name, middle_name, username, password, confirm_password.
    Validates: unique username, password match.
    Note: The account is created with role='student' until an existing admin approves it.
    """

    last_name = forms.CharField(max_length=150, label='Last Name')
    first_name = forms.CharField(max_length=150, label='First Name')
    middle_name = forms.CharField(max_length=100, required=False, label='Middle Name')  # Optional field
    username = forms.CharField(max_length=150, label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean_username(self):
        """Reject the form if the username is already taken."""
        username = self.cleaned_data.get('username')
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean(self):
        """Cross-field validation: ensure both password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data
