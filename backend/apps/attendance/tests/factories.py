"""Test factories for attendance app."""
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from apps.members.tests.factories import MemberFactory
from apps.attendance.models import MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert
from apps.core.constants import AttendanceSessionType, CheckInMethod


class MemberQRCodeFactory(DjangoModelFactory):
    class Meta:
        model = MemberQRCode

    member = factory.SubFactory(MemberFactory)
    # code and expires_at are set in model's save()


class AttendanceSessionFactory(DjangoModelFactory):
    class Meta:
        model = AttendanceSession

    name = factory.Sequence(lambda n: f'Session {n}')
    session_type = AttendanceSessionType.WORSHIP
    date = factory.LazyFunction(lambda: timezone.now().date())
    is_open = True
    opened_by = factory.SubFactory(MemberFactory)


class AttendanceRecordFactory(DjangoModelFactory):
    class Meta:
        model = AttendanceRecord

    session = factory.SubFactory(AttendanceSessionFactory)
    member = factory.SubFactory(MemberFactory)
    method = CheckInMethod.QR_SCAN


class AbsenceAlertFactory(DjangoModelFactory):
    class Meta:
        model = AbsenceAlert

    member = factory.SubFactory(MemberFactory)
    consecutive_absences = 3
