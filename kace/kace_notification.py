import json
import re
from datetime import datetime, timedelta

import frappe
import jwt
import requests
from frappe.utils import cstr


def send_employee_checkins_notification_cron():
    frappe.log_error("Linux cron job")
    current_time = datetime.now()
    prev_time = datetime.now() - timedelta(minutes=5)
    data = frappe.db.sql(
        """
        select 
            c.time, 
            p.name as employee, 
            p.user_id 
        from `tabEmployee Notification Schedule` c 
        inner join `tabEmployee` p on c.parent = p.name 
        where time between %s and %s""",
        (prev_time.time(), current_time.time()),
        as_dict=True,
        debug=True,
    )

    frappe.log_error("Employee Notification Schedule Data: ", str(data))

    if not data:
        return

    for i in data:
        if not i.get("user_id"):
            continue

        send_notification(i.get("user_id"))


@frappe.whitelist()
def send_notification(user_id):
    device_tokens = frappe.db.get_list(
        "Notifications Subscriptions",
        filters={"user_id": user_id},
        pluck="device_token",
    )

    # Get the current time for logging
    current_time = datetime.now()

    notification_title = "Random Check Alert"
    notification_body = "Open to mark random check attendance"

    for i in device_tokens:
        access_token = get_access_token()

        if not access_token:
            continue

        try:
            response = requests.post(
                "https://fcm.googleapis.com/v1/projects/employee-hub-cf56c/messages:send",
                headers={"Authorization": "Bearer " + access_token},
                data=json.dumps(
                    {
                        "message": {
                            "token": i,
                            "notification": {
                                "title": notification_title,
                                "body": notification_body,
                            },
                            "data": {
                                "notification_time": current_time.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
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

        except Exception as e:
            frappe.log_error(str(e), "Notification Send Failed")
            return

    # Create notification log in Frappe
    notification_log = frappe.get_doc(
        {
            "doctype": "Notification Log",
            "subject": notification_title,
            "for_user": user_id,
            "type": "Alert",
            "email_content": notification_body,
        }
    )
    notification_log.insert(ignore_permissions=True)
    frappe.db.commit()


def get_access_token():
    import time as time_object

    now = int(time_object.time())
    payload = {
        "iss": "push-notifications@employee-hub-cf56c.iam.gserviceaccount.com",  # your  "client_email"
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "aud": "https://oauth2.googleapis.com/token",  # your "token_uri"
        "iat": now,
        "exp": now + 3600,
    }

    # The private key should be in a file or environment variable for security reasons.
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


def send_notification_log(self, method=None):
    TAG_RE = re.compile(r"<[^>]+>")
    subject = TAG_RE.sub("", cstr(self.subject))
    email_content = TAG_RE.sub("", cstr(self.email_content))

    try:
        device_tokens = frappe.db.get_list(
            "Notifications Subscriptions",
            filters={"user_id": self.for_user},
            pluck="device_token",
        )

        if not device_tokens:
            return

        for i in device_tokens:
            access_token = get_access_token()
            if not access_token:
                continue

            requests.post(
                "https://fcm.googleapis.com/v1/projects/employee-hub-cf56c/messages:send",
                headers={"Authorization": f"Bearer {access_token}"},
                data=json.dumps(
                    {
                        "message": {
                            "token": i,
                            "notification": {
                                "title": subject,
                                "body": email_content,
                            },
                            "apns": {
                                "payload": {"aps": {"sound": "default", "badge": 1}}
                            },
                        }
                    }
                ),
            )

    except Exception as e:
        frappe.log_error(str(e), "Notification Failed")


@frappe.whitelist()
def validate_notification_checkin(notification_time, user_id, ): ...
