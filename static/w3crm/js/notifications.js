/**
 * EgliseConnect - Real-time Notifications via WebSocket
 *
 * Connects to the Django Channels WebSocket endpoint for live notification updates.
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Unread badge count updates
 * - Toast notifications for high-priority alerts
 * - Mark as read functionality
 */

(function() {
    'use strict';

    const EC_NOTIFICATIONS = {
        socket: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 10,
        reconnectDelay: 1000,
        isConnected: false,

        /**
         * Initialize WebSocket connection for notifications.
         */
        init: function() {
            if (!document.querySelector('[data-notifications-enabled]')) {
                return;
            }
            this.connect();
        },

        /**
         * Create WebSocket connection.
         */
        connect: function() {
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var wsUrl = protocol + window.location.host + '/ws/notifications/';

            try {
                this.socket = new WebSocket(wsUrl);
            } catch (e) {
                console.warn('WebSocket connection failed:', e);
                return;
            }

            this.socket.onopen = this.onOpen.bind(this);
            this.socket.onmessage = this.onMessage.bind(this);
            this.socket.onclose = this.onClose.bind(this);
            this.socket.onerror = this.onError.bind(this);
        },

        /**
         * Handle connection open.
         */
        onOpen: function() {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
        },

        /**
         * Handle incoming WebSocket message.
         */
        onMessage: function(event) {
            var data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                return;
            }

            switch (data.type) {
                case 'count_update':
                    this.updateBadge(data.count);
                    break;
                case 'notification':
                    this.handleNotification(data.notification);
                    break;
                case 'toast':
                    this.showToast(data.title, data.message, data.level, data.url);
                    break;
            }
        },

        /**
         * Handle connection close with auto-reconnect.
         */
        onClose: function(event) {
            this.isConnected = false;

            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                var delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
                setTimeout(this.connect.bind(this), delay);
            }
        },

        /**
         * Handle WebSocket error.
         */
        onError: function(event) {
            console.warn('WebSocket error');
        },

        /**
         * Send JSON message to server.
         */
        send: function(data) {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(data));
            }
        },

        /**
         * Update notification badge count in header.
         */
        updateBadge: function(count) {
            var badges = document.querySelectorAll('.notification-badge-count');
            badges.forEach(function(badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = '';
                } else {
                    badge.style.display = 'none';
                }
            });
        },

        /**
         * Handle new notification.
         */
        handleNotification: function(notification) {
            // Update badge
            this.send({ action: 'get_count' });

            // Show toast for new notifications
            if (notification.title) {
                this.showToast(
                    notification.title,
                    notification.message || '',
                    notification.level || 'info',
                    notification.url || ''
                );
            }
        },

        /**
         * Show toast notification popup.
         */
        showToast: function(title, message, level, url) {
            var toastContainer = document.getElementById('notification-toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'notification-toast-container';
                toastContainer.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;max-width:350px;';
                document.body.appendChild(toastContainer);
            }

            var colorMap = {
                info: '#1a73e8',
                success: '#28a745',
                warning: '#ffc107',
                error: '#dc3545'
            };
            var borderColor = colorMap[level] || colorMap.info;

            var toast = document.createElement('div');
            toast.style.cssText = 'background:#fff;border-left:4px solid ' + borderColor +
                ';border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.15);padding:12px 16px;margin-bottom:8px;' +
                'animation:slideIn 0.3s ease;cursor:' + (url ? 'pointer' : 'default') + ';';
            toast.innerHTML = '<div style="font-weight:600;font-size:14px;margin-bottom:4px;">' +
                this.escapeHtml(title) + '</div>' +
                (message ? '<div style="font-size:13px;color:#666;">' + this.escapeHtml(message) + '</div>' : '');

            if (url) {
                toast.addEventListener('click', function() {
                    window.location.href = url;
                });
            }

            toastContainer.appendChild(toast);

            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(function() {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, 5000);
        },

        /**
         * Mark a notification as read.
         */
        markRead: function(notificationId) {
            this.send({
                action: 'mark_read',
                notification_id: notificationId,
            });
        },

        /**
         * Mark all notifications as read.
         */
        markAllRead: function() {
            this.send({ action: 'mark_all_read' });
        },

        /**
         * Request current unread count.
         */
        requestCount: function() {
            this.send({ action: 'get_count' });
        },

        /**
         * Escape HTML to prevent XSS.
         */
        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(text));
            return div.innerHTML;
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            EC_NOTIFICATIONS.init();
        });
    } else {
        EC_NOTIFICATIONS.init();
    }

    // Expose globally
    window.EC_NOTIFICATIONS = EC_NOTIFICATIONS;

})();
