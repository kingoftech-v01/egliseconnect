# Static Folder Name
folder_name = "w3crm"

dz_array = {
    "public": {
        "favicon": f"{folder_name}/images/favicon.png",
        "description": "EgliseConnect - Système de gestion d'église",
        "og_title": "EgliseConnect - Gestion d'église",
        "og_description": "Système de gestion pour les églises - Membres, Dons, Événements, Volontaires",
        "og_image": "",
        "title": "EgliseConnect - Gestion d'église",
    },
    "global": {
        "css": [
            f"{folder_name}/vendor/bootstrap-select/dist/css/bootstrap-select.min.css",
            f"{folder_name}/css/style.css",
        ],
        "js": {
            "top": [
                f"{folder_name}/vendor/global/global.min.js",
                f"{folder_name}/vendor/bootstrap-select/dist/js/bootstrap-select.min.js",
            ],
            "bottom": [
                f"{folder_name}/js/custom.min.js",
                f"{folder_name}/js/deznav-init.js",
            ],
        },
    },
    "pagelevel": {
        "w3crm": {
            "w3crm_views": {
                "css": {
                    # Reports app
                    "dashboard": [
                        f"{folder_name}/vendor/chartist/css/chartist.min.css",
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                        f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
                    ],
                    "member_stats": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "donation_report": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "attendance_report": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "volunteer_report": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "birthday_report": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    # Members app
                    "member_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "member_detail": [],
                    "member_create": [],
                    "member_update": [],
                    "birthday_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "directory": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "privacy_settings": [],
                    "group_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "group_detail": [],
                    "family_detail": [],
                    # Donations app
                    "donation_create": [],
                    "donation_detail": [],
                    "donation_history": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "donation_admin_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "donation_record": [],
                    "campaign_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "campaign_detail": [],
                    "receipt_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "receipt_detail": [],
                    "donation_monthly_report": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    # Events app
                    "event_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "event_detail": [],
                    "event_calendar": [
                        f"{folder_name}/vendor/fullcalendar/css/main.min.css",
                    ],
                    # Volunteers app
                    "position_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "schedule_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "my_schedule": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "availability_update": [],
                    # Communication app
                    "newsletter_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "newsletter_detail": [],
                    "newsletter_create": [],
                    "notification_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "preferences": [],
                    # Help Requests app
                    "request_list": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                    "request_detail": [],
                    "request_create": [],
                    "my_requests": [
                        f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
                    ],
                },
                "js": {
                    # Reports app
                    "dashboard": [
                        f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
                        f"{folder_name}/vendor/apexchart/apexchart.js",
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "member_stats": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "donation_report": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "attendance_report": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "volunteer_report": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "birthday_report": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    # Members app
                    "member_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
                        f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
                        f"{folder_name}/vendor/datatables/js/jszip.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "member_detail": [],
                    "member_create": [],
                    "member_update": [],
                    "birthday_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "directory": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
                        f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
                        f"{folder_name}/vendor/datatables/js/jszip.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "privacy_settings": [],
                    "group_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "group_detail": [],
                    "family_detail": [],
                    # Donations app
                    "donation_create": [],
                    "donation_detail": [],
                    "donation_history": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "donation_admin_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
                        f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
                        f"{folder_name}/vendor/datatables/js/jszip.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "donation_record": [],
                    "campaign_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "campaign_detail": [],
                    "receipt_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "receipt_detail": [],
                    "donation_monthly_report": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    # Events app
                    "event_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "event_detail": [],
                    "event_calendar": [
                        f"{folder_name}/vendor/fullcalendar/js/main.min.js",
                    ],
                    # Volunteers app
                    "position_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "schedule_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "my_schedule": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "availability_update": [],
                    # Communication app
                    "newsletter_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "newsletter_detail": [],
                    "newsletter_create": [],
                    "notification_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "preferences": [],
                    # Help Requests app
                    "request_list": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                    "request_detail": [],
                    "request_create": [],
                    "my_requests": [
                        f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
                        f"{folder_name}/js/plugins-init/datatables.init.js",
                    ],
                },
            },
        },
    },
}
