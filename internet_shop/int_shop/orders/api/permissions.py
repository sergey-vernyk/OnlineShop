from rest_framework.permissions import BasePermission


class UserPermission(BasePermission):
    """
    Permission allows to obtain, destroy, and update only staff users.
    Create objects can only authenticate user
    """

    def has_permission(self, request, view):
        if view.action in ('list', 'destroy', 'update', 'partial_update'):
            return request.user.is_staff
        if view.action == 'create' and request.user.is_authenticated:
            return True
