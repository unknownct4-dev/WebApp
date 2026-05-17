from django import forms                        # Django's form framework
from django.core.validators import validate_email  # Built-in validator for email format (not used directly here; EmailField handles it)

from landingpage.models import CustomUser  # The custom user model for uniqueness checks


# Maximum allowed profile photo size
MAX_PHOTO_SIZE_MB = 2
MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024  # Convert MB to bytes for comparison

# Accepted MIME types for profile photos
ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/gif']


class ProfileEditForm(forms.Form):
    """
    Form for editing a student's profile information.

    Validates:
    - id_number: not blank, unique among other students (excludes the current user)
    - last_name: not blank
    - first_name: not blank
    - email: valid email format (optional)
    - middle_name: optional

    The current user instance must be passed via __init__ so the uniqueness
    check can exclude the user from their own ID number query.
    """

    id_number = forms.CharField(
        max_length=20,
        label='ID Number',
        error_messages={
            'required': 'ID number is required.',
            'blank': 'ID number must not be blank.',
        },
    )
    last_name = forms.CharField(
        max_length=150,
        label='Last Name',
        error_messages={
            'required': 'Last name is required.',
            'blank': 'Last name must not be blank.',
        },
    )
    first_name = forms.CharField(
        max_length=150,
        label='First Name',
        error_messages={
            'required': 'First name is required.',
            'blank': 'First name must not be blank.',
        },
    )
    middle_name = forms.CharField(
        max_length=100,
        label='Middle Name',
        required=False,  # Middle name is optional
    )
    email = forms.EmailField(
        label='Email',
        required=False,  # Email is optional; validated for format if provided
        error_messages={'invalid': 'Enter a valid email address.'},
    )

    def __init__(self, *args, user=None, **kwargs):
        """
        Accept the current user instance so the uniqueness check can
        exclude them from the query (a student may keep their own ID number).
        """
        super().__init__(*args, **kwargs)
        self.current_user = user  # Store the user for use in clean_id_number()

    def clean_id_number(self):
        """Validate that the ID number is not blank and is not already used by another student."""
        id_number = self.cleaned_data.get('id_number', '').strip()
        if not id_number:
            raise forms.ValidationError('ID number must not be blank.')

        # Query for other students with the same ID number
        qs = CustomUser.objects.filter(id_number=id_number, role='student')
        if self.current_user is not None:
            # Exclude the current user so they can keep their own ID number
            qs = qs.exclude(pk=self.current_user.pk)
        if qs.exists():
            raise forms.ValidationError('This ID number is already in use by another student.')

        return id_number

    def clean_last_name(self):
        """Validate that last name is not blank after stripping whitespace."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError('Last name must not be blank.')
        return last_name

    def clean_first_name(self):
        """Validate that first name is not blank after stripping whitespace."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError('First name must not be blank.')
        return first_name


class ProfilePhotoForm(forms.Form):
    """
    Form for uploading a student profile photo.

    Validates:
    - File type must be JPEG, PNG, or GIF (checked via content_type).
    - File size must not exceed 2 MB.
    """

    photo = forms.ImageField(
        label='Profile Photo',
        error_messages={'required': 'Please select a photo to upload.'},
    )

    def clean_photo(self):
        """Validate the uploaded photo's type and size."""
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo  # Let the required validator handle the missing file case

        # Check the MIME type reported by the browser
        content_type = getattr(photo, 'content_type', '')
        if content_type not in ALLOWED_PHOTO_TYPES:
            raise forms.ValidationError(
                'Only JPEG, PNG, and GIF images are allowed.'
            )

        # Check the file size in bytes
        if photo.size > MAX_PHOTO_SIZE_BYTES:
            raise forms.ValidationError(
                f'File size must not exceed {MAX_PHOTO_SIZE_MB} MB.'
            )

        return photo
