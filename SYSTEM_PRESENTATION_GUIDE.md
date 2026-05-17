# UB Graduate School Web App - Code and Presentation Guide

This file explains how the system is organized, how the code works, and how you can present it to an audience.

## 1. System Overview

This project is a Django web application for a graduate school student portal. It supports:

- Student registration and login
- Admin registration requests and approval
- Student home dashboard
- Enrollment request submission
- Proof-of-payment receipt upload
- Admin verification or rejection of enrollment requests
- Student profile viewing, editing, and photo upload
- Course and subject management
- Book submission and book claim tracking

The system uses Django's Model-Template-View pattern:

- Models define database tables and relationships.
- Views process browser requests and decide what response to return.
- Templates render the HTML pages shown to users.
- Forms validate user input before saving it.
- URLs connect browser paths like `/profile/` or `/admin-dashboard/` to the correct view.

## 2. Project Structure

Important folders and files:

```text
ubgraduateschool/
  settings.py        Main Django configuration
  urls.py            Root URL routing for all apps

landingpage/
  models.py          CustomUser and admin registration request models
  views.py           Landing page, login, logout, registration
  forms.py           Student and admin registration forms
  backends.py        Custom student login using ID number
  mixins.py          Student-only and admin-only access control

studenthome/
  views.py           Student dashboard and AJAX enrollment handler
  forms.py           Home-page enrollment form

studentenrollment/
  models.py          EnrollmentRequest and EnrollmentReceipt
  views.py           Dedicated enrollment page, subjects JSON, confirmation
  forms.py           Enrollment validation and receipt validation

studentprofile/
  views.py           Profile display, edit profile, upload profile photo
  forms.py           Profile and photo validation

admindash/
  models.py          Course and Subject
  views.py           Admin dashboard actions
  forms.py           Course and subject forms

bookmanagement/
  models.py          BookClaim, BookSubmission, SubmittedBook
  views.py           Student book submissions and admin book status actions

templates/
  base.html          Shared layout

staticfiles/ and app/static/
  CSS, JavaScript, and images

media/
  Uploaded profile pictures and receipts
```

## 3. Main Django Configuration

The project settings are in `ubgraduateschool/settings.py`.

Key settings:

- `INSTALLED_APPS` lists Django's built-in apps and this system's apps.
- `DATABASES` uses SQLite through `db.sqlite3`.
- `AUTH_USER_MODEL = 'landingpage.CustomUser'` tells Django to use the custom user model.
- `LOGIN_URL = '/'` sends unauthenticated users back to the landing page.
- `MEDIA_ROOT` and `MEDIA_URL` handle uploaded files like receipts and profile pictures.
- `AUTHENTICATION_BACKENDS` enables two login styles:
  - Students log in using ID number and password.
  - Admins log in using username and password.

The root URL file is `ubgraduateschool/urls.py`. It delegates paths to each app:

```text
/                  landing page, login, registration
/home/             student dashboard
/enrollment/       enrollment page
/profile/          student profile
/books/            book management
/admin-dashboard/  admin dashboard
/admin/            Django built-in admin
```

## 4. Database Models

### CustomUser

Located in `landingpage/models.py`.

This extends Django's `AbstractUser` and adds system-specific fields:

- `role`: either `student` or `admin`
- `id_number`: unique student ID for student login
- `middle_name`
- `profile_picture`
- `course`: linked to `admindash.Course`
- `year_level`

This is the central user table for both students and admins.

### AdminRegistrationRequest

Also in `landingpage/models.py`.

This stores admin account requests. When someone applies to become an admin, the system creates a normal user first, then creates an admin request with a status:

- `pending`
- `approved`
- `rejected`

An existing admin must approve the request before the user becomes an admin.

### Course and Subject

Located in `admindash/models.py`.

`Course` represents a graduate program. `Subject` belongs to a course and contains:

- subject code
- description
- number of units
- year level
- semester

Subjects are filtered by course, year level, and semester during enrollment.

### EnrollmentRequest

Located in `studentenrollment/models.py`.

This stores a student's enrollment submission:

- student
- course
- year level
- semester
- selected subjects
- status
- submitted date

The status can be:

- `pending`
- `verified`
- `rejected`

It also has a `total_units` property that sums the units of selected subjects.

### EnrollmentReceipt

Also in `studentenrollment/models.py`.

This stores uploaded proof-of-payment images connected to an enrollment request. The uploaded files are saved inside `media/receipts/`.

### Book Models

Located in `bookmanagement/models.py`.

There are two book-related flows:

- `BookClaim`: older claim form for textbook requests.
- `BookSubmission`: newer status-tracked submission process.
- `SubmittedBook`: book titles connected to a submission.

Book submission statuses are:

- `pending`
- `received`
- `processing`
- `claimable`
- `claimed`

Note: the model comment says students submit exactly 6 books, but the current view reads only `title_1`. If presenting, describe the current working behavior as a book-title submission/status tracker unless you update the code later.

## 5. Access Control

Access rules are centralized in `landingpage/mixins.py`.

### StudentRequiredMixin

Used by student-only pages.

It checks:

1. Is the user logged in?
2. Is `request.user.role == 'student'`?
3. If not, redirect or return forbidden access.

### AdminRequiredMixin

Used by admin-only pages.

It checks:

1. Is the user logged in?
2. Is `request.user.role == 'admin'`?
3. If not, redirect or return forbidden access.

This keeps role protection consistent across the system.

## 6. Authentication and Registration Flow

### Student Registration

File: `landingpage/views.py`

1. Student fills out the registration form.
2. `StudentRegistrationForm` validates:
   - unique ID number
   - unique email
   - password confirmation
3. `RegisterStudentView` creates a `CustomUser`.
4. The user gets `role='student'`.
5. The student can log in using ID number and password.

### Student Login

File: `landingpage/backends.py`

Students do not log in with username. They log in with `id_number`.

The custom `StudentBackend`:

1. Receives ID number and password.
2. Looks for a student with that ID number.
3. Checks the hashed password.
4. Returns the user if valid.

### Admin Registration

Admin registration is controlled for security.

1. A user submits the admin registration form.
2. The system creates a user with `role='student'`.
3. It creates an `AdminRegistrationRequest` with `status='pending'`.
4. An existing admin approves the request.
5. Approval changes the user's role to `admin`.

### Admin Login

Admins log in with username and password through Django's default authentication backend. The login view only allows access if the user role is `admin`.

## 7. Student Workflow

### Student Home

File: `studenthome/views.py`

The student home page loads:

- all courses and subjects
- the student's enrollment requests
- the student's book submissions
- an enrollment form

This gives the student one central dashboard.

### Enrollment Submission

There are two enrollment entry points:

- `/home/enroll/` from the student dashboard using AJAX
- `/enrollment/` from the dedicated enrollment page

Both flows validate:

- course
- year level
- semester
- selected subjects
- total units must not exceed 9
- at least one receipt
- maximum of 3 receipt images
- receipt type must be JPEG or PNG
- receipt size must not exceed 5 MB

After validation:

1. The system creates an `EnrollmentRequest`.
2. It connects selected subjects through a many-to-many relationship.
3. It saves receipt images as `EnrollmentReceipt` records.
4. The request starts with `status='pending'`.
5. The admin later verifies or rejects it.

### Subject Loading

File: `studentenrollment/views.py`

`SubjectsJsonView` returns subjects as JSON. It lets the front end update the subject list when the student selects a course, year level, or semester.

This makes the enrollment form dynamic instead of showing every subject at once.

### Profile Page

File: `studentprofile/views.py`

The profile page shows:

- student's personal information
- profile photo
- latest verified enrollment
- enrolled subjects

Students can edit personal details and upload a profile photo.

Profile photos are stored in:

```text
media/profile_pictures/
```

## 8. Admin Workflow

File: `admindash/views.py`

The admin dashboard is the control center. It displays:

- courses
- subjects
- enrollment requests
- pending admin registration requests
- active admin accounts
- book submissions

### Course and Subject Management

Admins can:

- add courses
- remove courses
- add subjects
- remove subjects

Course deletion is protected. A course cannot be removed if enrollment requests already reference it.

### Enrollment Verification

When an admin verifies an enrollment:

1. The `EnrollmentRequest.status` changes from `pending` to `verified`.
2. The student's `course` field is updated.
3. The student's `year_level` field is updated.
4. The profile page can now show the verified enrollment.

When an admin rejects an enrollment:

1. The `EnrollmentRequest.status` changes to `rejected`.
2. The request remains in the database for record keeping.

### Admin Account Approval

Admins can approve or reject pending admin requests.

Approval changes:

```text
CustomUser.role: student -> admin
AdminRegistrationRequest.status: pending -> approved
```

Rejection changes only the request status. The user does not gain admin access.

### Book Submission Management

Admins update a student's book submission status:

```text
pending -> processing -> claimable -> claimed
```

The dashboard also counts pending and claimable book submissions for quick visibility.

## 9. Important Data Relationships

Here is a simplified relationship map:

```text
CustomUser
  has many EnrollmentRequest
  has many BookSubmission
  has many BookClaim
  may belong to one Course

Course
  has many Subject
  has many CustomUser through student course assignment
  has many EnrollmentRequest

EnrollmentRequest
  belongs to one CustomUser
  belongs to one Course
  has many Subject through many-to-many
  has many EnrollmentReceipt

BookSubmission
  belongs to one CustomUser
  has many SubmittedBook

AdminRegistrationRequest
  belongs to one CustomUser
```

## 10. Why the System Is Designed This Way

The system separates responsibilities by app:

- `landingpage` handles identity: registration, login, logout, users.
- `studenthome` handles the student dashboard experience.
- `studentenrollment` handles enrollment records and receipt uploads.
- `studentprofile` handles personal student information.
- `admindash` handles administrative control.
- `bookmanagement` handles book-related student requests.

This separation makes the project easier to explain, maintain, and debug because each app has one major responsibility.

## 11. Presentation Script

You can use this as your spoken presentation.

### Opening

Good day everyone. Our system is a Django-based Graduate School Web Application designed to support students and administrators in managing enrollment, profiles, courses, subjects, payment receipts, and book submissions.

The main goal of the system is to reduce manual processing by giving students an online portal and giving administrators a dashboard where they can review and manage requests.

### Architecture

The project follows Django's Model-Template-View structure. Models define the database, views handle the logic, templates display the pages, and forms validate user input.

The system is divided into several apps. Each app has a clear role. For example, the landing page app handles login and registration, the enrollment app handles enrollment requests, and the admin dashboard app handles administrator actions.

### User Roles

There are two main roles: student and admin.

Students can register, log in using their ID number, view their dashboard, submit enrollment requests, upload receipts, manage their profile, and submit book-related requests.

Admins can log in using a username and password, manage courses and subjects, verify or reject enrollment requests, approve admin registration requests, and update book submission statuses.

### Registration and Login

For students, registration requires basic personal information, an ID number, email, and password. The system checks that the ID number and email are unique.

For admins, registration is not automatically approved. A request is created first, and an existing admin must approve it. This protects the system from unauthorized admin access.

### Enrollment Flow

The enrollment flow begins when a student selects a course, year level, semester, and subjects. The system filters subjects based on those choices. It also validates that the student selects at least one subject and that the total units do not exceed 9.

The student must upload proof of payment. The system accepts up to 3 receipt images, only JPEG or PNG, with a maximum size of 5 MB each.

After submission, the request is marked as pending. An admin then reviews it and either verifies or rejects it.

### Admin Dashboard

The admin dashboard is the central management area. It shows courses, subjects, enrollment requests, admin account requests, active admins, and book submissions.

When an admin verifies an enrollment, the system updates the enrollment request and also updates the student's course and year level. This lets the profile page show the student's verified enrollment information.

### Profile and File Uploads

Students can view and edit their profile information. They can also upload a profile picture. Uploaded files are stored in the media folder, while normal design files like CSS and images are stored as static files.

### Closing

Overall, this system improves the enrollment process by organizing student records, making admin review easier, and keeping the workflow digital. It uses Django's built-in security features, custom role checks, form validation, and database relationships to keep the system structured and reliable.

## 12. Demo Flow for an Audience

Use this order during a live demonstration:

1. Show the landing page.
2. Register or log in as a student.
3. Show the student dashboard.
4. Submit an enrollment request with selected subjects and receipt upload.
5. Show that the request is pending.
6. Log out and log in as admin.
7. Open the admin dashboard.
8. Show courses and subjects.
9. Verify or reject the enrollment request.
10. Return to the student profile and show the verified enrollment.
11. Demonstrate book submission status if needed.

## 13. Common Questions and Suggested Answers

### Why did you use Django?

Django provides built-in tools for routing, authentication, database models, forms, templates, sessions, and admin features. This makes it suitable for a secure school management system.

### Why use a custom user model?

The system needs extra user fields such as role, ID number, middle name, profile picture, course, and year level. A custom user model lets us store those directly on the user account.

### How is student login different from admin login?

Students log in using their ID number through a custom authentication backend. Admins log in using username and password through Django's default backend. The views also check the user's role before redirecting them.

### How does the system prevent unauthorized access?

Student pages use `StudentRequiredMixin`, and admin pages use `AdminRequiredMixin`. These mixins check whether the user is logged in and whether they have the correct role.

### How are receipts handled?

Receipt files are uploaded through forms, validated by type and size, saved in the media folder, and linked to an enrollment request using the `EnrollmentReceipt` model.

### What happens after an enrollment is verified?

The enrollment request status becomes `verified`, and the student's course and year level are copied to the student's profile record.

### What database is used?

The project currently uses SQLite through the `db.sqlite3` file. This is suitable for local development and demonstrations.

## 14. Technical Highlights

- Custom user model with student/admin roles
- Custom student authentication by ID number
- Role-based access control through reusable mixins
- Dynamic subject loading through JSON
- Enrollment receipt upload validation
- Admin approval workflow
- Many-to-many relationship between enrollments and subjects
- Dashboard filtering by student name, ID, and status
- Separate apps for clearer organization

## 15. Files to Mention During Code Explanation

When explaining the code, focus on these files:

```text
ubgraduateschool/settings.py
ubgraduateschool/urls.py
landingpage/models.py
landingpage/views.py
landingpage/backends.py
landingpage/mixins.py
studentenrollment/models.py
studentenrollment/forms.py
studentenrollment/views.py
admindash/models.py
admindash/views.py
studentprofile/views.py
bookmanagement/models.py
bookmanagement/views.py
```

These files show the most important backend logic and are enough to explain the inner workings of the system.
