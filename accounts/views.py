from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from ExactusPay.context import base_meta_context

from .forms import ProfileUpdateForm, RegistrationForm, UserUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Your account has been created."))
        return redirect("accounts:profile")

    context = base_meta_context(
        meta_title=_("Create Your ExactusPay Account"),
        meta_description=_("Create an ExactusPay account to manage your profile, preferences, and demo activity."),
        canonical_path="/accounts/register/",
    )
    context["form"] = form
    return render(request, "accounts/register.html", context)


@login_required
def profile_view(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileUpdateForm(request.POST or None, instance=request.user.profile)

    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, _("Your profile has been updated."))
        return redirect("accounts:profile")

    context = base_meta_context(
        meta_title=_("Your ExactusPay Profile"),
        meta_description=_("Manage your ExactusPay account profile and language preferences."),
        canonical_path="/accounts/profile/",
    )
    context["user_form"] = user_form
    context["profile_form"] = profile_form
    return render(request, "accounts/profile.html", context)
