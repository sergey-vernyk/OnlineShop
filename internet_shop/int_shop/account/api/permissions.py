from rest_framework.permissions import BasePermission


class ActionsWithOwnProfilePermission(BasePermission):
    """
    Permission allows to create, update or delete only own profile.

    """

    def has_permission(self, request, view):
        if view.action in 'create' and not request.user.is_authenticated:
            return True
        if view.action in ('partial_update', 'update') and request.user.is_authenticated:
            return True
        if view.action == 'delete_own_profile' and request.user.is_authenticated:
            return True
        if view.action in ('list', 'retrieve') and request.user.is_staff:
            return True

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user == obj.user or request.user.is_staff and view.action in (
                'partial_update', 'update', 'retrieve')
        )


class IsNotAuthenticated(BasePermission):
    """
    Permission only for unauthenticated users
    """

    def has_permission(self, request, view):
        return not request.user.is_authenticated
