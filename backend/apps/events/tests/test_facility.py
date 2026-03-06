"""Tests for facility/room booking service and views."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.core.constants import BookingStatus
from apps.events.models import Room, RoomBooking
from apps.events.services_facility import FacilityService
from apps.events.tests.factories import RoomFactory, RoomBookingFactory, EventFactory
from apps.members.tests.factories import MemberFactory, MemberWithUserFactory


pytestmark = pytest.mark.django_db


# ── FacilityService Tests ──

class TestFacilityServiceCheckAvailability:
    def test_room_available_when_no_bookings(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        assert FacilityService.check_availability(room, start, end) is True

    def test_room_unavailable_with_overlapping_booking(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        RoomBookingFactory(room=room, start_datetime=start, end_datetime=end, status=BookingStatus.CONFIRMED)
        assert FacilityService.check_availability(room, start, end) is False

    def test_room_available_with_cancelled_booking(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        RoomBookingFactory(room=room, start_datetime=start, end_datetime=end, status=BookingStatus.CANCELLED)
        assert FacilityService.check_availability(room, start, end) is True

    def test_room_available_with_non_overlapping_booking(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        other_start = end + timedelta(hours=1)
        other_end = other_start + timedelta(hours=2)
        RoomBookingFactory(room=room, start_datetime=other_start, end_datetime=other_end, status=BookingStatus.CONFIRMED)
        assert FacilityService.check_availability(room, start, end) is True

    def test_exclude_booking_id(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        booking = RoomBookingFactory(room=room, start_datetime=start, end_datetime=end, status=BookingStatus.CONFIRMED)
        assert FacilityService.check_availability(room, start, end, exclude_booking_id=booking.pk) is True


class TestFacilityServiceDetectConflicts:
    def test_detects_partial_overlap(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        RoomBookingFactory(
            room=room,
            start_datetime=start + timedelta(hours=1),
            end_datetime=end + timedelta(hours=1),
            status=BookingStatus.PENDING,
        )
        conflicts = FacilityService.detect_conflicts(room, start, end)
        assert conflicts.count() == 1

    def test_no_conflicts_for_different_rooms(self):
        room1 = RoomFactory()
        room2 = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        RoomBookingFactory(room=room1, start_datetime=start, end_datetime=end, status=BookingStatus.CONFIRMED)
        conflicts = FacilityService.detect_conflicts(room2, start, end)
        assert conflicts.count() == 0


class TestFacilityServiceBookRoom:
    def test_successful_booking(self):
        room = RoomFactory()
        member = MemberFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        booking, error = FacilityService.book_room(room, start, end, booked_by=member)
        assert booking is not None
        assert error is None
        assert booking.status == BookingStatus.PENDING

    def test_booking_with_event(self):
        room = RoomFactory()
        event = EventFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        booking, error = FacilityService.book_room(room, start, end, event=event)
        assert booking is not None
        assert booking.event == event

    def test_booking_conflict_returns_error(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        RoomBookingFactory(room=room, start_datetime=start, end_datetime=end, status=BookingStatus.CONFIRMED)
        booking, error = FacilityService.book_room(room, start, end)
        assert booking is None
        assert error is not None

    def test_booking_end_before_start_returns_error(self):
        room = RoomFactory()
        start = timezone.now() + timedelta(days=1)
        end = start - timedelta(hours=1)
        booking, error = FacilityService.book_room(room, start, end)
        assert booking is None
        assert error is not None


class TestFacilityServiceApproveReject:
    def test_approve_pending_booking(self):
        booking = RoomBookingFactory(status=BookingStatus.PENDING)
        ok, err = FacilityService.approve_booking(booking)
        assert ok is True
        booking.refresh_from_db()
        assert booking.status == BookingStatus.CONFIRMED

    def test_cannot_approve_already_confirmed(self):
        booking = RoomBookingFactory(status=BookingStatus.CONFIRMED)
        ok, err = FacilityService.approve_booking(booking)
        assert ok is False

    def test_reject_booking(self):
        booking = RoomBookingFactory(status=BookingStatus.PENDING)
        ok, err = FacilityService.reject_booking(booking)
        assert ok is True
        booking.refresh_from_db()
        assert booking.status == BookingStatus.REJECTED

    def test_cancel_booking(self):
        booking = RoomBookingFactory(status=BookingStatus.CONFIRMED)
        ok, err = FacilityService.cancel_booking(booking)
        assert ok is True
        booking.refresh_from_db()
        assert booking.status == BookingStatus.CANCELLED


class TestFacilityServiceGetRoomBookings:
    def test_returns_active_bookings(self):
        room = RoomFactory()
        RoomBookingFactory(room=room, status=BookingStatus.PENDING)
        RoomBookingFactory(room=room, status=BookingStatus.CONFIRMED)
        RoomBookingFactory(room=room, status=BookingStatus.CANCELLED)
        bookings = FacilityService.get_room_bookings(room)
        assert bookings.count() == 2

    def test_filter_by_date_range(self):
        room = RoomFactory()
        today = timezone.now().date()
        RoomBookingFactory(
            room=room,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=2),
            status=BookingStatus.CONFIRMED,
        )
        RoomBookingFactory(
            room=room,
            start_datetime=timezone.now() + timedelta(days=10),
            end_datetime=timezone.now() + timedelta(days=10, hours=2),
            status=BookingStatus.CONFIRMED,
        )
        bookings = FacilityService.get_room_bookings(room, start_date=today, end_date=today + timedelta(days=5))
        assert bookings.count() == 1


# ── Room Model Tests ──

class TestRoomModel:
    def test_str(self):
        room = RoomFactory(name='Sanctuaire')
        assert str(room) == 'Sanctuaire'

    def test_default_amenities(self):
        room = Room.objects.create(name='Test', capacity=10)
        assert isinstance(room.amenities_json, list)


class TestRoomBookingModel:
    def test_str(self):
        booking = RoomBookingFactory()
        assert booking.room.name in str(booking)

    def test_default_status_is_pending(self):
        booking = RoomBookingFactory()
        assert booking.status == BookingStatus.PENDING
