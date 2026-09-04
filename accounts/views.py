from rest_framework import generics
from .models import User
from .serializers import RegisterSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework import serializers

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_staff': user.is_staff,
        })


class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'is_active', 'date_joined']


class UserManagementViewSet(viewsets.ModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = User.objects.exclude(is_staff=True).order_by('-date_joined')

        role = self.request.query_params.get('role')
        search = self.request.query_params.get('search')

        if role:
            queryset = queryset.filter(role=role)

        if search:
            queryset = queryset.filter(username__icontains=search)

        return queryset

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()

        return Response({
            'status': 'User suspended.'
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()

        return Response({
            'status': 'User activated.'
        })

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        # Extra safety: never allow an admin account to be deleted
        if user.is_staff:
            return Response(
                {'detail': 'Admin users cannot be deleted.'},
                status=403
            )

        username = user.username
        user.delete()

        return Response({
            'status': 'User deleted successfully.',
            'username': username,
        })