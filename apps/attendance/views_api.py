"""API views for attendance."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import Roles, CheckInMethod
from apps.core.permissions import IsPastorOrAdmin, IsMember
from .models import (
    MemberQRCode, AttendanceSession, AttendanceRecord, AbsenceAlert,
    ChildCheckIn, KioskConfig, NFCTag, AttendanceStreak,
    GeoFence, VisitorInfo,
)
from .serializers import (
    MemberQRCodeSerializer,
    AttendanceSessionSerializer,
    AttendanceRecordSerializer,
    AbsenceAlertSerializer,
    CheckInSerializer,
    ChildCheckInSerializer,
    ChildCheckOutSerializer,
    KioskConfigSerializer,
    NFCTagSerializer,
    NFCCheckinSerializer,
    AttendanceStreakSerializer,
    GeoFenceSerializer,
    GeoCheckinSerializer,
    VisitorInfoSerializer,
    MemberSearchSerializer,
    CheckOutSerializer,
    FamilyCheckinSerializer,
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

        # Update streak
        from .views_frontend import _update_member_streak
        _update_member_streak(qr.member, session.date)

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

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an absence alert."""
        from django.utils import timezone
        alert = self.get_object()
        if alert.acknowledged_by:
            return Response(
                {'warning': 'Alerte déjà reconnue'},
                status=status.HTTP_400_BAD_REQUEST
            )
        member = getattr(request.user, 'member_profile', None)
        if not member:
            return Response(
                {'error': 'No profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        alert.acknowledged_by = member
        alert.acknowledged_at = timezone.now()
        notes = request.data.get('notes', '')
        if notes:
            alert.notes = notes
        alert.save()
        return Response(AbsenceAlertSerializer(alert).data)


class ChildCheckInViewSet(viewsets.ModelViewSet):
    """CRUD for child check-ins."""
    serializer_class = ChildCheckInSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = ChildCheckIn.objects.filter(is_active=True)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Check out a child using security code."""
        serializer = ChildCheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        security_code = serializer.validated_data['security_code']

        try:
            checkin = ChildCheckIn.objects.select_related('child').get(
                security_code=security_code,
                check_out_time__isnull=True,
            )
        except ChildCheckIn.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou enfant déjà retiré'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        member = getattr(request.user, 'member_profile', None)
        checkin.check_out_time = timezone.now()
        checkin.checked_out_by = member
        checkin.save()

        return Response({
            'success': True,
            'child_name': checkin.child.full_name,
        })


class NFCTagViewSet(viewsets.ModelViewSet):
    """CRUD for NFC tags."""
    serializer_class = NFCTagSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = NFCTag.objects.filter(is_active=True)

    @action(detail=False, methods=['post'])
    def checkin(self, request):
        """Process NFC-based check-in."""
        serializer = NFCCheckinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag_id = serializer.validated_data['tag_id']
        session_id = serializer.validated_data['session_id']

        try:
            nfc = NFCTag.objects.select_related('member').get(
                tag_id=tag_id, is_active=True
            )
        except NFCTag.DoesNotExist:
            return Response(
                {'error': 'Tag NFC non reconnu'},
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
            member=nfc.member,
            defaults={
                'checked_in_by': scanner,
                'method': CheckInMethod.NFC,
            }
        )

        if not created:
            return Response({
                'warning': 'Déjà enregistré',
                'member_name': nfc.member.full_name,
            })

        from .views_frontend import _update_member_streak
        _update_member_streak(nfc.member, session.date)

        return Response({
            'success': True,
            'member_name': nfc.member.full_name,
            'member_photo': nfc.member.photo.url if nfc.member.photo else None,
        })


class GeoFenceViewSet(viewsets.ModelViewSet):
    """CRUD for geo-fences."""
    serializer_class = GeoFenceSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = GeoFence.objects.filter(is_active=True)

    @action(detail=False, methods=['post'])
    def checkin(self, request):
        """GPS-based check-in."""
        serializer = GeoCheckinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['latitude']
        lng = serializer.validated_data['longitude']
        session_id = serializer.validated_data['session_id']

        # Find matching fence
        fences = GeoFence.objects.filter(is_active=True)
        within = False
        for fence in fences:
            if fence.is_within_fence(lat, lng):
                within = True
                break

        if not within:
            return Response(
                {'error': 'Hors de la zone de check-in'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = AttendanceSession.objects.get(pk=session_id, is_open=True)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': 'Session invalide ou fermée'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = getattr(request.user, 'member_profile', None)
        if not member:
            return Response(
                {'error': 'No profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            member=member,
            defaults={'method': CheckInMethod.GEO}
        )

        if not created:
            return Response({'warning': 'Déjà enregistré'})

        from .views_frontend import _update_member_streak
        _update_member_streak(member, session.date)

        return Response({
            'success': True,
            'member_name': member.full_name,
        })


class VisitorInfoViewSet(viewsets.ModelViewSet):
    """CRUD for visitor information."""
    serializer_class = VisitorInfoSerializer
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]
    queryset = VisitorInfo.objects.filter(is_active=True)

    @action(detail=True, methods=['post'])
    def complete_followup(self, request, pk=None):
        """Mark follow-up as completed."""
        from django.utils import timezone
        visitor = self.get_object()
        visitor.follow_up_completed = True
        visitor.follow_up_completed_at = timezone.now()
        visitor.save()
        return Response(VisitorInfoSerializer(visitor).data)


class CheckOutViewSet(viewsets.ViewSet):
    """Process member check-outs via API."""
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        record_id = serializer.validated_data['record_id']

        try:
            record = AttendanceRecord.objects.select_related('member').get(pk=record_id)
        except AttendanceRecord.DoesNotExist:
            return Response(
                {'error': 'Enregistrement introuvable'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if record.checked_out_at:
            return Response({'warning': 'Déjà sorti'})

        from django.utils import timezone
        record.checked_out_at = timezone.now()
        record.save()

        return Response({
            'success': True,
            'member_name': record.member.full_name,
            'duration_minutes': record.duration_minutes,
        })


class FamilyCheckInViewSet(viewsets.ViewSet):
    """Family check-in via API."""
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = FamilyCheckinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        family_id = serializer.validated_data['family_id']
        session_id = serializer.validated_data['session_id']
        member_ids = serializer.validated_data.get('member_ids', [])

        from apps.members.models import Family, Member

        try:
            family = Family.objects.get(pk=family_id)
        except Family.DoesNotExist:
            return Response(
                {'error': 'Famille introuvable'},
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

        if member_ids:
            members = Member.objects.filter(pk__in=member_ids, family=family, is_active=True)
        else:
            members = Member.objects.filter(family=family, is_active=True)

        checked_in = []
        already = []

        for member in members:
            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                member=member,
                defaults={
                    'checked_in_by': scanner,
                    'method': CheckInMethod.KIOSK,
                }
            )
            if created:
                from .views_frontend import _update_member_streak
                _update_member_streak(member, session.date)
                checked_in.append(member.full_name)
            else:
                already.append(member.full_name)

        return Response({
            'success': True,
            'checked_in': checked_in,
            'already_checked': already,
        })


class AttendanceAnalyticsViewSet(viewsets.ViewSet):
    """Analytics endpoints for attendance data."""
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get attendance trends."""
        from .services import AttendanceAnalyticsService

        period = request.query_params.get('period', 'weekly')
        weeks = int(request.query_params.get('weeks', 12))

        trends = AttendanceAnalyticsService.get_attendance_trends(period, weeks)
        return Response({
            'labels': [t['period'].strftime('%Y-%m-%d') for t in trends],
            'data': [t['count'] for t in trends],
        })

    @action(detail=False, methods=['get'])
    def average_by_type(self, request):
        """Get average attendance per session type."""
        from .services import AttendanceAnalyticsService
        return Response(AttendanceAnalyticsService.get_average_attendance_by_type())

    @action(detail=False, methods=['get'])
    def growth(self, request):
        """Get growth indicators."""
        from .services import AttendanceAnalyticsService
        return Response(AttendanceAnalyticsService.get_growth_indicators())

    @action(detail=False, methods=['get'])
    def member_rate(self, request):
        """Get attendance rate for a specific member."""
        from .services import AttendanceAnalyticsService
        from apps.members.models import Member

        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {'error': 'member_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response(
                {'error': 'Membre introuvable'},
                status=status.HTTP_400_BAD_REQUEST
            )

        days = int(request.query_params.get('days', 90))
        return Response(AttendanceAnalyticsService.get_member_attendance_rate(member, days))

    @action(detail=False, methods=['get'])
    def engagement_score(self, request):
        """Get engagement score for a specific member."""
        from .services import EngagementScoringService
        from apps.members.models import Member

        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {'error': 'member_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response(
                {'error': 'Membre introuvable'},
                status=status.HTTP_400_BAD_REQUEST
            )

        score = EngagementScoringService.calculate_engagement_score(member)
        streak = EngagementScoringService.get_attendance_streak(member)
        consistency = EngagementScoringService.calculate_consistency_score(member)

        return Response({
            'score': score,
            'consistency': consistency,
            'current_streak': streak['current_streak'],
            'longest_streak': streak['longest_streak'],
        })

    @action(detail=False, methods=['get'])
    def prediction(self, request):
        """Get attendance prediction for a session type."""
        from .services import AttendancePredictionService

        session_type = request.query_params.get('session_type', 'worship')
        prediction = AttendancePredictionService.predict_attendance(session_type)
        recommendations = AttendancePredictionService.get_resource_recommendations(session_type)

        return Response({
            **prediction,
            'recommendations': recommendations['recommendations'],
        })
