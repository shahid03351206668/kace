from .main import Employee

app_name = "kace"
app_title = "KACE"
app_publisher = "CodesSoft"
app_description = "kace"
app_email = "info@codessoft.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kace",
# 		"logo": "/assets/kace/logo.png",
# 		"title": "KACE",
# 		"route": "/kace",
# 		"has_permission": "kace.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kace/css/kace.css"
# app_include_js = "/assets/kace/js/kace.js"

# include js, css files in header of web template
# web_include_css = "/assets/kace/css/kace.css"
# web_include_js = "/assets/kace/js/kace.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kace/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Employee" : "public/js/employee_custom.js",
    "Location Request" : "public/js/location_request_custom.js",
    "Attendance Location" : "public/js/attendance_location_custom.js",
    "Employee Checkin" : "public/js/employee_checkin_custom.js",
    "Kace Settings" : "public/js/kace_settings_custom.js",
    "Notification Schedule" : "public/js/notification_schedule_custom.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kace/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kace.utils.jinja_methods",
# 	"filters": "kace.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kace.install.before_install"
# after_install = "kace.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kace.uninstall.before_uninstall"
# after_uninstall = "kace.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kace.utils.before_app_install"
# after_app_install = "kace.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kace.utils.before_app_uninstall"
# after_app_uninstall = "kace.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kace.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {"Shift Type": "kace.shift_type_custom.ShiftTypeCustom"}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # "*": {
    # 	"on_update": "method",
    # 	"on_cancel": "method",
    # 	"on_trash": "method"
    # }
    "Face Verification": {"after_insert": "kace.main.face_verification_after_insert"},
    "Employee": {
        "validate": "kace.main.validate_employee",
        "after_insert": "kace.main.create_employee_user",
    },
    # "Employee Checkin": {
    #     "after_insert": "kace.main.employee_checkin_after_insert",
    #     "validate": "kace.main.employee_checkin_validate",
    # },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    # "all": [
    # 	"kace.tasks.all"
    # ],
    "daily": [
        # "kace.main.update_employee_attendance",
        "kace.main.create_daily_attendance"
    ],
    # "hourly": [
    # 	"kace.tasks.hourly"
    # ],
    # "weekly": [
    # 	"kace.tasks.weekly"
    # ],
    # "monthly": [
    # 	"kace.tasks.monthly"
    # ],
    "cron": {
        "0/5 * * * *": [
            "kace.kace.doctype.notification_schedule.notification_schedule.send_schedule_notifications"
        ]
    },
}

# Testing
# -------

# before_tests = "kace.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kace.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kace.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kace.utils.before_request"]
# after_request = ["kace.utils.after_request"]

# Job Events
# ----------
# before_job = ["kace.utils.before_job"]
# after_job = ["kace.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kace.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
    {"dt": "Custom Field", "filters": {"module": "KACE"}},
    {"dt": "Client Script", "filters": {"module": "KACE"}},
]
