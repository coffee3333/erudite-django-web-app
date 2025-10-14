from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetOTP, EmailVerificationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["id"]
    list_display = ["email", "username", "role", "is_staff", "is_active", "email_verified"]
    search_fields = ["email", "username"]
    readonly_fields = ["date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("user_bio", "photo", "role")}),  # ✅ добавили роль
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("date_joined",)}),
        ("Verification", {"fields": ("email_verified",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "role", "password1", "password2"),  # ✅ добавили роль
        }),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ["user", "otp_code", "created_at", "is_used"]
    search_fields = ["user__email", "otp_code"]
    list_filter = ["is_used", "created_at"]


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "code", "created_at", "is_used"]
    search_fields = ["user__email", "code"]
    list_filter = ["is_used", "created_at"]