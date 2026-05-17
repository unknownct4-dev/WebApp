from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch


class NamedURLPatternsReverseTest(TestCase):
    """
    T11 — URL Wiring and Navigation
    Test all named URL patterns resolve correctly using reverse().

    Covers every named pattern across all six apps:
      landingpage, studenthome, studentenrollment,
      studentprofile, bookmanagement, admindash
    """

    # Patterns that require no kwargs
    SIMPLE_PATTERNS = [
        # landingpage
        ('landingpage:index',              '/'),
        ('landingpage:login',              '/login/'),
        ('landingpage:logout',             '/logout/'),
        ('landingpage:register_student',   '/register/student/'),
        ('landingpage:register_admin',     '/register/admin/'),
        # studenthome
        ('studenthome:index',              '/home/'),
        ('studenthome:enroll',             '/home/enroll/'),
        # studentenrollment
        ('studentenrollment:index',        '/enrollment/'),
        ('studentenrollment:confirmation', '/enrollment/confirmation/'),
        # studentprofile
        ('studentprofile:index',           '/profile/'),
        ('studentprofile:edit',            '/profile/edit/'),
        ('studentprofile:upload_photo',    '/profile/photo/'),
        # bookmanagement
        ('bookmanagement:claim',           '/books/claim/'),
        ('bookmanagement:claimed',         '/books/claimed/'),
        ('bookmanagement:enrollment',      '/books/enrollment/'),
        # admindash
        ('admindash:index',                '/admin-dashboard/'),
        ('admindash:add_course',           '/admin-dashboard/courses/add/'),
        ('admindash:add_subject',          '/admin-dashboard/subjects/add/'),
    ]

    # Patterns that require a pk kwarg
    PK_PATTERNS = [
        ('admindash:remove_course',      '/admin-dashboard/courses/1/remove/'),
        ('admindash:remove_subject',     '/admin-dashboard/subjects/1/remove/'),
        ('admindash:verify_enrollment',  '/admin-dashboard/enrollment/1/verify/'),
        ('admindash:reject_enrollment',  '/admin-dashboard/enrollment/1/reject/'),
        ('admindash:approve_admin',      '/admin-dashboard/admin-requests/1/approve/'),
        ('admindash:reject_admin',       '/admin-dashboard/admin-requests/1/reject/'),
    ]

    def test_simple_url_patterns_resolve(self):
        """All named URL patterns without kwargs resolve without raising NoReverseMatch."""
        for name, expected_url in self.SIMPLE_PATTERNS:
            with self.subTest(name=name):
                url = reverse(name)
                self.assertEqual(url, expected_url,
                    msg=f"{name} resolved to '{url}', expected '{expected_url}'")

    def test_subjects_json_resolves_with_course_code(self):
        """studentenrollment:subjects_json resolves with a course_code kwarg."""
        url = reverse('studentenrollment:subjects_json', kwargs={'course_code': 'MAEM'})
        self.assertEqual(url, '/enrollment/subjects/MAEM/')

    def test_pk_url_patterns_resolve(self):
        """All named URL patterns that require a pk kwarg resolve correctly."""
        for name, expected_url in self.PK_PATTERNS:
            with self.subTest(name=name):
                url = reverse(name, kwargs={'pk': 1})
                self.assertEqual(url, expected_url,
                    msg=f"{name} resolved to '{url}', expected '{expected_url}'")

    def test_all_patterns_do_not_raise(self):
        """Calling reverse() on every named pattern never raises NoReverseMatch."""
        all_simple = [name for name, _ in self.SIMPLE_PATTERNS]
        all_simple.append('studentenrollment:confirmation')
        for name in all_simple:
            with self.subTest(name=name):
                try:
                    reverse(name)
                except NoReverseMatch as exc:
                    self.fail(f"reverse('{name}') raised NoReverseMatch: {exc}")

        for name, _ in self.PK_PATTERNS:
            with self.subTest(name=name):
                try:
                    reverse(name, kwargs={'pk': 99})
                except NoReverseMatch as exc:
                    self.fail(f"reverse('{name}', pk=99) raised NoReverseMatch: {exc}")


class UnmatchedURLReturns404Test(TestCase):
    """
    T11 — URL Wiring and Navigation
    Test that a request to an unmatched URL returns HTTP 404.

    Django's URL dispatcher raises Http404 for any path that does not match
    any entry in urlpatterns. With DEBUG=True this is the default behaviour —
    no catch-all pattern exists in the root urls.py, so unmatched paths fall
    through and Django returns a 404 response.
    """

    def setUp(self):
        self.client = Client()

    def test_unmatched_url_returns_404(self):
        """A GET request to a path that matches no URL pattern returns HTTP 404."""
        response = self.client.get('/this-does-not-exist/')
        self.assertEqual(response.status_code, 404)

    def test_unmatched_nested_url_returns_404(self):
        """A deeply nested path that matches no URL pattern also returns HTTP 404."""
        response = self.client.get('/no/such/path/exists/here/')
        self.assertEqual(response.status_code, 404)

    def test_unmatched_url_with_query_string_returns_404(self):
        """An unmatched URL with a query string still returns HTTP 404."""
        response = self.client.get('/nonexistent/?foo=bar')
        self.assertEqual(response.status_code, 404)
