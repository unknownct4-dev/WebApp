"""
Root URL configuration for the ubgraduateschool project.

Each app's URL patterns are included here under a distinct prefix.
The namespace argument lets templates use {% url 'appname:viewname' %} syntax.
"""
from django.contrib import admin          # Django's built-in admin site
from django.urls import path, include     # path() defines a URL pattern; include() delegates to an app's urls.py
from django.conf import settings          # Access project settings (e.g. DEBUG, MEDIA_URL)
from django.conf.urls.static import static  # Helper to serve media files during development

urlpatterns = [
    # Django's built-in admin interface at /admin/
    path('admin/', admin.site.urls),

    # Landing page app: handles /, /login/, /logout/, /register/student/, /register/admin/
    path('', include('landingpage.urls', namespace='landingpage')),

    # Student home app: handles /home/ and /home/enroll/
    path('home/', include('studenthome.urls', namespace='studenthome')),

    # Student enrollment app: handles /enrollment/, /enrollment/subjects/<code>/, /enrollment/confirmation/
    path('enrollment/', include('studentenrollment.urls', namespace='studentenrollment')),

    # Student profile app: handles /profile/, /profile/edit/, /profile/photo/
    path('profile/', include('studentprofile.urls', namespace='studentprofile')),

    # Book management app: handles /books/claim/, /books/claimed/, /books/enrollment/
    path('books/', include('bookmanagement.urls', namespace='bookmanagement')),

    # Admin dashboard app: handles /admin-dashboard/ and all its sub-paths
    path('admin-dashboard/', include('admindash.urls', namespace='admindash')),
]

# In development (DEBUG=True), serve user-uploaded media files directly through Django
# In production, a web server (nginx/Apache) would serve these files instead
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
