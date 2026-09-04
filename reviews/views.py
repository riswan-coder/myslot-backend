from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from bookings.models import Booking
from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Review.objects.filter(is_flagged=False)
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset


class SubmitReviewView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        booking_id = request.data.get('booking_id', '').strip()
        phone = request.data.get('phone', '').strip()
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')

        if not booking_id or not phone or not rating:
            return Response({'error': 'Booking ID, phone, and rating are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(booking_id=booking_id, guest_phone=phone)
        except Booking.DoesNotExist:
            return Response({'error': 'No matching booking found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != Booking.Status.COMPLETED:
            return Response({'error': 'Only completed bookings can be reviewed.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(booking, 'review'):
            return Response({'error': 'This booking has already been reviewed.'}, status=status.HTTP_400_BAD_REQUEST)

        shop = booking.slot.machine.game.shop
        review = Review.objects.create(
            booking=booking,
            shop=shop,
            guest_name=booking.guest_name,
            rating=rating,
            comment=comment,
        )
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FlagReviewView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found.'}, status=status.HTTP_404_NOT_FOUND)
        review.is_flagged = True
        review.save()
        return Response({'status': 'Review flagged and hidden.'})