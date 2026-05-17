# Implementation Tasks — Django Project Migration

## Task Dependency Graph

```
T1 (Scaffold)
 └─> T2 (Models & Migrations)
      └─> T3 (Auth Backend & Settings)
           └─> T4 (landingpage app)
                └─> T5 (studenthome app)
                └─> T6 (studentenrollment app)
                └─> T7 (studentprofile app)
                └─> T8 (bookmanagement app)
                └─> T9 (admindash app)
                     └─> T10 (Templates & Static Files)
                          └─> T11 (URL Wiring & Navigation)
                               └─> T12 (Property-Based Tests)
```

---

## T1 — Django Project Scaffold

**Depends on:** nothing

- [x] Run `django-admin startproject ubgraduateschool .` in the workspace root to create `manage.py` and the `ubgraduateschool/` settings package.
- [x] Run `python manage.py startapp landingpage`, `startapp studenthome`, `startapp studentenrollment`, `startapp studentprofile`, `startapp bookmanagement`, `startapp admindash` to create all six app directories.
- [x] Create `templates/` directory at the project root and add `base.html` with blocks `title`, `content`, `extra_css`, `extra_js`.
- [x] In `ubgraduateschool/settings.py`:
  - Add all six apps plus `django.contrib.staticfiles` and `django.contrib.sessions` to `INSTALLED_APPS`.
  - Set `TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']` and `APP_DIRS = True`.
  - Set `DATABASES` to SQLite: `{'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}`.
  - Set `STATIC_URL = '/static/'`, `STATIC_ROOT = BASE_DIR / 'staticfiles'`.
  - Set `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.
  - Set `AUTH_USER_MODEL = 'landingpage.CustomUser'`.
  - Set `LOGIN_URL = '/'`.
  - Add `AUTHENTICATION_BACKENDS` list (to be populated in T3).
- [x] Add `media/` to `.gitignore`.

**Verification:** `python manage.py check` passes with no errors.

---

## T2 — Data Models and Migrations

**Depends on:** T1

- [x] In `admindash/models.py`, define `Course` and `Subject` models exactly as specified in the design (fields, constraints, `YEAR_CHOICES`).
- [x] In `landingpage/models.py`, define `CustomUser` (extends `AbstractUser`) with `role`, `id_number`, `middle_name`, `profile_picture`, `course` (FK to `admindash.Course`, `SET_NULL`), and `year_level` fields.
- [x] In `landingpage/models.py`, define `AdminRegistrationRequest` with `user` (OneToOne to `CustomUser`, CASCADE), `status`, and `requested_at`.
- [x] In `studentenrollment/models.py`, define `EnrollmentRequest` and `EnrollmentReceipt` models.
- [x] In `bookmanagement/models.py`, define `BookClaim` model.
- [x] Run `python manage.py makemigrations` and `python manage.py migrate`.
- [x] Confirm all FK `on_delete` values match the spec: CASCADE or SET_NULL as specified per field.

**Verification:** `python manage.py migrate` completes without errors; `python manage.py shell` can import all models.

---

## T3 — Authentication Backend and Settings

**Depends on:** T2

- [x] Create `landingpage/backends.py` with `StudentBackend` class that authenticates by `id_number` + password for users with `role='student'`.
- [x] In `ubgraduateschool/settings.py`, set:
  ```python
  AUTHENTICATION_BACKENDS = [
      'landingpage.backends.StudentBackend',
      'django.contrib.auth.backends.ModelBackend',
  ]
  ```
- [x] Create `landingpage/mixins.py` with `StudentRequiredMixin` and `AdminRequiredMixin` (redirect unauthenticated to `landingpage:index`; return HTTP 403 for wrong role).

**Verification:** Unit test confirms `StudentBackend.authenticate()` returns the correct user for valid `id_number`/password and `None` for invalid credentials.

---

## T4 — `landingpage` App

**Depends on:** T3

- [x] Create `landingpage/forms.py` with:
  - `StudentRegistrationForm`: fields `last_name`, `first_name`, `middle_name`, `id_number`, `email`, `password`, `confirm_password`. Validates unique `id_number`, unique `email`, password match.
  - `AdminRegistrationForm`: fields `last_name`, `first_name`, `middle_name`, `username`, `password`, `confirm_password`. Validates unique `username`, password match.
- [x] Create `landingpage/views.py` with:
  - `IndexView` (TemplateView) — renders `landingpage/index.html`.
  - `LoginView` (View, POST) — authenticates via both backends; redirects to `/admin-dashboard/` or `/home/`; on failure re-renders with error.
  - `LogoutView` (View, POST) — calls `logout()`, redirects to `landingpage:index`.
  - `RegisterStudentView` (View, POST) — validates form, creates `CustomUser(role='student')`, redirects to `landingpage:index`.
  - `RegisterAdminView` (View, POST) — validates form, creates `CustomUser` + `AdminRegistrationRequest(status='pending')`, redirects to `landingpage:index`.
- [x] Create `landingpage/urls.py` with all five named URL patterns.
- [x] Create `landingpage/templates/landingpage/index.html` by converting `landingpage/landingpage.html`:
  - Replace `<link>` and `<script src>` with `{% static %}` tags.
  - Replace JS-driven form show/hide with server-rendered sections using Django form context.
  - Add CSRF tokens to all `<form>` elements.
  - Display login error and registration form errors from context.

**Verification:** 
- GET `/` returns HTTP 200.
- POST `/login/` with valid admin credentials redirects to `/admin-dashboard/`.
- POST `/login/` with valid student credentials redirects to `/home/`.
- POST `/login/` with invalid credentials returns HTTP 200 with error message.
- POST `/register/student/` with duplicate `id_number` returns form error.

---

## T5 — `studenthome` App

**Depends on:** T4

- [x] Create `studenthome/forms.py` with `HomeEnrollmentForm` (course, year_level, subjects M2M, proof-of-payment files).
- [x] Create `studenthome/views.py` with:
  - `HomeView` (`StudentRequiredMixin`, TemplateView): fetches courses, student's enrollment requests (for notifications), passes to template.
  - `EnrollView` (`StudentRequiredMixin`, View, POST): validates form (unit cap ≤9, ≥1 receipt, not already verified), creates `EnrollmentRequest` + `EnrollmentReceipt` records, returns JSON response.
- [x] Create `studenthome/urls.py` with `studenthome:index` and `studenthome:enroll`.
- [x] Create `studenthome/templates/studenthome/home.html` by converting `studenthome/home.html`:
  - Replace hardcoded course/subject data with `{% for course in courses %}` loops from DB context.
  - Replace `localStorage`-based notifications with server-rendered notification list from `enrollment_requests` context.
  - Replace hardcoded `href` links with `{% url %}` tags.
  - Add `{% static %}` for avatar image and CSS.
  - Add CSRF token to enrollment form.
  - Show email warning notification if `request.user.email` is empty.
- [x] Move `studenthome/home.css` to `studenthome/static/studenthome/home.css`.
- [x] Move `studenthome/gellman.jpg` to `studenthome/static/studenthome/gellman.jpg`.

**Verification:**
- GET `/home/` by unauthenticated user redirects to `/`.
- GET `/home/` by admin returns HTTP 403.
- GET `/home/` by student returns HTTP 200 with course list from DB.
- POST `/home/enroll/` with >9 units returns error.
- POST `/home/enroll/` without receipt returns error.

---

## T6 — `studentenrollment` App

**Depends on:** T4

- [x] Create `studentenrollment/forms.py` with `EnrollmentForm` and `EnrollmentReceiptForm` (file type JPEG/PNG, max 5 MB, max 3 files).
- [x] Create `studentenrollment/views.py` with:
  - `EnrollmentView` (`StudentRequiredMixin`, View): GET renders form with courses; POST validates, creates records, stores `enrollment_request_id` in session, redirects to confirmation.
  - `SubjectsJsonView` (`StudentRequiredMixin`, View, GET): returns `JsonResponse({'subjects': [{'code':..., 'name':..., 'units':...}]})` for the given course code.
  - `ConfirmationView` (`StudentRequiredMixin`, TemplateView): reads session, fetches `EnrollmentRequest`, renders confirmation.
- [x] Create `studentenrollment/urls.py` with three named URL patterns.
- [x] Create `studentenrollment/templates/studentenrollment/enrollment.html` by converting `studentenrollment/studentenrollment.html`:
  - Course dropdown populated from DB context.
  - Subject list loaded dynamically via fetch to `studentenrollment:subjects_json`.
  - CSRF token on form.
  - `{% static %}` for CSS.
- [x] Create `studentenrollment/templates/studentenrollment/confirmation.html` showing course, year level, subjects, total units.
- [x] Move CSS to `studentenrollment/static/studentenrollment/`.

**Verification:**
- GET `/enrollment/subjects/MAEM/` returns JSON with subjects for that course.
- POST `/enrollment/` with missing course returns form error.
- POST `/enrollment/` with >3 receipts returns error.
- POST `/enrollment/` with zero saved files does not create `EnrollmentRequest`.
- Successful POST redirects to `/enrollment/confirmation/` showing correct summary.

---

## T7 — `studentprofile` App

**Depends on:** T4

- [x] Create `studentprofile/forms.py` with `ProfileEditForm` and `ProfilePhotoForm`.
- [x] Create `studentprofile/views.py` with:
  - `ProfileView` (`StudentRequiredMixin`, TemplateView): fetches user + most recent verified `EnrollmentRequest` subjects.
  - `EditProfileView` (`StudentRequiredMixin`, View): GET pre-fills form; POST validates and saves.
  - `UploadPhotoView` (`StudentRequiredMixin`, View, POST): validates file, saves to `MEDIA_ROOT/profile_pictures/`, updates user.
- [x] Create `studentprofile/urls.py` with three named URL patterns.
- [x] Create `studentprofile/templates/studentprofile/profile.html` by converting `studentprofile/studentprofile.html`:
  - Display user fields from `request.user`.
  - Show enrolled subjects from verified enrollment request.
  - Show email warning if `request.user.email` is empty.
  - `{% static %}` and `{% url %}` throughout.
- [x] Move CSS to `studentprofile/static/studentprofile/`.

**Verification:**
- GET `/profile/` by unauthenticated user redirects to `/`.
- POST `/profile/edit/` with empty `last_name` returns per-field error.
- POST `/profile/edit/` with duplicate `id_number` returns error without saving.
- POST `/profile/photo/` with file >2 MB returns error.
- POST `/profile/photo/` with valid JPEG saves file and updates `profile_picture` field.

---

## T8 — `bookmanagement` App

**Depends on:** T4

- [x] Create `bookmanagement/forms.py` with `BookClaimForm`.
- [x] Create `bookmanagement/views.py` with `ClaimBookView`, `ClaimedBooksView`, `EnrollmentSummaryView`.
- [x] Create `bookmanagement/urls.py` with three named URL patterns.
- [x] Create templates by converting existing HTML files:
  - `bookmanagement/templates/bookmanagement/claim.html` from `claim-books.html`.
  - `bookmanagement/templates/bookmanagement/claimed.html` from `claimed-books.html`.
  - `bookmanagement/templates/bookmanagement/enrollment.html` from `enrollment.html`.
  - Replace all static refs with `{% static %}`, all hrefs with `{% url %}`, add CSRF tokens.
- [x] Move CSS and images to `bookmanagement/static/bookmanagement/`.

**Verification:**
- GET `/books/claim/` by unauthenticated user redirects to `/`.
- POST `/books/claim/` with empty `book_title` returns validation error.
- POST `/books/claim/` with valid data creates `BookClaim` and shows success message.
- GET `/books/claimed/` shows only the authenticated student's claims, ordered by `submitted_at` descending.

---

## T9 — `admindash` App

**Depends on:** T4

- [x] Create `admindash/forms.py` with `CourseForm` and `SubjectForm`.
- [x] Create `admindash/views.py` with all nine views listed in the design.
- [x] Create `admindash/urls.py` with all nine named URL patterns.
- [x] Create `admindash/templates/admindash/dashboard.html` by converting `admindash/admindashboard.html`:
  - Replace JS-managed `courses` array with server-rendered course/subject tables from DB context.
  - Replace JS-managed `enrollmentRequests` array with server-rendered enrollment request table.
  - Replace JS-managed admin registration list with server-rendered list.
  - All form actions use `{% url %}` with CSRF tokens.
  - Filter form (search by name/ID/status) submits GET to `admindash:index` with query params; view filters queryset accordingly.
- [x] Move CSS to `admindash/static/admindash/`.

**Verification:**
- GET `/admin-dashboard/` by unauthenticated user redirects to `/`.
- GET `/admin-dashboard/` by student returns HTTP 403.
- POST `/admin-dashboard/courses/add/` with duplicate course name returns error.
- POST `/admin-dashboard/courses/<pk>/remove/` for course with enrollment requests returns error.
- POST `/admin-dashboard/enrollment/<pk>/verify/` sets status to `verified`.
- POST `/admin-dashboard/enrollment/<pk>/reject/` on already-rejected request returns error.
- POST `/admin-dashboard/admin-requests/<pk>/approve/` sets user role to `admin`.

---

## T10 — Templates and Static Files Audit

**Depends on:** T4–T9

- [x] Verify every `<link rel="stylesheet">` and `<script src>` in all templates uses `{% static %}` — no hardcoded paths remain.
- [x] Verify every navigation `href` and form `action` uses `{% url %}` — no hardcoded URL strings remain.
- [x] Verify all `<form>` elements include `{% csrf_token %}`.
- [x] Verify `base.html` is extended by all six app templates.
- [x] Run `python manage.py collectstatic --noinput` and confirm all static files are collected to `staticfiles/` without errors.
- [x] Verify uploaded media files are served at `MEDIA_URL` when `DEBUG = True`.

---

## T11 — URL Wiring and Navigation

**Depends on:** T10

- [x] Confirm root `urls.py` includes all six app URL configs with correct prefixes and namespaces.
- [x] Confirm `static(settings.MEDIA_URL, ...)` is appended to `urlpatterns` when `DEBUG = True`.
- [x] Test that a request to an unmatched URL returns HTTP 404.
- [x] Test all named URL patterns resolve correctly using `reverse()` in a Django shell.
- [x] Confirm the profile dropdown link in `studenthome` navigates to `/profile/` (not the old relative HTML path).
- [x] Confirm the logout link in all headers POSTs to `landingpage:logout`.

---

## T12 — Property-Based Tests

**Depends on:** T11

- [x] Install `hypothesis` and `pytest-django`: add to `requirements.txt`.
- [x] Create `tests/test_properties.py` with the following test functions:

  - **`test_p1_enrollment_unit_cap`**: Generate random lists of subjects with units summing to ≤9; assert `EnrollmentRequest` is created. Generate lists summing to >9; assert form validation rejects them.
  - **`test_p2_duplicate_id_rejection`**: Attempt to register two students with the same `id_number`; assert the second registration returns a form error and only one `CustomUser` exists with that `id_number`.
  - **`test_p3_role_based_access`**: For each student-only URL, assert admin user gets HTTP 403. For each admin-only URL, assert student user gets HTTP 403.
  - **`test_p4_enrollment_status_transitions`**: Assert valid transitions (`pending→verified`, `pending→rejected`, `verified→rejected`) succeed. Assert invalid transitions (`rejected→rejected`, `verified→verified`) return errors.
  - **`test_p5_receipt_count_invariant`**: Assert enrollment submissions with 0 receipts are rejected. Assert submissions with 1–3 receipts succeed. Assert submissions with >3 receipts are rejected.
  - **`test_p6_book_claim_quantity_positivity`**: Assert `BookClaimForm` rejects `quantity=0` and `quantity=-1`. Assert `quantity=1` is accepted.
  - **`test_p7_admin_request_uniqueness`**: Assert creating a second `AdminRegistrationRequest` for the same user raises an `IntegrityError` (OneToOne constraint).
  - **`test_p8_course_deletion_guard`**: Assert `RemoveCourseView` rejects deletion of a course that has associated `EnrollmentRequest` records.

- [x] Run `pytest --tb=short` and confirm all property-based tests pass.

**Verification:** All 8 property tests pass with at least 100 Hypothesis examples each.
