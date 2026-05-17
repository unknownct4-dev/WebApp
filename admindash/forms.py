from django import forms  # Django's form framework

from .models import Course, Subject  # Models this app manages


class CourseForm(forms.ModelForm):
    """
    ModelForm for creating or editing a Course record.

    Validates:
    - name is not blank
    - name does not exceed 200 characters
    - name is unique (excluding the current instance when editing)
    """

    class Meta:
        model = Course          # Bind this form to the Course model
        fields = ['name']       # Only the name field; description was removed from the model
        error_messages = {
            'name': {
                'required': 'Course name is required.',
                'max_length': 'Course name cannot exceed 200 characters.',
            },
        }

    def __init__(self, *args, **kwargs):
        # Call the parent __init__ to set up the form fields normally
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Validate the course name: strip whitespace, check length, check uniqueness."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Course name is required.')
        if len(name) > 200:
            raise forms.ValidationError('Course name cannot exceed 200 characters.')

        # Check that no other course already has this name
        # When editing an existing course, exclude it from the check so it can keep its own name
        qs = Course.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)  # Exclude the current record
        if qs.exists():
            raise forms.ValidationError(
                'A course with this name already exists.'
            )
        return name


class SubjectForm(forms.ModelForm):
    """
    ModelForm for creating or editing a Subject record.
    Includes both year_level (1st Year / 2nd Year) and semester (1st Semester / 2nd Semester / Summer).
    """

    class Meta:
        model = Subject
        fields = ['course', 'code', 'description', 'units', 'year_level', 'semester']
        error_messages = {
            'code': {
                'required': 'Subject code is required.',
                'max_length': 'Subject code cannot exceed 20 characters.',
            },
            'units': {
                'required': 'Units are required.',
                'invalid': 'Please enter a valid whole number for units.',
            },
            'year_level': {'required': 'Year level is required.'},
            'semester':   {'required': 'Semester is required.'},
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code:
            raise forms.ValidationError('Subject code is required.')
        qs = Subject.objects.filter(code=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A subject with this code already exists.')
        return code

    def clean_units(self):
        units = self.cleaned_data.get('units')
        if units is None:
            raise forms.ValidationError('Units are required.')
        if units < 1 or units > 9:
            raise forms.ValidationError('Units must be an integer between 1 and 9.')
        return units

    def clean_year_level(self):
        year_level = self.cleaned_data.get('year_level', '').strip()
        valid = [c[0] for c in Subject.YEAR_CHOICES]
        if not year_level:
            raise forms.ValidationError('Year level is required.')
        if year_level not in valid:
            raise forms.ValidationError(f'Valid options: {", ".join(valid)}.')
        return year_level

    def clean_semester(self):
        semester = self.cleaned_data.get('semester', '').strip()
        valid = [c[0] for c in Subject.SEMESTER_CHOICES]
        if not semester:
            raise forms.ValidationError('Semester is required.')
        if semester not in valid:
            raise forms.ValidationError(f'Valid options: {", ".join(valid)}.')
        return semester
