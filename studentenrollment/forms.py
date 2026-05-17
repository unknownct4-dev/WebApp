from django import forms              # Django's form framework
from admindash.models import Course, Subject  # Models used to populate form dropdowns


class MultipleFileInput(forms.FileInput):
    """
    Custom file input widget that allows selecting multiple files at once.
    Sets allow_multiple_selected = True so the browser renders <input multiple>.
    """
    allow_multiple_selected = True


# Year level choices for the enrollment form dropdown
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

MAX_RECEIPT_SIZE_MB = 5                                    # Maximum allowed file size in megabytes
MAX_RECEIPT_SIZE_BYTES = MAX_RECEIPT_SIZE_MB * 1024 * 1024  # Convert MB to bytes for comparison
ALLOWED_RECEIPT_TYPES = ['image/jpeg', 'image/png']        # Only JPEG and PNG receipts are accepted
MAX_RECEIPTS = 3                                           # Maximum number of receipt files per submission


class EnrollmentForm(forms.Form):
    """
    Main enrollment form. Validates course, year level, semester, subjects, and receipts.
    """

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


class EnrollmentReceiptForm(forms.Form):
    """
    Form for validating a single proof-of-payment receipt upload.
    For multi-file validation, use the validate_receipt_files() utility function instead.
    """

    receipts = forms.FileField(
        widget=MultipleFileInput(),  # Allow multiple file selection in the browser
        required=True,
        label='Proof of Payment'
    )

    def clean_receipts(self):
        """
        Validate a single uploaded receipt file.
        Note: For multiple file uploads, validation is done in the view using
        request.FILES.getlist('receipts') and the validate_receipt_files() function.
        """
        receipt = self.cleaned_data.get('receipts')
        if receipt:
            # Check that the file is a JPEG or PNG
            if receipt.content_type not in ALLOWED_RECEIPT_TYPES:
                raise forms.ValidationError(
                    f'Only JPEG and PNG files are allowed. Got: {receipt.content_type}'
                )
            # Check that the file does not exceed the size limit
            if receipt.size > MAX_RECEIPT_SIZE_BYTES:
                raise forms.ValidationError(
                    f'File size must not exceed {MAX_RECEIPT_SIZE_MB} MB.'
                )
        return receipt


def validate_receipt_files(files):
    """
    Validate a list of uploaded receipt files from request.FILES.getlist('receipts').

    Checks:
    - At least one file must be provided.
    - No more than MAX_RECEIPTS (3) files may be uploaded.
    - Each file must be JPEG or PNG.
    - Each file must not exceed MAX_RECEIPT_SIZE_MB (5 MB).

    Returns:
        (valid_files, errors): A tuple where valid_files is the list of files that
        passed all checks, and errors is a list of human-readable error strings.
        If any count-level error occurs (0 files or >3 files), returns ([], [error]).
    """
    errors = []
    valid_files = []

    # Reject if no files were uploaded at all
    if not files:
        return [], ['Please upload at least one proof of payment.']

    # Reject if too many files were uploaded
    if len(files) > MAX_RECEIPTS:
        return [], [f'You can upload a maximum of {MAX_RECEIPTS} proof of payment images.']

    # Validate each file individually
    for f in files:
        if f.content_type not in ALLOWED_RECEIPT_TYPES:
            # File type is not JPEG or PNG
            errors.append(f'"{f.name}" is not a valid image type. Only JPEG and PNG are allowed.')
        elif f.size > MAX_RECEIPT_SIZE_BYTES:
            # File exceeds the size limit
            errors.append(f'"{f.name}" exceeds the {MAX_RECEIPT_SIZE_MB} MB size limit.')
        else:
            # File passed all checks — add to the valid list
            valid_files.append(f)

    return valid_files, errors
