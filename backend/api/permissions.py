from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    message = 'Доступно только студентам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student
