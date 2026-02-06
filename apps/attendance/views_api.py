"""API views for attendance."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import Roles, CheckInMethod
from apps.core.permissions import IsPastorOrAdmin
from .models import MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert
from .serializers import (
    MemberQRCodeSerializer,
    AttendanceSessionSerializer,
    AttendanceRecordSerializer,
    AbsenceAlertSerializer,
    CheckInSerializer,
)


class MemberQRCodeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemberQRCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'member_profile'):
            return MemberQRCode.objects.filter(member=user.member_profile)
        return MemberQRCode.objects.none()

    @action(detail=False, methods=['post'])
    def regenerate(self, request):
        if not hasattr(request.user, 'member_profile'):
            return Response({'error': 'No profile'}, status=status.HTTP_400_BAD_REQUEST)
        qr, _ = MemberQRCode.objects.get_or_create(member=request.user.member_profile)
        qr.regenerate()
        return Response(MemberQRCodeSerializer(qr).data)


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = AttendanceSession.objects.filter(is_active=True)
    filterset_fields = ['session_type', 'date', 'is_open']


class CheckInViewSet(viewsets.ViewSet):
    """Process QR code check-ins via API."""
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qr_code = serializer.validated_data['qr_code']
        session_id = serializer.validated_data['session_id']

        # Validate QR
        try:
            qr = MemberQRCode.objects.select_related('member').get(code=qr_code)
        except MemberQRCode.DoesNotExist:
            return Response(
                {'error': 'Code QR invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not qr.is_valid:
            return Response(
                {'error': 'Code QR expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = AttendanceSession.objects.get(pk=session_id, is_open=True)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': 'Session invalide ou fermée'},
                status=status.HTTP_400_BAD_REQUEST
            )

        scanner = getattr(request.user, 'member_profile', None)

        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            member=qr.member,
            defaults={
                'checked_in_by': scanner,
                'method': CheckInMethod.QR_SCAN,
            }
        )

        if not created:
            return Response({
                'warning': 'Déjà enregistré',
                'member_name': qr.member.full_name,
            })

        # Mark lesson attendance if applicable
        if session.scheduled_lesson:
            from apps.onboarding.services import OnboardingService
            OnboardingService.mark_lesson_attended(session.scheduled_lesson, scanner)

        return Response({
            'success': True,
            'member_name': qr.member.full_name,
            'member_photo': qr.member.photo.url if qr.member.photo else None,
        })


class AbsenceAlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AbsenceAlertSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = AbsenceAlert.objects.filter(is_active=True)
    filterset_fields = ['alert_sent']
