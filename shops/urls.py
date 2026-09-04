from rest_framework.routers import DefaultRouter
from .views import GamingCenterViewSet

router = DefaultRouter()
router.register('gaming-centers', GamingCenterViewSet, basename='gaming-center')

urlpatterns = router.urls