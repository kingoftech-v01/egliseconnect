from dz import dz_array


def dz_static(request):
    context = {"dz_array": dz_array}

    # Add unread notification count for authenticated users
    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'member_profile'):
            from apps.communication.models import Notification
            context['unread_notification_count'] = Notification.objects.filter(
                member=request.user.member_profile,
                is_read=False,
            ).count()

    return context
