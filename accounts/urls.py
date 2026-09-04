from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RegisterView, MeView, UserManagementViewSet

router = DefaultRouter()
router.register('users', UserManagementViewSet, basename='user-management')

urlpatterns = router.urls + [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
]