from rest_framework.routers import DefaultRouter
from .views import GameViewSet, MachineViewSet

router = DefaultRouter()
router.register('games', GameViewSet, basename='game')
router.register('machines', MachineViewSet, basename='machine')

urlpatterns = router.urls