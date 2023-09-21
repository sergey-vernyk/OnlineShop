from rest_framework.permissions import BasePermission


class IsOrderOwnerOrAdmin(BasePermission):
    """
    Permission allows to interact with order(s) only owner of order(s)
    """

    def has_object_permission(self, request, view, obj):
        return bool(request.user == obj.profile.user or request.user.is_staff)

    def has_permission(self, request, view):
        if view.action == 'list' and not request.user.is_staff:
            return False
        return True
