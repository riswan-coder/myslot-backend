from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, SubmitReviewView, FlagReviewView

router = DefaultRouter()
router.register('reviews', ReviewViewSet, basename='review')

urlpatterns = router.urls + [
    path('submit/', SubmitReviewView.as_view(), name='submit-review'),
    path('<int:pk>/flag/', FlagReviewView.as_view(), name='flag-review'),
]