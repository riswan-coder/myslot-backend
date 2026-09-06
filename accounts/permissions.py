from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsShopOwner(permissions.BasePermission):
    """
    Allows read access to anyone.
    Allows write access only to authenticated users with role='owner'.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'owner'


class IsObjectOwner(permissions.BasePermission):
    """
    Object-level check: does this specific object belong to the logged-in user?
    Works for GamingCenter (has .owner) and anything with a path to .owner
    via .shop.owner or .game.shop.owner.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        owner = getattr(obj, 'owner', None)
        if owner is None and hasattr(obj, 'shop'):
            owner = obj.shop.owner
        if owner is None and hasattr(obj, 'game'):
            owner = obj.game.shop.owner
        if owner is None and hasattr(obj, 'machine'):
            owner = obj.machine.game.shop.owner

        return owner == request.user


class IsAdminOrShopOwner(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or getattr(request.user, 'role', None) == 'owner'
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return obj.owner == request.user