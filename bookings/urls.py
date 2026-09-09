from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    SlotViewSet,
    BookingViewSet,
    GuestBookingLookupView,
    GuestBookingCancelView,
    CreatePaymentOrderView,
    VerifyPaymentView,
)

router = DefaultRouter()

router.register('slots', SlotViewSet, basename='slot')
router.register('bookings', BookingViewSet, basename='booking')

urlpatterns = router.urls + [
    path(
        'guest/lookup/',
        GuestBookingLookupView.as_view(),
        name='guest-lookup'
    ),
    path(
        'guest/cancel/',
        GuestBookingCancelView.as_view(),
        name='guest-cancel'
    ),
    path(
        'payment/create-order/',
        CreatePaymentOrderView.as_view(),
        name='create-payment-order'
    ),
    path(
        'payment/verify/',
        VerifyPaymentView.as_view(),
        name='verify-payment'
    ),
]