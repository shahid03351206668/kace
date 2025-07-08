# Copyright (c) 2025, CodesSoft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import jwt
import requests
from datetime import timedelta, datetime
import json
from frappe.utils import cstr


class NotificationSchedule(Document):
    def on_submit(self):
        if not self.employees:
            frappe.throw("Please add employees to the schedule")

        self.create_notification_checkins()

        if self.alert_type == "Immediate":
            self.send_immediate_notification()

    def create_notification_checkins(self):
        for i in self.employees:
            if not i.employee:
                continue

            checkin_doc = frappe.new_doc("Notification Checkin")
            checkin_doc.employee = i.employee
            checkin_doc.log_type = "IN"
            checkin_doc.time = frappe.utils.now_datetime()
            checkin_doc.notification_schedule = self.name
            checkin_doc.save()

    def get_access_token(self):
        import time as time_object

        now = int(time_object.time())
        payload = {
            "iss": "push-notifications@employee-hub-cf56c.iam.gserviceaccount.com",
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": now + 3600,
        }

        signed_jwt = jwt.encode(
            payload,
            "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDAoykgXTWArHcy\nX43Nfq42mYvnwPfpY4W9MTeyRmOlvV2UPbbfDvA8FA4XabIx9anJz1TlbMO+zCBp\nElIVX5V523kkzIZ6VpENeXVrmoDLoCG6TvfVW8vW4FYL34DVDLo6mWurrrJIQAsE\nBmOIQKP5OB9lLka+EmIFg0WwQoo6XJhWtCRPuGUEgbwvPi1Yq+CxrnYXvi3Dbd9z\nDfQvx0X2KIqgyB/GakEY6x6vuB3a/Y1L+3cJDtrFkEUJC02nEwk1+Wk1z5//A9Ke\njSzfwOXz5xu7O3IcaJtVudU2MkS4cduK3wsBVp12HX4P1Xq8zZ62t5PkPUlaZ1Hr\np+r69xN/AgMBAAECggEADjXuTb9/UYIau1hgAWQyY9kis5kBPaVXpopGV1w1jT93\n8y/OTFj+XeA43eWwY8EbCMX6HeabiUXm48Y0A45s9doiVXwFAgQqzsZCZD3q+TQg\nTzpa5Z42kYZnf2Ugf7CUEfvJY2PcYQbgb46TfxsNpAMaeQAkVdczUsBi8eRZ7Oe3\nWhZZHGr6fX050PoY4lDiwuJenOBeRzQpioFbVLT6jWCYvrnjw4c8n2FOvm6e+ahZ\n/nicnr8v6Rx8Qv3DNDAgL0hzQyVuuj00c0dFRUmq9jiLGqGLeZUAuU4nJu4pzzJf\ndFy4J4GPzdIy6P+r2pfhvZy76T+0UL24AeEoGzps0QKBgQDq0lBAWPksgaPtvdq9\nkst+5+TQ9zotaUwKi8nj1BUJkU/Vk8I1OpSQqQrt2iDwjwOSi809jTCrXsbPD2x6\nyjWeFNh+zpm7rn7ioIOLY9lssX1xPkqdhidg572lBYR4Ph2TD2r0DMaaBDw4CMoH\nNf4LJ0+vKqwgyBTayDv0JPVf+QKBgQDSAuAzKP5KgCYvi6V8OfrX1xfBD9Y82HOS\nG0p9hRk+scGVAjVjS9Ol2zvNFlTBBxccWkT/3+oTNybhKpQFlRvMBRViuwyTOHjk\nO4+fULA18U5z6t2imAeknPWxfl/AT8nwX8hGz8lq9KN7jRkcKd+fzubHvXPuWqhV\noXLT1fJdNwKBgQCAEYohPiVPx7i/Lf+ByvDfWtvpuBxrrfUB/3FxpzZ+DFmNM1QF\nMdja+Mb0KDY03Nrm7wZV3o4/uKYXQeM5KNWLTPUyW71upeGf+kkkGaX4aOjwfTe2\np/cMG/fLa7Hu3nnEvfDn/5vFXi/1o52Dx0exj5QfBdfw3Q66r+A67HlDCQKBgQCJ\nMwXDhpFynHvV7fZjzQEah1PmdfExePsvxZKJpC2U7s4YCgRU5ZHUtgBAgMlH/djU\nVgjj3SXv/cTxrz5a00oApIWPJcIWX/tip6KxoyYrZ4UoZ5T6BzZfDYfZuETXv4ie\n+ARAdrkQndg7/DceViDZJ3NPpG6bljCJGNuKlygqSwKBgDBwaKl4xR4XrKI0JwRL\ngR1GtJd825MUtk13HhPOzFCaKvmMdjsFmuQms2nqPnwXP3ROs9UJw5xy1utFkCqz\n20sxgsGvH8J1dDy2TjEZkFLplgK/J14NO2YsCI3Jw/bUhSuAx/a+cNn36axDie/2\ndbLFNzjS88L5NiAaR2KanpeV\n-----END PRIVATE KEY-----\n",
            algorithm="RS256",
        )

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": signed_jwt,
            },
        )

        if response.ok:
            return response.json().get("access_token")

    def send_immediate_notification(self):
        for i in self.employees:
            try:
                self.send_notification(
                    frappe.db.get_value("Employee", i.employee, "user_id")
                )
            except Exception as e:
                frappe.log_error("Error in sending notification", str(e))

    def send_notification(self, user):

        if not user:
            return

        tokens = frappe.db.get_list(
            "Notifications Subscriptions",
            filters={"user_id": user},
            pluck="device_token",
        )

        for i in tokens:
            response = requests.post(
                "https://fcm.googleapis.com/v1/projects/employee-hub-cf56c/messages:send",
                headers={"Authorization": "Bearer " + self.get_access_token()},
                data=json.dumps(
                    {
                        "message": {
                            "token": i,
                            "notification": {
                                "title": "Random Check Alert",
                                "body": "Open to mark random check attendance",
                            },
                            "data": {
                                "schedule_id": str(self.name),
                                "notification_time": frappe.utils.now_datetime().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "timeout": cstr(self.notification_timeout),
                                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                                "screen": "/random_check",
                            },
                            "apns": {
                                "payload": {
                                    "aps": {
                                        "mutable-content": 1,
                                        "sound": "default",
                                        "badge": 1,
                                    }
                                }
                            },
                        }
                    }
                ),
            )
            frappe.log_error("FCM Response", str(response.json()))


def send_schedule_notifications():
    start_time = frappe.utils.now_datetime() - timedelta(minutes=5)
    records = frappe.db.sql(
        """
		select 
			name
		from `tabNotification Schedule` 
		where schedule_time between %s and %s
		and alert_type = 'Scheduled'
		""",
        (
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    for i in records:
        doc = frappe.get_doc("Notification Schedule", i[0])
        for i in doc.employees:
            doc.send_notification(
                frappe.db.get_value("Employee", i.employee, "user_id")
            )


@frappe.whitelist(allow_guest=True)
def validate_schedule_notification(notification_time, employee, schedule_id):
    # frappe.response["message"] = schedule_id
    # return
    schedule_doc = frappe.get_doc("Notification Schedule", schedule_id)
    schedule_time = datetime.strptime(
        notification_time, "%Y-%m-%d %H:%M:%S"
    ) + timedelta(seconds=schedule_doc.notification_timeout)

    current_time = frappe.utils.now_datetime()
    if schedule_time < current_time:
        frappe.db.set_value(
            "Notification Checkin",
            {
                "notification_schedule": schedule_id,
                "employee": employee,
            },
            {"status": "Expired"},
        )
        frappe.response["message"] = "Expired"
        return

    frappe.db.set_value(
        "Notification Checkin",
        {
            "notification_schedule": schedule_id,
            "employee": employee,
        },
        {"status": "Acknowledged"},
    )
    frappe.response["message"] = "Acknowledged"
    return
