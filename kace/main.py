import json
import re
from datetime import datetime

import frappe
import requests
from frappe.utils import cint, cstr, flt, getdate, now
from frappe.utils.file_manager import save_file

from erpnext.setup.doctype.employee.employee import Employee
from .kace_notification import get_access_token


@frappe.whitelist(allow_guest=True)
def update_face_verification_status(id, status):
    frappe.db.set_value("Face Verification", id, {"status": status})
    frappe.db.commit()
    frappe.response.message = "Face verification status updated successfully"


def face_verification_after_insert(self, method=None):
    employee_user = frappe.db.get_value("Employee", self.employee, "user_id")
    if not employee_user:
        return

    device_tokens = frappe.db.get_list(
        "Notifications Subscriptions",
        filters={"user_id": employee_user},
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
                            "title": "Kiosk",
                            "body": "You have new alert message",
                        },
                        "data": {
                            "id": self.name,
                            "alert_message": self.message,
                            "screen": "/alert_screen",
                            "click_action": "FLUTTER_NOTIFICATION_CLICK",
                        },
                        "apns": {"payload": {"aps": {"sound": "default", "badge": 1}}},
                    }
                }
            ),
        )


...


def create_employee_user(self, method=None):
    if not self.get("personal_email"):
        return

    if self.user_id:
        return

    user = frappe.new_doc("User")
    user.email = self.personal_email
    user.first_name = self.first_name
    user.last_name = self.last_name
    user.middle_name = self.middle_name
    user.birth_date = self.date_of_birth
    user.phone = self.cell_number
    user.send_welcome_email = False
    user.flags.ignore_permissions = True
    user.save()

    self.db_set("user_id", user.name)


def create_daily_attendance():
    today = getdate()
    employees = frappe.db.sql(
        "select name from `tabEmployee` where status = 'Active' ", as_dict=True
    )

    for i in employees:
        try:
            doc = frappe.new_doc("Attendance")
            doc.attendance_date = today
            doc.status = "Absent"
            doc.employee = i.name
            doc.flags.ignore_permissions = True
            doc.save()
        except Exception as error:
            frappe.log_error(
                f"Daily attendance job error employee {i.name}",
                f"{error} \n\n\n {frappe.get_traceback()}",
            )


def validate_employee(self, method=None):
    if self.status == "Left" and self.user_id:
        frappe.db.set_value("User", self.user_id, {"enabled": 0})

    elif (
        self.status == "Active"
        and self.user_id
        and not frappe.db.get_value("User", self.user_id, "enabled")
    ):
        frappe.db.set_value("User", self.user_id, {"enabled": 1})


def validate_for_enabled_user_id_func(self, enabled):
    if not self.status == "Active":
        return

    if enabled is None:
        frappe.throw("User {0} does not exist").format(self.user_id)

    # if enabled == 0:
    #     frappe.throw(_("User {0} is disabled").format(self.user_id), EmployeeUserDisabledError)


Employee.validate_for_enabled_user_id = validate_for_enabled_user_id_func


def get_user_language() -> str:
    system_language = frappe.db.get_value(
        "System Settings", "System Settings", "language"
    )
    user_language = frappe.db.get_value("User", frappe.session.user, "language")
    if not user_language:
        return system_language or "en"

    if user_language != system_language:
        return user_language

    return system_language


def create_log(title="App Api", message=""):
    frappe.log_error(title, message)


def make_response(success=True, message="Success", data={}, session_success=True):
    frappe.local.response["message"] = {
        "user": get_user_details(),
        "session_success": session_success,
        "success": success,
        "success_key": cint(success),
        "message": message,
        "data": data,
    }


def get_user_details(user=None):
    try:
        if not user:
            user = frappe.session.user

        if user and user not in ["Guest"]:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if employee is None or employee == "":
                frappe.local.response["message"] = {
                    "user": None,
                    "session_success": False,
                    "success": False,
                    "message": "No employee found against this user!",
                }

            user = frappe.get_doc("User", user)
            data = {
                "full_name": user.full_name,
                "name": user.name,
                "sid": frappe.session.sid,
                "version": "15",
                "language": get_user_language(),
                "username": user.username,
                "email": user.email,
                "user_image": user.user_image,
                "success": True,
                "employee": employee,
                # "sales_person": sales_person,
            }
            return frappe._dict(data)
        else:
            frappe.local.response["message"] = {
                "user": None,
                "session_success": False,
                "success": False,
                "message": "Session not found",
            }
            return
    except Exception:
        frappe.local.response["message"] = {
            "user": None,
            "session_success": False,
            "success": False,
            "message": "Invalid login credentials!",
            "data": data,
        }


def get_date_time_to_use():
    dt = now()
    date, time = dt.split(" ")
    date = date.split("-")
    d = datetime.strptime(time, "%H:%M:%S.%f")
    formatted_time = d.strftime("%I:%M:%S %p")
    time = time.split(":")
    data = {
        "formatted_time": formatted_time,
        "now": dt,
        "today": getdate(),
        "year": date[0],
        "month": date[1],
        "day": date[2],
        "hour": time[0],
        "min": time[1],
        "sec": time[2],
    }
    return frappe._dict(data)


@frappe.whitelist(allow_guest=True)
def get_date_time():
    try:
        user_details = get_user_details()
        if user_details:
            dt = now()
            date, time = dt.split(" ")
            date = date.split("-")
            d = datetime.strptime(time, "%H:%M:%S.%f")
            formatted_time = d.strftime("%I:%M:%S %p")
            time = time.split(":")
            data = {
                "user_details": user_details,
                "formatted_time": formatted_time,
                "now": dt,
                "today": getdate(),
                "year": date[0],
                "month": date[1],
                "day": date[2],
                "hour": time[0],
                "min": time[1],
                "sec": time[2],
            }
            make_response(data=data)
        else:
            make_response(
                success=False, message="Session Not Found.", session_success=False
            )
    except Exception as e:
        create_log("Failed to Send Datetime", e)
        make_response(success=False, message=e)


@frappe.whitelist(allow_guest=True)
def subscribe_notifications(user_id, device_token, unsubscribe=False):
    if unsubscribe:
        subcription = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` WHERE user_id = '{user_id}' AND device_token = {frappe.db.escape(device_token)}  """
        )
        if subcription:
            frappe.delete_doc("Notifications Subscriptions", subcription[0][0])
            frappe.db.commit()
            frappe.response["message"] = "Unsubcribe successfully"
        else:
            frappe.response["message"] = f"No record found for {user_id}"

    else:
        old_subcriptions = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` WHERE device_token = {frappe.db.escape(device_token)}  """
        )

        if old_subcriptions:
            record = old_subcriptions[0][0]
            frappe.delete_doc("Notifications Subscriptions", record)
            frappe.db.commit()

        subscription_doc = frappe.new_doc("Notifications Subscriptions")
        subscription_doc.user_id = user_id
        subscription_doc.device_token = device_token
        subscription_doc.flags.ignore_permissions = True
        subscription_doc.save()
        frappe.db.commit()
        frappe.response["message"] = "Subcribe successfully"


def striphtml(data):
    p = re.compile(r"<.*?>")
    return p.sub("", data)


def send_notifications_users(self, method=None):
    url = "https://fcm.googleapis.com/v1/projects/employee-hub-cf56c/messages:send"
    for_user = self.for_user
    content = self.email_content
    devices = frappe.db.sql(
        f"""SELECT device_token FROM `tabNotifications Subscriptions` WHERE user_id = '{for_user}' """
    )
    for device in devices:
        device_token = device[0]
        try:
            oauth2_url = "https://oauth2.googleapis.com/token"
            oauth2_payload = json.dumps(
                {
                    "client_id": "551442328561-e2jlvas05evofok2arr7jticat673gis.apps.googleusercontent.com",
                    "client_secret": "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",
                    "refresh_token": "1//04QigEfWIN3VaCgYIARAAGAQSNwF-L9IrDuVDhBuvlueynfjjKfQmL-Z03M_n9ikeekmyjxCXa60ob-Zl-svH93jiczNchN0utc0",
                    "grant_type": "refresh_token",
                }
            )
            oauth2_response = requests.request(
                "POST",
                oauth2_url,
                headers={"Content-Type": "application/json"},
                data=oauth2_payload,
            )
            if oauth2_response.status_code == 200:
                token_res = oauth2_response.json()
                access_token = token_res.get("access_token")
                if access_token:
                    firebase_token_req = requests.request(
                        "POST",
                        url,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                        data=json.dumps(
                            {
                                "message": {
                                    "token": device_token,
                                    "notification": {
                                        "body": striphtml(content),
                                        "title": striphtml(self.subject or ""),
                                    },
                                }
                            }
                        ),
                    )
                    if firebase_token_req.status_code == 200:
                        frappe.log_error("Firebase Success notification")
        except Exception as e:
            frappe.log_error("Firbase Error", str(e))
