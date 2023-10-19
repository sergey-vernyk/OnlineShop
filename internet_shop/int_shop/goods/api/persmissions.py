from rest_framework.permissions import BasePermission


class ObjectEditPermission(BasePermission):
    """
    Permission, that allows to create, update, partial update or delete object only
    staff users, but get list of objects, retrieve single object can anyone user
    """

    def has_permission(self, request, view):
        extra_actions = [action.__name__ for action in view.get_extra_actions()]
        if view.action in ['list', 'retrieve'] + extra_actions:
            return True
        if view.action in ('create', 'update', 'partial_update', 'destroy') and not request.user.is_staff:
            return False
        return True
