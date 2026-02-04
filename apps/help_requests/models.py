"""Help Requests models."""
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel
from apps.core.constants import HelpRequestUrgency, HelpRequestStatus


class HelpRequestCategory(BaseModel):
    """Category for help requests (Prayer, Financial, Material, Pastoral)."""
    name = models.CharField(max_length=100)
    name_fr = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI")
    # Note: is_active is inherited from BaseModel, no need to redeclare it
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Help Request Category'
        verbose_name_plural = 'Help Request Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class HelpRequest(BaseModel):
    """Help request ticket from a member."""
    request_number = models.CharField(max_length=20, unique=True, editable=False)
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='help_requests'
    )
    category = models.ForeignKey(
        HelpRequestCategory,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    urgency = models.CharField(
        max_length=20,
        choices=HelpRequestUrgency.choices,
        default=HelpRequestUrgency.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=HelpRequestStatus.choices,
        default=HelpRequestStatus.NEW
    )
    assigned_to = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_help_requests'
    )
    is_confidential = models.BooleanField(
        default=False,
        help_text="Only visible to pastors and admins"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Help Request'
        verbose_name_plural = 'Help Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self._generate_request_number()
        super().save(*args, **kwargs)

    def _generate_request_number(self):
        """Generate unique request number: HR-YYYYMM-XXXX."""
        from apps.core.utils import generate_request_number
        return generate_request_number()

    def mark_resolved(self, notes=''):
        """Mark the request as resolved."""
        self.status = HelpRequestStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])

    def assign_to(self, member):
        """Assign request to a staff member."""
        self.assigned_to = member
        if self.status == HelpRequestStatus.NEW:
            self.status = HelpRequestStatus.IN_PROGRESS
        self.save(update_fields=['assigned_to', 'status', 'updated_at'])


class HelpRequestComment(BaseModel):
    """Comment on a help request."""
    help_request = models.ForeignKey(
        HelpRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='help_request_comments'
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal staff-only note"
    )

    class Meta:
        verbose_name = 'Help Request Comment'
        verbose_name_plural = 'Help Request Comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.help_request.request_number} by {self.author}"
