from django import forms
from admindash.models import Course, Subject

YEAR_CHOICES = [
    ('', '-- Select Year Level --'),
    ('1st Year', '1st Year'),
    ('2nd Year', '2nd Year'),
]

SEMESTER_CHOICES = [
    ('', '-- Select Semester --'),
    ('1st Semester', '1st Semester'),
    ('2nd Semester', '2nd Semester'),
    ('Summer', 'Summer'),
]


class HomeEnrollmentForm(forms.Form):
    """Enrollment form on the student home page. Filters subjects by course, year, and semester."""

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        empty_label='-- Select Course --',
        label='Course'
    )
    year_level = forms.ChoiceField(choices=YEAR_CHOICES, label='Year Level')
    semester = forms.ChoiceField(choices=SEMESTER_CHOICES, label='Semester')
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Subjects'
    )

    def __init__(self, *args, course_id=None, year_level=None, semester=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Subject.objects.none()
        if course_id:
            qs = Subject.objects.filter(course_id=course_id)
            if year_level:
                qs = qs.filter(year_level=year_level)
            if semester:
                qs = qs.filter(semester=semester)
        self.fields['subjects'].queryset = qs

    def clean_year_level(self):
        year_level = self.cleaned_data.get('year_level')
        if not year_level:
            raise forms.ValidationError('Please select a year level.')
        return year_level

    def clean_semester(self):
        semester = self.cleaned_data.get('semester')
        if not semester:
            raise forms.ValidationError('Please select a semester.')
        return semester

    def clean_subjects(self):
        subjects = self.cleaned_data.get('subjects')
        if not subjects:
            raise forms.ValidationError('Please select at least one subject.')
        total_units = sum(s.units for s in subjects)
        if total_units > 9:
            raise forms.ValidationError(
                f'Total units ({total_units}) exceed the maximum allowed (9).'
            )
        return subjects
