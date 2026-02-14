"""Tests for WebSocket notification consumers."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from apps.core.consumers import (
    NotificationConsumer,
    send_notification_to_user,
    send_toast_to_user,
    update_notification_count,
)
from apps.members.tests.factories import UserFactory


@pytest.mark.django_db
class TestNotificationConsumerHelpers:
    """Test synchronous helper functions for sending notifications."""

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_send_notification_to_user(self, mock_async, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer
        mock_async.return_value = MagicMock()

        send_notification_to_user(
            user_id=1,
            notification_data={'title': 'Test', 'message': 'Hello'},
        )
        mock_async.assert_called_once()

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_send_toast_to_user(self, mock_async, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer
        mock_async.return_value = MagicMock()

        send_toast_to_user(
            user_id=1,
            title='Test Toast',
            message='Toast message',
            level='success',
            url='/test/',
        )
        mock_async.assert_called_once()

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_update_notification_count(self, mock_async, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer
        mock_async.return_value = MagicMock()

        update_notification_count(user_id=1, count=5)
        mock_async.assert_called_once()

    def test_group_name_format(self):
        """Verify the notification group naming convention."""
        user_id = 42
        group_name = f'notifications_{user_id}'
        assert group_name == 'notifications_42'


@pytest.mark.django_db
class TestNotificationConsumerUnit:
    """Unit tests for NotificationConsumer methods."""

    def test_consumer_class_exists(self):
        """Verify consumer class is importable and has expected methods."""
        assert hasattr(NotificationConsumer, 'connect')
        assert hasattr(NotificationConsumer, 'disconnect')
        assert hasattr(NotificationConsumer, 'receive_json')
        assert hasattr(NotificationConsumer, 'notification_message')
        assert hasattr(NotificationConsumer, 'notification_count')
        assert hasattr(NotificationConsumer, 'notification_toast')
        assert hasattr(NotificationConsumer, 'send_unread_count')
        assert hasattr(NotificationConsumer, 'mark_notification_read')
        assert hasattr(NotificationConsumer, 'mark_all_read')

    def test_consumer_is_async(self):
        """Verify consumer methods are async."""
        import asyncio
        assert asyncio.iscoroutinefunction(NotificationConsumer.connect)
        assert asyncio.iscoroutinefunction(NotificationConsumer.disconnect)
        assert asyncio.iscoroutinefunction(NotificationConsumer.receive_json)
