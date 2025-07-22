import json
import re
from datetime import datetime

import frappe
import requests
from frappe.utils import cint, cstr, flt, getdate, now
from frappe.utils.file_manager import save_file


def create_log(title="App Api", message=""):
    frappe.log_error(title, message)


def make_response(success=True, message="Success", data={}, session_success=True):
    frappe.local.response["message"] = {
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
            employee, employee_type = frappe.db.get_value(
                "Employee", {"user_id": user}, ["name", "employee_type"]
            ) or [None, None]
            # sales_person = frappe.db.get_value("Sales Person", {"user": user, "enabled": 1}, "name")
            user = frappe.get_doc("User", user)
            data = {
                "name": user.name,
                "sid": frappe.session.sid,
                "username": user.username,
                "email": user.email,
                "employee": employee,
                "user_image": user.user_image,
                "employee_type": employee_type,
                # "sales_person": sales_person,
            }
            return frappe._dict(data)
        else:
            make_response(
                success=False, message="Session Not Found.", session_success=False
            )
    except Exception as e:
        create_log("API Test", f"{e}\n{frappe.get_traceback()}")
        make_response(success=False, message="Invalid login credentials!")


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
        subscription = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` 
                WHERE user_id = '{user_id}' AND device_token = {frappe.db.escape(device_token)} """
        )
        if subscription:
            frappe.delete_doc("Notifications Subscriptions", subscription[0][0])
            frappe.db.commit()
            frappe.response["message"] = "Unsubscribe successfully"
        else:
            frappe.response["message"] = f"No record found for {user_id}"
    else:
        old_subscriptions = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` 
                WHERE device_token = {frappe.db.escape(device_token)} """
        )

        if old_subscriptions and len(old_subscriptions) > 0:
            record = old_subscriptions[0][0]
            frappe.delete_doc("Notifications Subscriptions", record)
            frappe.db.commit()

        try:
            subscription_doc = frappe.new_doc("Notifications Subscriptions")
            subscription_doc.user_id = user_id
            subscription_doc.device_token = device_token
            subscription_doc.flags.ignore_permissions = True
            subscription_doc.save()
            frappe.db.commit()
            frappe.response["message"] = "Subscribe successfully"
        except Exception as e:
            frappe.log_error(
                f"Failed to create subscription: {str(e)}",
                "Notification Subscription Error",
            )
            frappe.response["message"] = "Failed to subscribe"


def striphtml(data):
    try:
        p = re.compile(r"<.*?>")
        return p.sub("", data)
    except Exception:
        return ""


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


@frappe.whitelist(allow_guest=True)
def set_face_recongnition():
    try:
        request_data = json.loads(frappe.request.data)
        user_details = get_user_details()

        if not user_details.employee:
            return

        if not request_data:
            return

        doc = frappe.get_doc("Employee", user_details.employee)
        doc.face_registration_data = request_data.get("image", {}).get("base64")
        doc.flags.ignore_permissions = True
        doc.save()

        facial_image = save_file(
            request_data.get("image", {}).get("name"),
            request_data.get("image", {}).get("base64"),
            doc.doctype,
            doc.name,
            decode=True,
            is_private=0,
            df="face_image_registration",
        )

        if facial_image.name:
            frappe.db.set_value(
                doc.doctype,
                doc.name,
                {"face_image_registration": facial_image.file_url},
            )
            frappe.db.commit()
            frappe.response["message"] = "Face registration image updated successfully!"

    except Exception as e:
        create_log("Api Failed", e)


@frappe.whitelist(allow_guest=True)
def get_face_recongnition():
    data = frappe.db.sql(
        "SELECT name, user_id, face_registration_data FROM `tabEmployee` WHERE (face_registration_data IS NOT NULL or face_registration_data != '') ",
        as_dict=True,
    )
    return [d for d in data if d.face_registration_data]


@frappe.whitelist(allow_guest=True)
def get_koisk_users():
    user = frappe.get_list(
        "Employee",
        fields=["name", "user_id", "face_registration_data"],
    )
    # return [u for u in user if u.face_registration_data]
    return user


@frappe.whitelist(allow_guest=True)
def set_koisk_user_face():
    try:
        request_data = json.loads(frappe.request.data)

        if not request_data:
            return

        doc = frappe.get_doc("Employee", request_data.get("employee"))
        doc.face_registration_data = request_data.get("image", {}).get("base64")
        doc.flags.ignore_permissions = True
        doc.save()

        facial_image = save_file(
            request_data.get("image", {}).get("name"),
            request_data.get("image", {}).get("base64"),
            doc.doctype,
            doc.name,
            decode=True,
            is_private=0,
            df="face_image_registration",
        )

        if facial_image.name:
            frappe.db.set_value(
                doc.doctype,
                doc.name,
                {"face_image_registration": facial_image.file_url},
            )
            frappe.db.commit()
            frappe.response["message"] = "Face registration image updated successfully!"

    except Exception as e:
        create_log("Api Failed", e)
