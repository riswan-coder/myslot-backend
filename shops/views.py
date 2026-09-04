from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAdminUser,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from accounts.permissions import IsShopOwner, IsObjectOwner

from .models import GamingCenter
from .serializers import GamingCenterSerializer


class GamingCenterViewSet(viewsets.ModelViewSet):
    """
    Gaming Center API

    Public users:
        - Can view active shops only.

    Shop owners:
        - Can create shops.
        - Can view their own shops.
        - Can update their own shops.
        - Can delete their own shops.

    Admin:
        - Can view all shops.
        - Can approve shops.
        - Can reject shops.
        - Can update/delete shops.
    """

    serializer_class = GamingCenterSerializer

    # ---------------------------------------------------------
    # QUERYSET
    # ---------------------------------------------------------

    def get_queryset(self):
        user = self.request.user

        # Admin can see all shops
        if user.is_authenticated and user.is_staff:
            return GamingCenter.objects.all().order_by('-created_at')

        # Logged-in shop owner can see their own shops
        if (
            user.is_authenticated
            and getattr(user, 'role', None) == 'owner'
        ):
            return GamingCenter.objects.filter(
                owner=user
            ).order_by('-created_at')

        # Public users can see active shops only
        return GamingCenter.objects.filter(
            status=GamingCenter.Status.ACTIVE,
            is_enabled=True
        ).order_by('-created_at')

    # ---------------------------------------------------------
    # PERMISSIONS
    # ---------------------------------------------------------

    def get_permissions(self):
        # Public users can view shops
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]

        # Only shop owners can create shops
        elif self.action == 'create':
            permission_classes = [IsShopOwner]

        # Admin-only actions
        elif self.action in ['approve', 'reject']:
            permission_classes = [IsAdminUser]

        # Owner can delete own shop
        elif self.action == 'destroy':
            permission_classes = [
                IsShopOwner,
                IsObjectOwner,
            ]

        # Owner can update own shop
        elif self.action in ['update', 'partial_update']:
            permission_classes = [
                IsShopOwner,
                IsObjectOwner,
            ]

        # Other authenticated actions
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]

        return [permission() for permission in permission_classes]

    # ---------------------------------------------------------
    # CREATE SHOP
    # ---------------------------------------------------------

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
            status=GamingCenter.Status.PENDING,
        )

    # ---------------------------------------------------------
    # APPROVE SHOP
    # ---------------------------------------------------------

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
    )
    def approve(self, request, pk=None):
        shop = self.get_object()

        shop.status = GamingCenter.Status.ACTIVE
        shop.is_enabled = True

        shop.save(
            update_fields=[
                'status',
                'is_enabled',
            ]
        )

        return Response({
            'status': 'Shop approved and activated.',
            'shop': shop.name,
            'shop_id': shop.id,
        })

    # ---------------------------------------------------------
    # REJECT SHOP
    # ---------------------------------------------------------

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
    )
    def reject(self, request, pk=None):
        shop = self.get_object()

        shop.status = GamingCenter.Status.SUSPENDED
        shop.is_enabled = False

        shop.save(
            update_fields=[
                'status',
                'is_enabled',
            ]
        )

        return Response({
            'status': 'Shop rejected and suspended.',
            'shop': shop.name,
            'shop_id': shop.id,
        })
