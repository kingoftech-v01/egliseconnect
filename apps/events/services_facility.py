"""Facility / room booking service — availability checks and conflict detection."""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.constants import BookingStatus
from .models import Room, RoomBooking


class FacilityService:
    """Business logic for room availability and booking."""

    @staticmethod
    def check_availability(room, start_datetime, end_datetime, exclude_booking_id=None):
        """Return True if the room is available for the given time range."""
        conflicts = FacilityService.detect_conflicts(
            room, start_datetime, end_datetime, exclude_booking_id,
        )
        return not conflicts.exists()

    @staticmethod
    def detect_conflicts(room, start_datetime, end_datetime, exclude_booking_id=None):
        """Return queryset of overlapping confirmed/pending bookings."""
        qs = RoomBooking.objects.filter(
            room=room,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).filter(
            # Overlap: existing.start < new.end AND existing.end > new.start
            Q(start_datetime__lt=end_datetime) & Q(end_datetime__gt=start_datetime),
        )
        if exclude_booking_id:
            qs = qs.exclude(pk=exclude_booking_id)
        return qs

    @staticmethod
    def book_room(room, start_datetime, end_datetime, booked_by=None, event=None, notes=''):
        """Create a booking after verifying no conflicts. Returns (booking, error_msg)."""
        if not FacilityService.check_availability(room, start_datetime, end_datetime):
            return None, _('Cette salle est déjà réservée pour ce créneau.')

        if end_datetime <= start_datetime:
            return None, _('La date de fin doit être après la date de début.')

        booking = RoomBooking.objects.create(
            room=room,
            event=event,
            booked_by=booked_by,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status=BookingStatus.PENDING,
            notes=notes,
        )
        return booking, None

    @staticmethod
    def approve_booking(booking):
        """Approve a pending booking if no conflicts arose since creation."""
        if booking.status != BookingStatus.PENDING:
            return False, _('Seules les réservations en attente peuvent être approuvées.')

        if not FacilityService.check_availability(
            booking.room, booking.start_datetime, booking.end_datetime,
            exclude_booking_id=booking.pk,
        ):
            return False, _('Un conflit de réservation existe.')

        booking.status = BookingStatus.CONFIRMED
        booking.save(update_fields=['status', 'updated_at'])
        return True, None

    @staticmethod
    def reject_booking(booking):
        """Reject a pending booking."""
        booking.status = BookingStatus.REJECTED
        booking.save(update_fields=['status', 'updated_at'])
        return True, None

    @staticmethod
    def cancel_booking(booking):
        """Cancel a booking."""
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        return True, None

    @staticmethod
    def get_room_bookings(room, start_date=None, end_date=None):
        """Return active bookings for a room, optionally filtered by date range."""
        qs = RoomBooking.objects.filter(
            room=room,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).order_by('start_datetime')
        if start_date:
            qs = qs.filter(start_datetime__date__gte=start_date)
        if end_date:
            qs = qs.filter(end_datetime__date__lte=end_date)
        return qs
