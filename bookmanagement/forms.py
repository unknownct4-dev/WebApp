from django import forms  # Django's form framework


class BookClaimForm(forms.Form):
    """
    Form for submitting a book claim request.

    Required fields: course_name, book_title, quantity (positive integer ≥ 1).
    Optional field: phone.

    Validates:
    - course_name and book_title are not blank after stripping whitespace.
    - quantity is a positive integer (≥ 1).
    """

    course_name = forms.CharField(
        max_length=200,
        label='Course Name',
        error_messages={'required': 'Course name is required.'},
    )
    book_title = forms.CharField(
        max_length=200,
        label='Book Title',
        error_messages={'required': 'Book title is required.'},
    )
    quantity = forms.IntegerField(
        min_value=1,  # Django's IntegerField enforces this via a MinValueValidator
        label='Quantity',
        error_messages={
            'required': 'Quantity is required.',
            'invalid': 'Please enter a valid whole number.',
            'min_value': 'Quantity must be at least 1.',
        },
    )
    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        required=False,  # Phone number is optional
    )

    def clean_course_name(self):
        """Reject the form if course_name is blank after stripping whitespace."""
        course_name = self.cleaned_data.get('course_name', '').strip()
        if not course_name:
            raise forms.ValidationError('Course name is required.')
        return course_name

    def clean_book_title(self):
        """Reject the form if book_title is blank after stripping whitespace."""
        book_title = self.cleaned_data.get('book_title', '').strip()
        if not book_title:
            raise forms.ValidationError('Book title is required.')
        return book_title

    def clean_quantity(self):
        """Reject the form if quantity is missing or less than 1."""
        quantity = self.cleaned_data.get('quantity')
        if quantity is None:
            raise forms.ValidationError('Quantity is required.')
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity
