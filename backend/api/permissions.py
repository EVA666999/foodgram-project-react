from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user)


class IsAuthor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in
            permissions.SAFE_METHODS or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        ):
            return True
        else:
            raise PermissionDenied()


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class GuestPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["list", "retrieve", "create"]:
            return True

        if view.action == "filter":
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if view.action == "retrieve" and view.basename == "users":
            return True

        return False
