from rest_framework.permissions import BasePermission


class IsTheSameUserThatMakeAction(BasePermission):
    """
    Allow to perform action, when user in request is the same which makes this action
    """
    def has_object_permission(self, request, view, obj):
        return request.user.pk == obj.user.pk
