# Requirements Document

## Introduction

This document defines the requirements for migrating the University of Bohol Graduate School web application from a static HTML/CSS/JS structure into a Django project. The existing application consists of six folders — `admindash`, `bookmanagement`, `landingpage`, `studentenrollment`, `studenthome`, and `studentprofile` — each of which becomes a dedicated Django app. The migration replaces browser-side `localStorage` state management and hardcoded data with a proper server-side database, Django's authentication system, and Django's template engine. All existing UI functionality and visual design must be preserved.

## Glossary

- **Django_Project**: The top-level Django project named `ubgraduateschool` that contains settings, root URL configuration, and the WSGI/ASGI entry points.
- **Django_App**: A self-contained Django application module (models, views, URLs, templates, static files) corresponding to one of the six original folders.
- **Portal**: The complete University of Bohol Graduate School web application served by the Django_Project.
- **Student**: An authenticated user with the role `student` who can view the home page, enroll in subjects, manage a profile, and claim books.
- **Admin**: An authenticated user with the role `admin` who can manage courses, subjects, enrollment requests, and admin accounts through the admin dashboard.
- **Enrollment_Request**: A record submitted by a Student containing course, year level, selected subjects, and proof-of-payment images, pending Admin verification.
- **Course**: An academic program (e.g., Master of Arts in Educational Management) managed by the Admin.
- **Subject**: An individual academic unit belonging to a Course, with a subject code, description, unit count, and year level.
- **Book_Claim**: A record submitted by a Student containing course name, book title, quantity, and optional phone number.
- **Static_Files**: CSS, JavaScript, and image assets served by Django's static file mechanism.
- **Template**: A Django HTML template that extends a base layout and uses the Django template language.
- **Session**: Django's server-side session used to persist the authenticated user's identity across requests.

---

## Requirements

### Requirement 1: Django Project Scaffold

**User Story:** As a developer, I want a properly structured Django project, so that all apps are organized under a single deployable project.

#### Acceptance Criteria

1. THE Django_Project SHALL contain a `manage.py` entry point, a `ubgraduateschool/` settings package, and a root `urls.py` that includes each Django_App's own `urls.py` under a distinct URL prefix.
2. THE Django_Project SHALL define `INSTALLED_APPS` that registers all six Django_Apps: `landingpage`, `studenthome`, `studentenrollment`, `studentprofile`, `bookmanagement`, and `admindash`.
3. THE Django_Project SHALL configure a `DATABASES` setting using SQLite for local development.
4. THE Django_Project SHALL configure `STATIC_URL`, `STATICFILES_DIRS`, and `MEDIA_URL`/`MEDIA_ROOT` such that a request to a static file URL returns an HTTP 200 response with the correct file content when `DEBUG = True`.
5. THE Django_Project SHALL configure `TEMPLATES` to locate templates inside each app's `templates/` subdirectory using `APP_DIRS = True`.
6. THE Django_Project SHALL set `AUTH_USER_MODEL` in settings to point to a custom user model that extends `AbstractUser` with a `role` field (choices: `student`, `admin`) that defaults to `student`.

---

### Requirement 2: Authentication and Role-Based Access

**User Story:** As a user, I want to log in with my credentials and be directed to the correct dashboard, so that Students and Admins each see only their own pages.

#### Acceptance Criteria

1. WHEN a user submits valid Admin credentials on the landing page login form, THE Portal SHALL authenticate the user, create a Session, and redirect to the Admin Dashboard.
2. WHEN a user submits valid Student credentials on the landing page login form, THE Portal SHALL authenticate the user, create a Session, and redirect to the Student Home page.
3. IF a login attempt is made with invalid credentials, THEN THE Portal SHALL re-render the landing page with an error message indicating the credentials are incorrect.
4. WHEN an authenticated user clicks "Log Out", THE Portal SHALL terminate the Session and redirect to the landing page.
5. WHILE a user is not authenticated, THE Portal SHALL redirect any request to a protected URL to the landing page login view.
6. WHILE a Student is authenticated, THE Portal SHALL deny access to Admin-only URLs and return an HTTP 403 response.
7. WHILE an Admin is authenticated, THE Portal SHALL deny access to Student-only URLs and return an HTTP 403 response.

---

### Requirement 3: Landing Page App (`landingpage`)

**User Story:** As a visitor, I want to see the University of Bohol landing page with login and registration options, so that I can access the portal.

#### Acceptance Criteria

1. THE `landingpage` Django_App SHALL serve the landing page at the root URL `/`.
2. WHEN a visitor submits the student registration form with last name, first name, middle name, ID number, email, password, and matching password confirmation, THE `landingpage` Django_App SHALL create a new Student user and redirect to the landing page.
3. WHEN a visitor submits the admin registration form with last name, first name, middle name, username, password, and matching password confirmation, THE `landingpage` Django_App SHALL create a pending Admin registration request and redirect to the landing page.
4. IF a student registration form is submitted with a duplicate ID number or email, THEN THE `landingpage` Django_App SHALL re-render the registration form with an error message identifying which field (ID number or email) contains the duplicate value.
5. IF a registration form is submitted with mismatched passwords, THEN THE `landingpage` Django_App SHALL re-render the registration form with a password mismatch error and SHALL NOT create a user record.
6. IF an admin registration form is submitted with a duplicate username, THEN THE `landingpage` Django_App SHALL re-render the admin registration form with an error message indicating the username is already taken and SHALL NOT create a registration request.
7. THE `landingpage` Django_App SHALL serve all assets (logo, cover image, CSS, JS) from its `static/landingpage/` directory using Django's `{% static %}` template tag.

---

### Requirement 4: Student Home App (`studenthome`)

**User Story:** As a Student, I want a home page with tabs for Overview, Programs, Updates, and Enrollment, so that I can access all student-facing information in one place.

#### Acceptance Criteria

1. THE `studenthome` Django_App SHALL serve the student home page at `/home/`, and WHILE a user is not authenticated, THE `studenthome` Django_App SHALL redirect the request to the landing page login view.
2. THE `studenthome` Django_App SHALL render the Overview tab with the university's Vision, Mission, Core Values, Goals, Objectives, and Outcomes content.
3. THE `studenthome` Django_App SHALL render the Programs tab listing all Doctorate and Master's programs retrieved from the database.
4. THE `studenthome` Django_App SHALL render the Updates tab with the university news iframe and contact information.
5. WHEN a Student selects a course and year level on the Enrollment tab, THE `studenthome` Django_App SHALL load the available Subjects for that course and year level from the database and display them in the subject selection list.
6. WHEN a Student submits the Enrollment tab form with a valid course, year level, at least one subject totalling at least 1 unit, and at least one proof-of-payment image, THE `studenthome` Django_App SHALL create an Enrollment_Request record with status `pending` and display a confirmation message, provided the Student does not already have a `verified` enrollment status.
7. IF a Student submits the Enrollment tab form with more than 9 total units selected, THEN THE `studenthome` Django_App SHALL reject the submission and display a validation error.
8. IF a Student with a `verified` enrollment status attempts to submit a new enrollment request, THEN THE `studenthome` Django_App SHALL reject the submission and display an error message indicating the Student is already enrolled.
9. THE `studenthome` Django_App SHALL display the Student's notifications showing enrollment status and submission date for each Enrollment_Request, fetched from the database on page load.
10. THE `studenthome` Django_App SHALL serve the student home page avatar image from its `static/studenthome/` directory.
11. IF a Student submits the Enrollment tab form without at least one proof-of-payment image, THEN THE `studenthome` Django_App SHALL reject the submission and display a validation error requiring the Student to upload proof of payment.

---

### Requirement 5: Student Enrollment App (`studentenrollment`)

**User Story:** As a Student, I want a dedicated enrollment page where I can select subjects and upload proof of payment, so that I can formally submit my enrollment request.

#### Acceptance Criteria

1. THE `studentenrollment` Django_App SHALL serve the enrollment page at `/enrollment/` and require Student authentication; IF a user is not authenticated, THEN THE `studentenrollment` Django_App SHALL redirect to the landing page login view.
2. THE `studentenrollment` Django_App SHALL render a course selection dropdown populated from the database.
3. WHEN a Student selects a course, THE `studentenrollment` Django_App SHALL dynamically return the available subjects for that course via a JSON endpoint at `/enrollment/subjects/<course_code>/`, where each subject entry includes subject code, subject name, and unit count.
4. WHEN a Student submits the enrollment form with a valid course, year level, at least one subject, and at least one proof-of-payment image (JPEG, PNG, or PDF, max 5 MB each), and the form submission fully succeeds, THE `studentenrollment` Django_App SHALL create an Enrollment_Request record with status `pending`, save the uploaded images to `MEDIA_ROOT`, and redirect to a confirmation page.
5. IF a Student submits the enrollment form without selecting a course, year level, or at least one subject, THEN THE `studentenrollment` Django_App SHALL re-render the form with an error message identifying the missing field(s).
6. IF a Student uploads more than 3 proof-of-payment images, THEN THE `studentenrollment` Django_App SHALL reject the upload and display an error message.
7. IF the proof-of-payment upload process results in zero successfully saved files, THEN THE `studentenrollment` Django_App SHALL treat the submission as failed, SHALL NOT create an Enrollment_Request record, and SHALL re-render the form with a validation error requiring the Student to re-upload.
8. WHEN a Student is redirected to the confirmation page at `/enrollment/confirmation/`, THE `studentenrollment` Django_App SHALL display the submitted course, year level, subjects, and total units, where total units is the sum of unit counts of all selected subjects.

---

### Requirement 6: Student Profile App (`studentprofile`)

**User Story:** As a Student, I want to view and edit my profile information and see my enrolled subjects, so that my academic record is accurate.

#### Acceptance Criteria

1. THE `studentprofile` Django_App SHALL serve the student profile page at `/profile/`; WHILE a user is not authenticated, IF a request is made to `/profile/`, THEN THE `studentprofile` Django_App SHALL redirect to the landing page login view without serving any page content.
2. THE `studentprofile` Django_App SHALL display the authenticated Student's ID number, last name, first name, middle name, email, course, year level, and enrollment status fetched from the database.
3. WHEN a Student submits the profile edit form with a valid ID number, last name, first name, and correctly formatted email address, THE `studentprofile` Django_App SHALL update the Student record in the database and re-render the profile view with the updated values.
4. IF a Student submits the profile edit form with an empty required field (ID number, last name, or first name), THEN THE `studentprofile` Django_App SHALL re-render the edit form with a per-field error message for each empty required field.
5. IF a Student submits the profile edit form with an ID number that already belongs to another Student, THEN THE `studentprofile` Django_App SHALL re-render the edit form with an error message indicating the ID number is already in use and SHALL NOT update the Student record.
6. THE `studentprofile` Django_App SHALL display the Student's enrolled subjects (subject code, name, units, schedule, status) from the Student's most recent verified Enrollment_Request in the Enrollment tab.
7. WHEN a Student uploads a new profile photo in JPEG, PNG, or GIF format with a file size of 2 MB or less, THE `studentprofile` Django_App SHALL save the image to `MEDIA_ROOT` and update the Student's profile picture field in the database.
8. IF a Student uploads a profile photo that exceeds 2 MB or is not in JPEG, PNG, or GIF format, THEN THE `studentprofile` Django_App SHALL reject the upload and display an error message without updating the profile picture field.
9. WHEN the `studentprofile` Django_App renders the profile view for an authenticated Student whose email field is empty, THE `studentprofile` Django_App SHALL display a warning notification prompting the Student to add an email address.

---

### Requirement 7: Book Management App (`bookmanagement`)

**User Story:** As a Student, I want to submit book claims and view my claimed books, so that I can track which books I have received.

#### Acceptance Criteria

1. THE `bookmanagement` Django_App SHALL serve the book claim form at `/books/claim/` and require Student authentication; IF a user is not authenticated, THEN THE `bookmanagement` Django_App SHALL redirect to the landing page login view.
2. WHEN a Student submits the claim form with a valid course name, book title, and quantity (positive integer), THE `bookmanagement` Django_App SHALL create a Book_Claim record associated with the authenticated Student and display a success notification.
3. IF a Student submits the claim form with an empty required field (course name, book title, or quantity), THEN THE `bookmanagement` Django_App SHALL re-render the form with a validation error identifying the missing field(s).
4. THE `bookmanagement` Django_App SHALL serve the claimed books list at `/books/claimed/` and require Student authentication; IF a user is not authenticated, THEN THE `bookmanagement` Django_App SHALL redirect to the landing page login view.
5. THE `bookmanagement` Django_App SHALL display all Book_Claim records belonging to the authenticated Student, including course name, book title, quantity, phone number, and submission timestamp, ordered by submission timestamp descending.
6. THE `bookmanagement` Django_App SHALL serve the enrollment summary page at `/books/enrollment/` and require Student authentication; IF a user is not authenticated, THEN THE `bookmanagement` Django_App SHALL redirect to the landing page login view.

---

### Requirement 8: Admin Dashboard App (`admindash`)

**User Story:** As an Admin, I want a dashboard to manage courses, subjects, enrollment requests, and admin accounts, so that I can administer the Graduate School portal.

#### Acceptance Criteria

1. THE `admindash` Django_App SHALL serve the admin dashboard at `/admin-dashboard/` and require Admin authentication; IF a user is not authenticated or does not have the `admin` role, THEN THE `admindash` Django_App SHALL redirect to the landing page login view.
2. THE `admindash` Django_App SHALL provide a "Manage Courses" panel that lists all Courses with their Subjects fetched from the database.
3. WHEN an Admin submits the Add Course form with a valid course name (max 200 characters), THE `admindash` Django_App SHALL create a Course record in the database and re-render the courses list; IF the course name already exists, THEN THE `admindash` Django_App SHALL re-render the form with a duplicate name error.
4. WHEN an Admin submits the Add Subject form with a valid subject code, description, unit count (integer 1–9), and year level, THE `admindash` Django_App SHALL create a Subject record linked to the selected Course and re-render the subjects list; IF the subject code already exists, THEN THE `admindash` Django_App SHALL re-render the form with a duplicate code error.
5. WHEN an Admin clicks "Remove Course" for a Course that has no associated Enrollment_Requests, THE `admindash` Django_App SHALL delete the Course record and all associated Subject records from the database; IF the Course has associated Enrollment_Requests, THEN THE `admindash` Django_App SHALL reject the deletion and display an error message.
6. THE `admindash` Django_App SHALL provide a "Manage Students" panel that lists all Enrollment_Requests on page load.
7. WHEN an Admin applies a filter by student name, ID, or status on the "Manage Students" panel, THE `admindash` Django_App SHALL re-render the panel showing only Enrollment_Requests matching all supplied filter criteria.
8. WHEN an Admin clicks "Verify" on a pending Enrollment_Request, THE `admindash` Django_App SHALL update the Enrollment_Request status to `verified` in the database; IF the Enrollment_Request is not in `pending` status, THEN THE `admindash` Django_App SHALL reject the action and display an error message.
9. WHEN an Admin clicks "Reject" on a pending or verified Enrollment_Request, THE `admindash` Django_App SHALL update the Enrollment_Request status to `rejected`; IF the Enrollment_Request is already `rejected`, THEN THE `admindash` Django_App SHALL reject the action and display an error message.
10. THE `admindash` Django_App SHALL provide a "Notifications" panel listing all Enrollment_Requests with status `pending`, ordered by submission date descending.
11. THE `admindash` Django_App SHALL provide an "Add Admin Account" panel listing pending admin registration requests and active admin accounts.
12. WHEN an Admin approves a pending admin registration request, THE `admindash` Django_App SHALL update the requesting user's role to `admin`, mark the request as `approved`, and re-render the panel with the updated request status.
13. WHEN an Admin rejects a pending admin registration request, THE `admindash` Django_App SHALL mark the request as `rejected`, re-render the panel with the updated request status, and the requesting user SHALL NOT receive admin access.

---

### Requirement 9: Data Models

**User Story:** As a developer, I want well-defined database models, so that all application data is persisted reliably.

#### Acceptance Criteria

1. THE Django_Project SHALL define a `CustomUser` model extending `AbstractUser` with fields: `role` (choices: `student`, `admin`; default: `student`), `id_number` (unique, max 20 characters, nullable/blank for admins), `middle_name` (max 100 characters, optional), `profile_picture` (ImageField stored in `MEDIA_ROOT/profile_pictures/`, optional), `course` (FK to Course, SET_NULL on delete, nullable), and `year_level` (choices: `1st Year`, `2nd Year`, `3rd Year`, `4th Year`, `5th Year`, `Summer`, optional).
2. THE Django_Project SHALL define a `Course` model with fields: `name` (unique, max 200 characters), `description` (max 500 characters, optional), and `created_at` (auto_now_add).
3. THE Django_Project SHALL define a `Subject` model with fields: `course` (FK to Course, CASCADE on delete), `code` (unique, max 20 characters), `description` (max 200 characters), `units` (integer 1–9), and `year_level` (choices: `1st Year`, `2nd Year`, `3rd Year`, `4th Year`, `5th Year`, `Summer`).
4. THE Django_Project SHALL define an `EnrollmentRequest` model with fields: `student` (FK to CustomUser, CASCADE on delete), `course` (FK to Course, SET_NULL on delete, nullable), `year_level` (choices: `1st Year`, `2nd Year`, `3rd Year`, `4th Year`, `5th Year`, `Summer`), `subjects` (M2M to Subject), `status` (choices: `pending`, `verified`, `rejected`; default: `pending`), and `submitted_at` (auto_now_add).
5. THE Django_Project SHALL define an `EnrollmentReceipt` model with fields: `enrollment_request` (FK to EnrollmentRequest, CASCADE on delete) and `image` (ImageField stored in `MEDIA_ROOT/receipts/`, accepted formats: JPEG/PNG, max 5 MB).
6. THE Django_Project SHALL define a `BookClaim` model with fields: `student` (FK to CustomUser, CASCADE on delete), `course_name` (max 200 characters), `book_title` (max 200 characters), `quantity` (positive integer), `phone` (max 20 characters, optional), and `submitted_at` (auto_now_add).
7. THE Django_Project SHALL define an `AdminRegistrationRequest` model with fields: `user` (OneToOne FK to CustomUser, CASCADE on delete), `status` (choices: `pending`, `approved`, `rejected`; default: `pending`), and `requested_at` (auto_now_add).
8. THE Django_Project SHALL enforce that all FK fields use either CASCADE or SET_NULL on delete as specified per field, and no FK field SHALL use the default RESTRICT behavior.

---

### Requirement 10: URL Structure and Navigation

**User Story:** As a developer, I want a clean URL structure, so that all pages are reachable via predictable paths and internal links work correctly.

#### Acceptance Criteria

1. THE Django_Project SHALL map the following URL prefixes to their respective Django_App URL configurations: `/` → `landingpage`, `/home/` → `studenthome`, `/enrollment/` → `studentenrollment`, `/profile/` → `studentprofile`, `/books/` → `bookmanagement`, `/admin-dashboard/` → `admindash`.
2. THE `landingpage` Django_App SHALL expose named URL patterns: `landingpage:index`, `landingpage:login`, `landingpage:logout`, `landingpage:register_student`, `landingpage:register_admin`.
3. THE `studenthome` Django_App SHALL expose named URL patterns: `studenthome:index`, `studenthome:enroll`.
4. THE `studentenrollment` Django_App SHALL expose named URL patterns: `studentenrollment:index`, `studentenrollment:subjects_json`, `studentenrollment:confirmation`.
5. THE `studentprofile` Django_App SHALL expose named URL patterns: `studentprofile:index`, `studentprofile:edit`, `studentprofile:upload_photo`.
6. THE `bookmanagement` Django_App SHALL expose named URL patterns: `bookmanagement:claim`, `bookmanagement:claimed`, `bookmanagement:enrollment`.
7. THE `admindash` Django_App SHALL expose named URL patterns: `admindash:index`, `admindash:add_course`, `admindash:remove_course`, `admindash:add_subject`, `admindash:remove_subject`, `admindash:verify_enrollment`, `admindash:reject_enrollment`, `admindash:approve_admin`, `admindash:reject_admin`.
8. THE Django_Project SHALL use Django's `{% url %}` template tag for all `href`, `action`, and `src` attributes in templates, and `reverse()` for all URL construction in views, so that no hardcoded URL strings remain.
9. WHEN a request is made to a URL path not matched by any URL pattern, THE Django_Project SHALL return an HTTP 404 response.

---

### Requirement 11: Static Files and Templates

**User Story:** As a developer, I want each app to own its templates and static files, so that the project is modular and maintainable.

#### Acceptance Criteria

1. THE Django_Project SHALL place each app's HTML templates in `<app>/templates/<app>/` following Django's namespaced template convention.
2. THE Django_Project SHALL place each app's CSS, JS, and image assets in `<app>/static/<app>/` following Django's namespaced static file convention.
3. THE Django_Project SHALL define a shared base template at `templates/base.html` that provides the common HTML shell (doctype, meta tags, static block) with named template blocks `title`, `content`, `extra_css`, and `extra_js` that all app templates extend.
4. WHEN `DEBUG = True`, THE Django_Project SHALL serve static files via `django.contrib.staticfiles` without requiring a separate web server.
5. WHEN `DEBUG = True`, IF `MEDIA_URL` and `MEDIA_ROOT` are configured in settings, THEN THE Django_Project SHALL serve uploaded media files via a `MEDIA_URL` URL pattern added to the root `urls.py`.
6. THE Django_Project SHALL convert all `<link rel="stylesheet">` and `<script src="...">` references in the six app templates to use `{% load static %}` and `{% static '<path>' %}` such that no hardcoded `href` or `src` attributes referencing static files remain in any of the six app templates.
