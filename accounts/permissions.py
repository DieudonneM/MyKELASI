from rest_framework.permissions import BasePermission

from .models import User


class IsActiveVerifiedUser(BasePermission):
    message = "Un compte actif avec une adresse email verifiee est requis."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and user.is_active
            and user.status == User.Status.ACTIVE
            and user.email_verified
        )
