# from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetView, PasswordChangeView
from django.contrib.auth.views import PasswordResetConfirmView


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordReset(PasswordResetView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset.html'


class PasswordChange(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'
