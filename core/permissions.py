from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Allow authors to edit/delete; others read-only.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'owner', None) == request.user

class IsTeacherUser(permissions.BasePermission):
    """
    Allows access only to users with role='teacher'.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "teacher"
        )

class IsEmailVerified(permissions.BasePermission):
    """
    Allows access only to users with verified email (email_verified=True).
    """
    message = "Email is not verified. Please verify your email before continuing."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "email_verified", False)
        )

class AllowPublicReadOnly(BasePermission):
    """
    Кастомный пермишен: неавторизованные пользователи могут только читать опубликованные посты.
    Фильтры my_posts и status доступны только авторизованным пользователям.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Проверяем, пытается ли пользователь использовать фильтры my_posts или status
            if request.query_params.get('my_posts') or request.query_params.get('status'):
                return request.user.is_authenticated
            return True  # Неавторизованные могут видеть опубликованные посты
        return request.user.is_authenticated  # Для создания/обновления нужна аутентификация