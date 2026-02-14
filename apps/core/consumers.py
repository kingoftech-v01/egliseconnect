"""WebSocket consumers for real-time notifications."""
import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time in-app notifications.

    Clients connect to ws://<host>/ws/notifications/ and receive:
    - New notification alerts
    - Unread count updates
    - Toast messages for high-priority events
    """

    async def connect(self):
        """Accept connection if user is authenticated."""
        self.user = self.scope.get('user')

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Each user gets their own notification group
        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        # Send initial unread count
        await self.send_unread_count()

    async def disconnect(self, close_code):
        """Remove from notification group on disconnect."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content):
        """Handle messages from client (e.g., mark as read)."""
        action = content.get('action')

        if action == 'mark_read':
            notification_id = content.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
                await self.send_unread_count()

        elif action == 'mark_all_read':
            await self.mark_all_read()
            await self.send_unread_count()

        elif action == 'get_count':
            await self.send_unread_count()

    async def notification_message(self, event):
        """Handle notification broadcast from channel layer."""
        await self.send_json({
            'type': 'notification',
            'notification': event.get('notification', {}),
        })

    async def notification_count(self, event):
        """Handle unread count update broadcast."""
        await self.send_json({
            'type': 'count_update',
            'count': event.get('count', 0),
        })

    async def notification_toast(self, event):
        """Handle toast/popup notification for high-priority alerts."""
        await self.send_json({
            'type': 'toast',
            'title': event.get('title', ''),
            'message': event.get('message', ''),
            'level': event.get('level', 'info'),
            'url': event.get('url', ''),
        })

    async def send_unread_count(self):
        """Query and send current unread notification count."""
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def get_count():
            if not hasattr(self.user, 'member_profile'):
                return 0
            from apps.communication.models import Notification
            return Notification.objects.filter(
                member=self.user.member_profile,
                is_read=False,
            ).count()

        count = await get_count()
        await self.send_json({
            'type': 'count_update',
            'count': count,
        })

    async def mark_notification_read(self, notification_id):
        """Mark a single notification as read."""
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def do_mark_read(nid):
            if not hasattr(self.user, 'member_profile'):
                return
            from apps.communication.models import Notification
            Notification.objects.filter(
                pk=nid,
                member=self.user.member_profile,
            ).update(is_read=True)

        await do_mark_read(notification_id)

    async def mark_all_read(self):
        """Mark all notifications as read."""
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def do_mark_all_read():
            if not hasattr(self.user, 'member_profile'):
                return
            from apps.communication.models import Notification
            Notification.objects.filter(
                member=self.user.member_profile,
                is_read=False,
            ).update(is_read=True)

        await do_mark_all_read()


def send_notification_to_user(user_id, notification_data):
    """
    Utility function to send a notification to a specific user via WebSocket.
    Call from synchronous code (views, signals, Celery tasks).

    Args:
        user_id: The user's ID
        notification_data: dict with title, message, url, level, etc.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'notification': notification_data,
        }
    )


def send_toast_to_user(user_id, title, message, level='info', url=''):
    """
    Send a toast notification to a specific user via WebSocket.

    Args:
        user_id: The user's ID
        title: Toast title
        message: Toast message
        level: 'info', 'success', 'warning', 'error'
        url: Optional URL to navigate to on click
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_toast',
            'title': title,
            'message': message,
            'level': level,
            'url': url,
        }
    )


def update_notification_count(user_id, count):
    """Send updated unread count to user's WebSocket."""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_count',
            'count': count,
        }
    )
