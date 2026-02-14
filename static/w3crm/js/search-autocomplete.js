/**
 * EgliseConnect - Search Autocomplete / Typeahead
 *
 * Provides instant search suggestions as the user types in the header search bar.
 * Debounces requests and displays results in a dropdown.
 */

(function() {
    'use strict';

    var SEARCH_AUTOCOMPLETE = {
        input: null,
        dropdown: null,
        debounceTimer: null,
        debounceDelay: 300,
        minChars: 2,

        init: function() {
            this.input = document.querySelector('.search-area input[name="q"]');
            if (!this.input) return;

            this.createDropdown();
            this.bindEvents();
        },

        createDropdown: function() {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'search-autocomplete-dropdown';
            this.dropdown.style.cssText =
                'display:none;position:absolute;top:100%;left:0;right:0;' +
                'background:#fff;border:1px solid #e6e6e6;border-radius:0 0 8px 8px;' +
                'box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:9999;max-height:400px;' +
                'overflow-y:auto;';

            var parent = this.input.closest('.search-area') || this.input.parentElement;
            parent.style.position = 'relative';
            parent.appendChild(this.dropdown);
        },

        bindEvents: function() {
            var self = this;

            this.input.addEventListener('input', function() {
                clearTimeout(self.debounceTimer);
                var query = this.value.trim();

                if (query.length < self.minChars) {
                    self.hideDropdown();
                    return;
                }

                self.debounceTimer = setTimeout(function() {
                    self.fetchSuggestions(query);
                }, self.debounceDelay);
            });

            this.input.addEventListener('focus', function() {
                if (this.value.trim().length >= self.minChars && self.dropdown.children.length > 0) {
                    self.showDropdown();
                }
            });

            // Hide on click outside
            document.addEventListener('click', function(e) {
                if (!self.input.contains(e.target) && !self.dropdown.contains(e.target)) {
                    self.hideDropdown();
                }
            });

            // Keyboard navigation
            this.input.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    self.hideDropdown();
                }
            });
        },

        fetchSuggestions: function(query) {
            var self = this;
            var url = '/search/autocomplete/?q=' + encodeURIComponent(query);

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                self.renderSuggestions(data.suggestions || []);
            })
            .catch(function() {
                self.hideDropdown();
            });
        },

        renderSuggestions: function(suggestions) {
            this.dropdown.innerHTML = '';

            if (suggestions.length === 0) {
                this.hideDropdown();
                return;
            }

            var self = this;
            suggestions.forEach(function(item) {
                var div = document.createElement('a');
                div.href = item.url;
                div.className = 'search-suggestion-item';
                div.style.cssText =
                    'display:flex;align-items:center;padding:10px 16px;text-decoration:none;' +
                    'color:#333;border-bottom:1px solid #f0f0f0;transition:background 0.2s;';
                div.innerHTML =
                    '<i class="fas ' + self.escapeHtml(item.icon || 'fa-search') +
                    '" style="margin-right:12px;color:#888;width:16px;text-align:center;"></i>' +
                    '<div>' +
                    '<div style="font-weight:500;font-size:14px;">' + self.escapeHtml(item.label) + '</div>' +
                    '<div style="font-size:12px;color:#999;">' + self.escapeHtml(item.category) + '</div>' +
                    '</div>';

                div.addEventListener('mouseenter', function() {
                    this.style.background = '#f8f9fa';
                });
                div.addEventListener('mouseleave', function() {
                    this.style.background = '';
                });

                self.dropdown.appendChild(div);
            });

            this.showDropdown();
        },

        showDropdown: function() {
            this.dropdown.style.display = 'block';
        },

        hideDropdown: function() {
            this.dropdown.style.display = 'none';
        },

        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(text || ''));
            return div.innerHTML;
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            SEARCH_AUTOCOMPLETE.init();
        });
    } else {
        SEARCH_AUTOCOMPLETE.init();
    }

    window.SEARCH_AUTOCOMPLETE = SEARCH_AUTOCOMPLETE;

})();
