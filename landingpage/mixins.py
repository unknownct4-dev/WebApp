from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy


class StudentRequiredMixin(LoginRequiredMixin):
    """
    Access control mixin for student-only views.
    """

    login_url = reverse_lazy('landingpage:index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)

        if request.user.role != 'student':
            return HttpResponseForbidden(
                "Access denied. This page is for students only."
            )

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Access control mixin for admin-only views.
    """

    login_url = reverse_lazy('landingpage:index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)

        if request.user.role != 'admin':
            return HttpResponseForbidden(
                "Access denied. This page is for administrators only."
            )

        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(LoginRequiredMixin):
    """
    Access control mixin for super-admin-only views.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)

        if request.user.role != 'admin':
            return HttpResponseForbidden(
                "Access denied. This page is for administrators only."
            )

        if not request.user.is_super_admin:
            return HttpResponseForbidden(
                "Access denied. This action is for the super-admin only."
            )

        return super().dispatch(request, *args, **kwargs)
