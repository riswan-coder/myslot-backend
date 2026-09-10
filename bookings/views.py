from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Slot, Booking
from .serializers import SlotSerializer, BookingSerializer
from accounts.permissions import IsShopOwner, IsObjectOwner
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from games.models import Machine
from rest_framework.views import APIView
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from datetime import date as date_cls
import razorpay
from django.conf import settings
import hmac
import hashlib


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


from datetime import datetime, timedelta
from django.utils import timezone

class GuestBookingCancelView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        booking_id = request.data.get('booking_id', '').strip()
        phone = request.data.get('phone', '').strip()

        try:
            booking = Booking.objects.get(booking_id=booking_id, guest_phone=phone)
        except Booking.DoesNotExist:
            return Response({'error': 'No matching booking found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != Booking.Status.UPCOMING:
            return Response({'error': 'Only upcoming bookings can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        slot_datetime = datetime.combine(booking.slot.date, booking.slot.start_time)
        slot_datetime = timezone.make_aware(slot_datetime)
        hours_until_slot = (slot_datetime - timezone.now()).total_seconds() / 3600

        if hours_until_slot < 2:
            return Response(
                {'error': 'Cancellations are only allowed at least 2 hours before your slot. Please call the shop directly.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            booking.status = Booking.Status.CANCELLED
            booking.save()
            booking.slot.is_booked = False
            booking.slot.save()

        return Response({'status': 'Booking cancelled.', 'booking_id': booking.booking_id})

class SlotViewSet(viewsets.ModelViewSet):
    serializer_class = SlotSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]

        if self.action in ['create', 'bulk_create']:
            return [IsShopOwner()]

        return [IsShopOwner(), IsObjectOwner()]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'owner':
            return Slot.objects.filter(machine__game__shop__owner=self.request.user)
        return Slot.objects.all()

    def perform_create(self, serializer):
        machine_id = self.request.data.get('machine')
        try:
            machine = Machine.objects.get(id=machine_id, game__shop__owner=self.request.user)
        except Machine.DoesNotExist:
            raise PermissionDenied("You can only add slots to your own machines.")
        serializer.save(machine=machine)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        machine_id = request.data.get('machine')
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        duration_minutes = int(request.data.get('duration_minutes', 60))
        price = request.data.get('price')

        try:
            machine = Machine.objects.get(id=machine_id, game__shop__owner=request.user)
        except Machine.DoesNotExist:
            return Response({'error': 'Machine not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            day_start = datetime.strptime(start_time_str, '%H:%M').time()
            day_end = datetime.strptime(end_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid date/time format.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date.'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        skipped_count = 0
        current_date = start_date

        while current_date <= end_date:
            current_time = datetime.combine(current_date, day_start)
            day_end_dt = datetime.combine(current_date, day_end)

            while current_time + timedelta(minutes=duration_minutes) <= day_end_dt:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=duration_minutes)).time()

                _, was_created = Slot.objects.get_or_create(
                    machine=machine,
                    date=current_date,
                    start_time=slot_start,
                    defaults={'end_time': slot_end, 'price': price},
                )
                if was_created:
                    created_count += 1
                else:
                    skipped_count += 1

                current_time += timedelta(minutes=duration_minutes)

            current_date += timedelta(days=1)

        return Response({
            'created': created_count,
            'skipped': skipped_count,
            'message': f'{created_count} slots created, {skipped_count} already existed.',
        })

class CreatePaymentOrderView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        slot_id = request.data.get('slot')

        try:
            slot = Slot.objects.get(id=slot_id)
        except Slot.DoesNotExist:
            return Response({'error': 'Slot does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if slot.is_booked:
            return Response({'error': 'This slot is already booked.'}, status=status.HTTP_400_BAD_REQUEST)

        amount_paise = int(float(slot.price) * 100)  # Razorpay expects amount in paise

        order = razorpay_client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
        })

        return Response({
            'order_id': order['id'],
            'amount': amount_paise,
            'currency': 'INR',
            'razorpay_key': settings.RAZORPAY_KEY_ID,
        })

class VerifyPaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        slot_id = request.data.get('slot')
        guest_name = request.data.get('guest_name', '')
        guest_phone = request.data.get('guest_phone', '')

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            generated_signature,
            razorpay_signature or ''
        ):
            return Response(
                {'error': 'Payment verification failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            slot = Slot.objects.get(id=slot_id)
        except Slot.DoesNotExist:
            return Response(
                {'error': 'Slot does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if slot.is_booked:
            return Response(
                {'error': 'This slot is already booked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            booking = Booking.objects.create(
                user=None,
                guest_name=guest_name,
                guest_phone=guest_phone,
                slot=slot,
                amount=slot.price,
                payment_status=Booking.PaymentStatus.PAID,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
            )

            slot.is_booked = True
            slot.save()

        serializer = BookingSerializer(booking)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'owner':
            return Booking.objects.filter(slot__machine__game__shop__owner=user)
        if user.is_authenticated:
            return Booking.objects.filter(user=user)
        return Booking.objects.none()

    def create(self, request, *args, **kwargs):
        slot_id = request.data.get('slot')
        guest_name = request.data.get('guest_name', '')
        guest_phone = request.data.get('guest_phone', '')

        if not guest_name or not guest_phone:
            return Response({'error': 'Name and phone number are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = Slot.objects.get(id=slot_id)
        except Slot.DoesNotExist:
            return Response({'error': 'Slot does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if slot.is_booked:
            return Response({'error': 'This slot is already booked.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            booking = Booking.objects.create(
                user=request.user if request.user.is_authenticated else None,
                guest_name=guest_name,
                guest_phone=guest_phone,
                slot=slot,
                amount=slot.price,
            )
            slot.is_booked = True
            slot.save()

        serializer = self.get_serializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        if booking.status != Booking.Status.UPCOMING:
            return Response({'error': 'Only upcoming bookings can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            booking.status = Booking.Status.CANCELLED
            booking.save()
            booking.slot.is_booked = False
            booking.slot.save()

        return Response({'status': 'Booking cancelled.', 'booking_id': booking.booking_id})
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        booking = self.get_object()

        if booking.status != Booking.Status.UPCOMING:
            return Response({'error': 'Only upcoming bookings can be marked completed.'}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = Booking.Status.COMPLETED
        booking.save()
        return Response({'status': 'Booking marked as completed.', 'booking_id': booking.booking_id}) 

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        if not (user.is_authenticated and user.role == 'owner'):
            return Response({'error': 'Owner access only.'}, status=status.HTTP_403_FORBIDDEN)

        base_qs = Booking.objects.filter(
            slot__machine__game__shop__owner=user
        ).exclude(status=Booking.Status.CANCELLED)

        today = date_cls.today()
        today_qs = base_qs.filter(slot__date=today)

        result = {
            'today_bookings': today_qs.count(),
            'today_revenue': today_qs.aggregate(total=Sum('amount'))['total'] or 0,
            'total_bookings': base_qs.count(),
            'total_revenue': base_qs.aggregate(total=Sum('amount'))['total'] or 0,
        }

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            range_qs = base_qs.filter(slot__date__gte=start_date, slot__date__lte=end_date)
            result['range_bookings'] = range_qs.count()
            result['range_revenue'] = range_qs.aggregate(total=Sum('amount'))['total'] or 0
            result['range_start'] = start_date
            result['range_end'] = end_date

        return Response(result)

    @action(detail=False, methods=['post'])
    def owner_book(self, request):
        user = request.user
        if not (user.is_authenticated and user.role == 'owner'):
            return Response({'error': 'Owner access only.'}, status=status.HTTP_403_FORBIDDEN)

        slot_id = request.data.get('slot')
        customer_name = request.data.get('customer_name', 'Walk-in Customer')

        try:
            slot = Slot.objects.get(id=slot_id, machine__game__shop__owner=user)
        except Slot.DoesNotExist:
            return Response({'error': 'Slot not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

        if slot.is_booked:
            return Response({'error': 'This slot is already booked.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            booking = Booking.objects.create(
                user=None,
                guest_name=customer_name,
                guest_phone='',
                slot=slot,
                amount=slot.price,
            )
            slot.is_booked = True
            slot.save()

        serializer = self.get_serializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class GuestBookingLookupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        booking_id = request.data.get('booking_id', '').strip()
        phone = request.data.get('phone', '').strip()

        if not booking_id or not phone:
            return Response({'error': 'Booking ID and phone number are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(booking_id=booking_id, guest_phone=phone)
        except Booking.DoesNotExist:
            return Response({'error': 'No matching booking found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookingSerializer(booking)
        return Response(serializer.data)

