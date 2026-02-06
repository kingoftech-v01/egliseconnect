"""REST API endpoints for donation management."""
from decimal import Decimal

from django.db.models import Sum, Avg, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import (
    IsMember,
    IsTreasurer,
    IsPastorOrAdmin,
    IsFinanceStaff,
    IsOwnerOrStaff,
)
from apps.core.constants import Roles, PaymentMethod
from apps.core.utils import generate_receipt_number

from .models import Donation, DonationCampaign, TaxReceipt
from .serializers import (
    DonationSerializer,
    DonationListSerializer,
    DonationCreateSerializer,
    PhysicalDonationCreateSerializer,
    MemberDonationHistorySerializer,
    DonationCampaignSerializer,
    DonationCampaignListSerializer,
    TaxReceiptSerializer,
    TaxReceiptListSerializer,
    DonationSummarySerializer,
)


class DonationViewSet(viewsets.ModelViewSet):
    """CRUD operations for donations with role-based access."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['donation_type', 'payment_method', 'campaign', 'date']
    search_fields = ['donation_number', 'member__first_name', 'member__last_name']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        """Finance staff see all donations; members see only their own."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Donation.objects.all().select_related('member', 'campaign')

        if hasattr(user, 'member_profile'):
            member = user.member_profile

            if member.role in [Roles.TREASURER, Roles.PASTOR, Roles.ADMIN]:
                return Donation.objects.all().select_related('member', 'campaign')

            return Donation.objects.filter(member=member).select_related('campaign')

        return Donation.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return DonationListSerializer
        if self.action == 'create':
            return DonationCreateSerializer
        if self.action == 'record_physical':
            return PhysicalDonationCreateSerializer
        if self.action == 'my_history':
            return MemberDonationHistorySerializer
        return DonationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsMember()]
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsFinanceStaff()]
        if self.action == 'record_physical':
            return [IsTreasurer()]
        if self.action == 'summary':
            return [IsFinanceStaff()]
        if self.action == 'my_history':
            return [IsMember()]
        return [IsMember()]

    def perform_create(self, serializer):
        """Set member from request user and mark as online payment."""
        if not hasattr(self.request.user, 'member_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': 'Aucun profil membre trouvé'})
        member = self.request.user.member_profile
        serializer.save(
            member=member,
            payment_method=PaymentMethod.ONLINE
        )

    @action(detail=False, methods=['get'], url_path='my-history')
    def my_history(self, request):
        """Get current user's donation history, optionally filtered by year."""
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile
        queryset = Donation.objects.filter(member=member)

        year = request.query_params.get('year')
        if year:
            try:
                queryset = queryset.filter(date__year=int(year))
            except (ValueError, TypeError):
                pass

        queryset = queryset.order_by('-date')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MemberDonationHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MemberDonationHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='record-physical')
    def record_physical(self, request):
        """Record a physical donation (cash, check, etc.) - treasurer only."""
        serializer = PhysicalDonationCreateSerializer(data=request.data)
        if serializer.is_valid():
            donation = serializer.save(recorded_by=request.user.member_profile)
            return Response(
                DonationSerializer(donation).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get donation statistics for a period (month or year)."""
        period = request.query_params.get('period', 'month')
        try:
            year = int(request.query_params.get('year', timezone.now().year))
        except (ValueError, TypeError):
            year = timezone.now().year
        month = request.query_params.get('month')
        if month:
            try:
                month = int(month)
            except (ValueError, TypeError):
                month = None

        queryset = Donation.objects.filter(is_active=True)

        if period == 'month' and month:
            queryset = queryset.filter(date__year=year, date__month=month)
            period_label = f'{month}/{year}'
        elif period == 'year':
            queryset = queryset.filter(date__year=year)
            period_label = str(year)
        else:
            today = timezone.now()
            queryset = queryset.filter(
                date__year=today.year,
                date__month=today.month
            )
            period_label = f'{today.month}/{today.year}'

        stats = queryset.aggregate(
            total_amount=Sum('amount'),
            donation_count=Count('id'),
            average_donation=Avg('amount'),
        )

        by_type = dict(
            queryset.values('donation_type')
            .annotate(total=Sum('amount'))
            .values_list('donation_type', 'total')
        )

        by_method = dict(
            queryset.values('payment_method')
            .annotate(total=Sum('amount'))
            .values_list('payment_method', 'total')
        )

        data = {
            'period': period_label,
            'total_amount': stats['total_amount'] or Decimal('0.00'),
            'donation_count': stats['donation_count'] or 0,
            'average_donation': stats['average_donation'] or Decimal('0.00'),
            'by_type': by_type,
            'by_method': by_method,
        }

        serializer = DonationSummarySerializer(data)
        return Response(serializer.data)


class DonationCampaignViewSet(viewsets.ModelViewSet):
    """CRUD operations for fundraising campaigns."""

    queryset = DonationCampaign.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'goal_amount']
    ordering = ['-start_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return DonationCampaignListSerializer
        return DonationCampaignSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsMember()]
        return [IsPastorOrAdmin()]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active campaigns."""
        today = timezone.now().date()
        campaigns = self.queryset.filter(
            is_active=True,
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        )

        serializer = DonationCampaignListSerializer(campaigns, many=True)
        return Response(serializer.data)


class TaxReceiptViewSet(viewsets.ModelViewSet):
    """Tax receipt management with generation capabilities."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['year', 'email_sent']
    search_fields = ['receipt_number', 'member__first_name', 'member__last_name']
    ordering_fields = ['year', 'generated_at', 'total_amount']
    ordering = ['-year', '-generated_at']

    def get_queryset(self):
        """Finance staff see all receipts; members see only their own."""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return TaxReceipt.objects.all().select_related('member')

        if hasattr(user, 'member_profile'):
            member = user.member_profile

            if member.role in [Roles.TREASURER, Roles.ADMIN]:
                return TaxReceipt.objects.all().select_related('member')

            return TaxReceipt.objects.filter(member=member)

        return TaxReceipt.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return TaxReceiptListSerializer
        return TaxReceiptSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_receipts']:
            return [IsMember()]
        return [IsTreasurer()]

    @action(detail=False, methods=['get'], url_path='my-receipts')
    def my_receipts(self, request):
        """Get current user's tax receipts."""
        if not hasattr(request.user, 'member_profile'):
            return Response(
                {'error': 'Aucun profil membre trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        member = request.user.member_profile
        receipts = TaxReceipt.objects.filter(member=member).order_by('-year')

        serializer = TaxReceiptListSerializer(receipts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='generate/(?P<year>[0-9]{4})')
    def generate(self, request, year=None):
        """Generate tax receipts for a year, for one member or all members with donations."""
        year = int(year)
        member_id = request.query_params.get('member')

        if member_id:
            from apps.members.models import Member
            try:
                member = Member.objects.get(pk=member_id)
            except Member.DoesNotExist:
                return Response(
                    {'error': 'Membre non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )

            receipt = self._generate_receipt_for_member(member, year, request.user)
            if receipt:
                return Response(
                    TaxReceiptSerializer(receipt).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Aucun don trouvé pour cette année'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.members.models import Member

        members_with_donations = Member.objects.filter(
            donations__date__year=year,
            donations__is_active=True
        ).distinct()

        generated = []
        for member in members_with_donations:
            receipt = self._generate_receipt_for_member(member, year, request.user)
            if receipt:
                generated.append(receipt)

        return Response({
            'generated_count': len(generated),
            'year': year,
        })

    def _generate_receipt_for_member(self, member, year, user):
        """Generate a tax receipt for a member. Returns existing receipt if already generated."""
        existing = TaxReceipt.objects.filter(member=member, year=year).first()
        if existing:
            return existing

        total = Donation.objects.filter(
            member=member,
            date__year=year,
            is_active=True
        ).aggregate(total=Sum('amount'))['total']

        if not total or total <= 0:
            return None

        receipt = TaxReceipt.objects.create(
            receipt_number=generate_receipt_number(year),
            member=member,
            year=year,
            total_amount=total,
            generated_by=user.member_profile if hasattr(user, 'member_profile') else None,
        )

        return receipt
