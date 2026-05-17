# Technical Design Document — Django Project Migration

## 1. System Architecture

### 1.1 Overview

The University of Bohol Graduate School portal is migrated from a collection of standalone HTML/CSS/JS files into a single Django project named **`ubgraduateschool`**. Each of the six original folders becomes a self-contained Django app. The server replaces all `localStorage`-based state and hardcoded data with a relational database (SQLite for development), Django's ORM, and Django's session-based authentication.

```
ubgraduateschool/          ← Django project root
├── manage.py
├── ubgraduateschool/      ← project package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py            ← root URL dispatcher
│   ├── wsgi.py
│   └── asgi.py
├── templates/
│   └── base.html          ← shared base template
├── landingpage/           ← Django app
├── studenthome/           ← Django app
├── studentenrollment/     ← Django app
├── studentprofile/        ← Django app
├── bookmanagement/        ← Django app
├── admindash/             ← Django app
└── media/                 ← uploaded files (gitignored)
```

### 1.2 App Responsibilities

| App | URL Prefix | Responsibility |
|---|---|---|
| `landingpage` | `/` | Landing page, login, logout, student & admin registration |
| `studenthome` | `/home/` | Student home tabs: Overview, Programs, Updates, Enrollment |
| `studentenrollment` | `/enrollment/` | Dedicated enrollment form, subject JSON API, confirmation |
| `studentprofile` | `/profile/` | View/edit student profile, photo upload, enrolled subjects |
| `bookmanagement` | `/books/` | Book claim form, claimed books list, enrollment summary |
| `admindash` | `/admin-dashboard/` | Course/subject CRUD, enrollment verification, admin account management |

### 1.3 Request / Response Flow

```
Browser → Django URL Router → View (auth check → DB query → form processing)
                                    ↓
                              Django Template (context data)
                                    ↓
                              HTTP Response (rendered HTML)
```

- All form submissions use `POST` with CSRF tokens.
- JSON responses are used only for the subjects API endpoint (`/enrollment/subjects/<course_code>/`).
- File uploads (receipts, profile photos) are handled via `enctype="multipart/form-data"` and saved to `MEDIA_ROOT`.

---

## 2. Data Models

All models live in a shared `core` app (or distributed across apps as noted). The custom user model must be defined before any other model that references it.

### 2.1 CustomUser (`landingpage/models.py`)

Extends `AbstractUser`. Set as `AUTH_USER_MODEL = 'landingpage.CustomUser'`.

```python
class CustomUser(AbstractUser):
    ROLE_CHOICES = [('student', 'Student'), ('admin', 'Admin')]
    YEAR_CHOICES = [
        ('1st Year', '1st Year'), ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'), ('4th Year', '4th Year'),
        ('5th Year', '5th Year'), ('Summer', 'Summer'),
    ]

    role         = CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    id_number    = CharField(max_length=20, unique=True, null=True, blank=True)
    middle_name  = CharField(max_length=100, blank=True)
    profile_picture = ImageField(upload_to='profile_pictures/', null=True, blank=True)
    course       = ForeignKey('admindash.Course', on_delete=SET_NULL, null=True, blank=True)
    year_level   = CharField(max_length=10, choices=YEAR_CHOICES, blank=True)
```

### 2.2 Course (`admindash/models.py`)

```python
class Course(Model):
    name        = CharField(max_length=200, unique=True)
    description = CharField(max_length=500, blank=True)
    created_at  = DateTimeField(auto_now_add=True)
```

### 2.3 Subject (`admindash/models.py`)

```python
class Subject(Model):
    YEAR_CHOICES = [...]  # same as CustomUser.YEAR_CHOICES

    course      = ForeignKey(Course, on_delete=CASCADE, related_name='subjects')
    code        = CharField(max_length=20, unique=True)
    description = CharField(max_length=200)
    units       = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(9)])
    year_level  = CharField(max_length=10, choices=YEAR_CHOICES)
```

### 2.4 EnrollmentRequest (`studentenrollment/models.py`)

```python
class EnrollmentRequest(Model):
    STATUS_CHOICES = [('pending','Pending'),('verified','Verified'),('rejected','Rejected')]

    student      = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='enrollment_requests')
    course       = ForeignKey('admindash.Course', on_delete=SET_NULL, null=True)
    year_level   = CharField(max_length=10, choices=YEAR_CHOICES)
    subjects     = ManyToManyField('admindash.Subject')
    status       = CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = DateTimeField(auto_now_add=True)
```

### 2.5 EnrollmentReceipt (`studentenrollment/models.py`)

```python
class EnrollmentReceipt(Model):
    enrollment_request = ForeignKey(EnrollmentRequest, on_delete=CASCADE, related_name='receipts')
    image              = ImageField(upload_to='receipts/')
    # Validation: JPEG/PNG only, max 5 MB — enforced in the form clean() method
```

### 2.6 BookClaim (`bookmanagement/models.py`)

```python
class BookClaim(Model):
    student      = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)
    course_name  = CharField(max_length=200)
    book_title   = CharField(max_length=200)
    quantity     = PositiveIntegerField()
    phone        = CharField(max_length=20, blank=True)
    submitted_at = DateTimeField(auto_now_add=True)
```

### 2.7 AdminRegistrationRequest (`landingpage/models.py`)

```python
class AdminRegistrationRequest(Model):
    STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]

    user         = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE)
    status       = CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = DateTimeField(auto_now_add=True)
```

### 2.8 Entity-Relationship Summary

```
CustomUser ──FK──> Course
CustomUser ──FK──> EnrollmentRequest (as student)
EnrollmentRequest ──M2M──> Subject
EnrollmentRequest ──FK──> Course
EnrollmentRequest <──FK── EnrollmentReceipt
Subject ──FK──> Course
BookClaim ──FK──> CustomUser
AdminRegistrationRequest ──OneToOne──> CustomUser
```

---

## 3. URL Structure

### 3.1 Root `urls.py`

```python
urlpatterns = [
    path('',                include('landingpage.urls',       namespace='landingpage')),
    path('home/',           include('studenthome.urls',       namespace='studenthome')),
    path('enrollment/',     include('studentenrollment.urls', namespace='studentenrollment')),
    path('profile/',        include('studentprofile.urls',    namespace='studentprofile')),
    path('books/',          include('bookmanagement.urls',    namespace='bookmanagement')),
    path('admin-dashboard/',include('admindash.urls',         namespace='admindash')),
]
# In DEBUG mode, append static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 3.2 Per-App URL Patterns

**`landingpage/urls.py`**
| Name | Path | View |
|---|---|---|
| `landingpage:index` | `` (empty) | `IndexView` |
| `landingpage:login` | `login/` | `LoginView` |
| `landingpage:logout` | `logout/` | `LogoutView` |
| `landingpage:register_student` | `register/student/` | `RegisterStudentView` |
| `landingpage:register_admin` | `register/admin/` | `RegisterAdminView` |

**`studenthome/urls.py`**
| Name | Path | View |
|---|---|---|
| `studenthome:index` | `` | `HomeView` |
| `studenthome:enroll` | `enroll/` | `EnrollView` |

**`studentenrollment/urls.py`**
| Name | Path | View |
|---|---|---|
| `studentenrollment:index` | `` | `EnrollmentView` |
| `studentenrollment:subjects_json` | `subjects/<str:course_code>/` | `SubjectsJsonView` |
| `studentenrollment:confirmation` | `confirmation/` | `ConfirmationView` |

**`studentprofile/urls.py`**
| Name | Path | View |
|---|---|---|
| `studentprofile:index` | `` | `ProfileView` |
| `studentprofile:edit` | `edit/` | `EditProfileView` |
| `studentprofile:upload_photo` | `photo/` | `UploadPhotoView` |

**`bookmanagement/urls.py`**
| Name | Path | View |
|---|---|---|
| `bookmanagement:claim` | `claim/` | `ClaimBookView` |
| `bookmanagement:claimed` | `claimed/` | `ClaimedBooksView` |
| `bookmanagement:enrollment` | `enrollment/` | `EnrollmentSummaryView` |

**`admindash/urls.py`**
| Name | Path | View |
|---|---|---|
| `admindash:index` | `` | `DashboardView` |
| `admindash:add_course` | `courses/add/` | `AddCourseView` |
| `admindash:remove_course` | `courses/<int:pk>/remove/` | `RemoveCourseView` |
| `admindash:add_subject` | `subjects/add/` | `AddSubjectView` |
| `admindash:remove_subject` | `subjects/<int:pk>/remove/` | `RemoveSubjectView` |
| `admindash:verify_enrollment` | `enrollment/<int:pk>/verify/` | `VerifyEnrollmentView` |
| `admindash:reject_enrollment` | `enrollment/<int:pk>/reject/` | `RejectEnrollmentView` |
| `admindash:approve_admin` | `admin-requests/<int:pk>/approve/` | `ApproveAdminView` |
| `admindash:reject_admin` | `admin-requests/<int:pk>/reject/` | `RejectAdminView` |

---

## 4. View Design

### 4.1 Authentication Decorators / Mixins

Two reusable access-control helpers are defined in `landingpage/mixins.py`:

```python
class StudentRequiredMixin(LoginRequiredMixin):
    """Redirects unauthenticated users to landing page; returns 403 for admins."""
    login_url = reverse_lazy('landingpage:index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        if request.user.role != 'student':
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(LoginRequiredMixin):
    """Redirects unauthenticated users to landing page; returns 403 for students."""
    login_url = reverse_lazy('landingpage:index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        if request.user.role != 'admin':
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
```

### 4.2 `landingpage` Views

- **`IndexView`** (TemplateView): Renders `landingpage/index.html`. No auth required.
- **`LoginView`** (View, POST only): Calls `authenticate()` with submitted credentials. On success, calls `login()` and redirects to `/admin-dashboard/` (admin) or `/home/` (student). On failure, re-renders `landingpage/index.html` with `{'error': 'Invalid credentials'}`.
- **`LogoutView`** (View, POST only): Calls `logout()`, redirects to `landingpage:index`.
- **`RegisterStudentView`** (View, POST only): Validates `StudentRegistrationForm`. On success, creates `CustomUser(role='student')` and redirects to `landingpage:index`. On failure, re-renders with form errors.
- **`RegisterAdminView`** (View, POST only): Validates `AdminRegistrationForm`. On success, creates `CustomUser(role='student', is_active=True)` and an `AdminRegistrationRequest(status='pending')`. Redirects to `landingpage:index`.

### 4.3 `studenthome` Views

- **`HomeView`** (`StudentRequiredMixin`, TemplateView): Fetches `Course.objects.prefetch_related('subjects').all()` and the student's `EnrollmentRequest` records. Passes both to `studenthome/home.html`.
- **`EnrollView`** (`StudentRequiredMixin`, View, POST only): Validates the enrollment form (course, year level, subjects, unit cap ≤ 9, at least one receipt). Creates `EnrollmentRequest` + `EnrollmentReceipt` records. Returns JSON `{'status': 'ok'}` or `{'errors': [...]}` for AJAX submission from the Enrollment tab.

### 4.4 `studentenrollment` Views

- **`EnrollmentView`** (`StudentRequiredMixin`, View):
  - GET: Renders `studentenrollment/enrollment.html` with all courses.
  - POST: Validates `EnrollmentForm`. On success, creates `EnrollmentRequest` + receipts, stores `enrollment_request_id` in session, redirects to `studentenrollment:confirmation`.
- **`SubjectsJsonView`** (`StudentRequiredMixin`, View, GET): Returns `JsonResponse` with subjects for the given `course_code` (filtered by `Subject.course__name` or a course code field).
- **`ConfirmationView`** (`StudentRequiredMixin`, TemplateView): Reads `enrollment_request_id` from session, fetches the `EnrollmentRequest`, renders `studentenrollment/confirmation.html`.

### 4.5 `studentprofile` Views

- **`ProfileView`** (`StudentRequiredMixin`, TemplateView): Fetches `request.user` with related course and most recent verified `EnrollmentRequest`. Renders `studentprofile/profile.html`.
- **`EditProfileView`** (`StudentRequiredMixin`, View):
  - GET: Renders edit form pre-filled with current user data.
  - POST: Validates `ProfileEditForm`. On success, saves and redirects to `studentprofile:index`. On failure, re-renders with errors.
- **`UploadPhotoView`** (`StudentRequiredMixin`, View, POST only): Validates file type (JPEG/PNG/GIF) and size (≤ 2 MB). Saves to `MEDIA_ROOT/profile_pictures/`. Updates `request.user.profile_picture`.

### 4.6 `bookmanagement` Views

- **`ClaimBookView`** (`StudentRequiredMixin`, View):
  - GET: Renders `bookmanagement/claim.html` with empty `BookClaimForm`.
  - POST: Validates form. On success, creates `BookClaim` record, re-renders with success message.
- **`ClaimedBooksView`** (`StudentRequiredMixin`, TemplateView): Fetches `BookClaim.objects.filter(student=request.user).order_by('-submitted_at')`. Renders `bookmanagement/claimed.html`.
- **`EnrollmentSummaryView`** (`StudentRequiredMixin`, TemplateView): Fetches the student's most recent `EnrollmentRequest`. Renders `bookmanagement/enrollment.html`.

### 4.7 `admindash` Views

- **`DashboardView`** (`AdminRequiredMixin`, TemplateView): Fetches all courses with subjects, all enrollment requests, pending admin registration requests, and active admin accounts. Renders `admindash/dashboard.html`.
- **`AddCourseView`** (`AdminRequiredMixin`, View, POST only): Validates `CourseForm`. Creates `Course` or returns duplicate error. Redirects to `admindash:index`.
- **`RemoveCourseView`** (`AdminRequiredMixin`, View, POST only): Checks for associated `EnrollmentRequest` records. If none, deletes course (CASCADE removes subjects). Otherwise returns error.
- **`AddSubjectView`** (`AdminRequiredMixin`, View, POST only): Validates `SubjectForm`. Creates `Subject` or returns duplicate code error.
- **`RemoveSubjectView`** (`AdminRequiredMixin`, View, POST only): Deletes `Subject` by pk.
- **`VerifyEnrollmentView`** (`AdminRequiredMixin`, View, POST only): Sets `EnrollmentRequest.status = 'verified'` if currently `'pending'`. Otherwise returns error.
- **`RejectEnrollmentView`** (`AdminRequiredMixin`, View, POST only): Sets `EnrollmentRequest.status = 'rejected'` if not already `'rejected'`. Otherwise returns error.
- **`ApproveAdminView`** (`AdminRequiredMixin`, View, POST only): Sets `AdminRegistrationRequest.status = 'approved'` and `request.user.role = 'admin'`.
- **`RejectAdminView`** (`AdminRequiredMixin`, View, POST only): Sets `AdminRegistrationRequest.status = 'rejected'`. User role remains `'student'`.

---

## 5. Forms

| Form | App | Key Validation |
|---|---|---|
| `StudentRegistrationForm` | `landingpage` | Unique `id_number`, unique `email`, password match |
| `AdminRegistrationForm` | `landingpage` | Unique `username`, password match |
| `EnrollmentForm` | `studentenrollment` | Course required, year level required, ≥1 subject, total units ≤9, ≥1 receipt |
| `EnrollmentReceiptForm` | `studentenrollment` | File type JPEG/PNG, size ≤5 MB, max 3 files |
| `ProfileEditForm` | `studentprofile` | `id_number` not blank, unique among other students; `last_name`, `first_name` not blank; valid email format |
| `ProfilePhotoForm` | `studentprofile` | File type JPEG/PNG/GIF, size ≤2 MB |
| `BookClaimForm` | `bookmanagement` | `course_name`, `book_title`, `quantity` (positive int) all required |
| `CourseForm` | `admindash` | `name` not blank, max 200 chars, unique |
| `SubjectForm` | `admindash` | `code` unique, `units` 1–9, `year_level` from choices |

---

## 6. Template Hierarchy

```
templates/
└── base.html                    ← shared shell (doctype, meta, static blocks)
    ├── landingpage/
    │   └── index.html           ← extends base.html
    ├── studenthome/
    │   └── home.html            ← extends base.html
    ├── studentenrollment/
    │   ├── enrollment.html      ← extends base.html
    │   └── confirmation.html    ← extends base.html
    ├── studentprofile/
    │   └── profile.html         ← extends base.html
    ├── bookmanagement/
    │   ├── claim.html           ← extends base.html
    │   ├── claimed.html         ← extends base.html
    │   └── enrollment.html      ← extends base.html
    └── admindash/
        └── dashboard.html       ← extends base.html
```

### 6.1 `base.html` Block Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}University of Bohol Graduate School{% endblock %}</title>
  {% load static %}
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% block content %}{% endblock %}
  {% block extra_js %}{% endblock %}
</body>
</html>
```

Each app template begins with:
```html
{% extends "base.html" %}
{% load static %}
{% block title %}Page Title{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{% static 'appname/styles.css' %}">
{% endblock %}
{% block content %}
  <!-- page HTML -->
{% endblock %}
```

---

## 7. Static Files and Media Configuration

### 7.1 Settings

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = []          # app static dirs discovered via APP_DIRS
STATIC_ROOT = BASE_DIR / 'staticfiles'   # for collectstatic in production

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 7.2 Per-App Static File Layout

```
<app>/
└── static/
    └── <app>/
        ├── styles.css   (or app-specific name)
        ├── script.js
        └── images/
```

### 7.3 Development Media Serving

In `ubgraduateschool/urls.py` (DEBUG only):
```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 8. Authentication and Session Design

- `AUTH_USER_MODEL = 'landingpage.CustomUser'`
- Login uses `django.contrib.auth.authenticate()` and `login()`.
- Student login: username field is `id_number` — the `authenticate()` call uses a custom backend or the view manually looks up the user by `id_number` before calling `authenticate(username=user.username, password=...)`.
- Admin login: standard username + password.
- `LOGIN_URL = '/'` — unauthenticated redirects go to the landing page.
- Session data: Django's default database-backed sessions (`django.contrib.sessions`).
- CSRF protection: enabled globally via `django.middleware.csrf.CsrfViewMiddleware`.

### 8.1 Custom Authentication Backend

A `StudentBackend` in `landingpage/backends.py` allows students to authenticate with their `id_number`:

```python
class StudentBackend:
    def authenticate(self, request, id_number=None, password=None):
        try:
            user = CustomUser.objects.get(id_number=id_number, role='student')
        except CustomUser.DoesNotExist:
            return None
        if user.check_password(password):
            return user

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
```

`AUTHENTICATION_BACKENDS = ['landingpage.backends.StudentBackend', 'django.contrib.auth.backends.ModelBackend']`

---

## 9. Property-Based Testing Correctness Properties

The following properties define the formal correctness specification for the system. They are encoded as executable tests using `hypothesis` (Python PBT library).

### P1 — Enrollment Unit Cap
**Property:** For any `EnrollmentRequest` persisted in the database, the sum of `units` across all associated `Subject` records is always ≤ 9.

```python
@given(st.lists(st.integers(min_value=1, max_value=9), min_size=1, max_size=9))
def test_enrollment_unit_cap(unit_list):
    assume(sum(unit_list) <= 9)
    # Construct enrollment request with subjects having these units
    # Assert EnrollmentRequest is accepted and total_units <= 9
```

### P2 — Duplicate ID Number Rejection
**Property:** For any two `CustomUser` records with `role='student'`, their `id_number` values are always distinct (no two students share an ID number).

### P3 — Role-Based Access Invariant
**Property:** For any HTTP request to a student-only URL made by a user with `role='admin'`, the response status code is always 403. For any request to an admin-only URL by a user with `role='student'`, the response status code is always 403.

### P4 — Enrollment Status Transition Validity
**Property:** An `EnrollmentRequest` status can only transition as follows: `pending → verified`, `pending → rejected`, `verified → rejected`. A `rejected` request can never be set to `rejected` again (idempotent guard). A `verified` request cannot be set to `verified` again.

### P5 — Receipt Count Invariant
**Property:** For any `EnrollmentRequest` created through the enrollment form, the number of associated `EnrollmentReceipt` records is always between 1 and 3 (inclusive).

### P6 — Book Claim Quantity Positivity
**Property:** For any `BookClaim` record persisted in the database, `quantity` is always a positive integer (≥ 1).

### P7 — Admin Registration Request Uniqueness
**Property:** For any `CustomUser`, there exists at most one `AdminRegistrationRequest` record (enforced by the `OneToOneField`).

### P8 — Course Deletion Guard
**Property:** A `Course` that has at least one associated `EnrollmentRequest` (via `EnrollmentRequest.course`) is never deleted from the database.

---

## 10. Migration Strategy

1. **Scaffold** the Django project and all six apps with `django-admin startproject` and `python manage.py startapp`.
2. **Define models** in the order: `Course` → `Subject` → `CustomUser` → `EnrollmentRequest` → `EnrollmentReceipt` → `BookClaim` → `AdminRegistrationRequest`. Run `makemigrations` and `migrate`.
3. **Convert templates**: Copy each HTML file into the appropriate `<app>/templates/<app>/` directory, add `{% extends "base.html" %}`, replace all `<link>` and `<script src>` with `{% static %}` tags, replace all hardcoded `href` navigation with `{% url %}` tags.
4. **Move static files**: Copy CSS, JS, and images into `<app>/static/<app>/`.
5. **Implement views and forms** app by app, starting with `landingpage` (auth) then `studenthome`, `studentenrollment`, `studentprofile`, `bookmanagement`, `admindash`.
6. **Wire URLs** in each app's `urls.py` and include them in the root `urls.py`.
7. **Write and run tests**: Unit tests for forms and views; property-based tests for the correctness properties above.
