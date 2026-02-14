/**
 * EgliseConnect - PWA Install Prompt
 *
 * Shows a banner prompting mobile users to install the app.
 * Remembers user's choice to avoid repeated prompts.
 */

(function() {
    'use strict';

    var PWA_INSTALL = {
        deferredPrompt: null,
        dismissedKey: 'egliseconnect_pwa_dismissed',

        init: function() {
            // Check if already dismissed
            var dismissed = localStorage.getItem(this.dismissedKey);
            if (dismissed) {
                var dismissedTime = parseInt(dismissed, 10);
                // Re-show after 7 days
                if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
                    return;
                }
            }

            // Don't show if already installed
            if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
                return;
            }
            if (window.navigator.standalone === true) {
                return;
            }

            window.addEventListener('beforeinstallprompt', this.onBeforeInstallPrompt.bind(this));
        },

        onBeforeInstallPrompt: function(e) {
            e.preventDefault();
            this.deferredPrompt = e;

            // Show install banner after a short delay
            var self = this;
            setTimeout(function() {
                self.showBanner();
            }, 3000);
        },

        showBanner: function() {
            var self = this;

            var banner = document.createElement('div');
            banner.id = 'pwa-install-banner';
            banner.style.cssText =
                'position:fixed;bottom:0;left:0;right:0;z-index:9999;' +
                'background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;' +
                'padding:16px 20px;display:flex;align-items:center;justify-content:space-between;' +
                'box-shadow:0 -2px 10px rgba(0,0,0,0.2);animation:slideUp 0.3s ease;';

            banner.innerHTML =
                '<div style="flex:1;">' +
                '<strong>Installer EgliseConnect</strong><br>' +
                '<small>Acc&eacute;dez rapidement depuis votre &eacute;cran d\'accueil</small>' +
                '</div>' +
                '<div style="display:flex;gap:8px;">' +
                '<button id="pwa-install-btn" style="background:#fff;color:#1a73e8;border:none;' +
                'padding:8px 16px;border-radius:4px;font-weight:600;cursor:pointer;">Installer</button>' +
                '<button id="pwa-dismiss-btn" style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,0.5);' +
                'padding:8px 12px;border-radius:4px;cursor:pointer;">Plus tard</button>' +
                '</div>';

            document.body.appendChild(banner);

            document.getElementById('pwa-install-btn').addEventListener('click', function() {
                self.install();
            });

            document.getElementById('pwa-dismiss-btn').addEventListener('click', function() {
                self.dismiss();
            });
        },

        install: function() {
            if (!this.deferredPrompt) return;

            this.deferredPrompt.prompt();
            this.deferredPrompt.userChoice.then(function(choiceResult) {
                // Remove banner regardless of choice
                var banner = document.getElementById('pwa-install-banner');
                if (banner) banner.remove();
            });

            this.deferredPrompt = null;
        },

        dismiss: function() {
            localStorage.setItem(this.dismissedKey, Date.now().toString());
            var banner = document.getElementById('pwa-install-banner');
            if (banner) {
                banner.style.opacity = '0';
                banner.style.transition = 'opacity 0.3s';
                setTimeout(function() { banner.remove(); }, 300);
            }
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            PWA_INSTALL.init();
        });
    } else {
        PWA_INSTALL.init();
    }

    window.PWA_INSTALL = PWA_INSTALL;

})();
