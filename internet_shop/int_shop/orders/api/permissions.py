from rest_framework.permissions import BasePermission


class UserPermission(BasePermission):
    """
    Permission allows to obtain, destroy, and update only by staff users.
    Only authenticated users can create objects.
    """

    def has_permission(self, request, view):
        if view.action in ('list', 'destroy', 'update', 'partial_update', 'retrieve'):
            return request.user.is_staff
        if view.action == 'create' and request.user.is_authenticated:
            return True
