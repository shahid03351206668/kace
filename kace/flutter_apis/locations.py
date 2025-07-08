from datetime import datetime
from json import loads

import frappe
from frappe.utils import cint, cstr, flt

from .main import create_log, get_user_details, make_response


@frappe.whitelist(allow_guest=True)
def employee_allowed_locations():
    try:
        user_details = get_user_details()
        if user_details:
            emp_id = user_details.get("employee")
            data = frappe.db.sql(
                f""" SELECT a.location_name, a.latitude, a.longitude,a.meters  FROM  `tabAttendance Location Employee` p INNER JOIN  `tabAttendance Location` a on a.name = p.parent 
				WHERE p.employee = '{emp_id}' 
				""",
                as_dict=True,
            )
            make_response(success=True, data=data)
        # for entry in data:
        # 	entry['latitude'] = flt(entry['latitude'],10)  # Adjust the precision as needed
        # 	entry['longitude'] = flt(entry['longitude'],10)
        # else:
        # make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist()
def create_attendance_location():
    user_details = get_user_details()
    data: dict = loads(frappe.request.data)

    if user_details:
        try:
            attendance_location_doc = frappe.new_doc("Attendance Location")
            attendance_location_doc.longitude = data.get("longitude")
            attendance_location_doc.latitude = data.get("latitude")
            attendance_location_doc.meters = data.get("meters")
            attendance_location_doc.location_name = data.get("location_name")
            for row in data.get("employees"):
                attendance_location_doc.append("item", row)

            # attendance_location_doc.save(ignore_permissions=True)
            attendance_location_doc.run_method("set_missing_values")
            attendance_location_doc.save()

            frappe.db.commit()
            frappe.response["message"] = "New Attendance Location added successfully!"
            frappe.response["data"] = attendance_location_doc
        except Exception as e:
            frappe.response["success"] = False
            frappe.response["message"] = str(e)
    else:
        frappe.response["message"] = "Session user not found!"


@frappe.whitelist()
def request_attendance_location():
    user_details = get_user_details()
    data: dict = loads(frappe.request.data)

    if user_details:
        try:
            location_request_doc = frappe.new_doc("Location Request")
            location_request_doc.employee = data.get("employee")
            location_request_doc.location_name = data.get("location_name")
            location_request_doc.longitude = data.get("longitude")
            location_request_doc.latitude = data.get("latitude")
            location_request_doc.meters = data.get("meters")

            location_request_doc.run_method("set_missing_values")
            location_request_doc.save()

            frappe.db.commit()
            frappe.response["message"] = (
                "Request for Attendance Location has been created successfully!"
            )
            frappe.response["data"] = location_request_doc
        except Exception as e:
            frappe.response["success"] = False
            frappe.response["message"] = str(e)
    else:
        frappe.response["message"] = "Session User not found!"


# @frappe.whitelist()
# def create_attendance_location():
#     user_details = get_user_details()
#     if not user_details:
#         frappe.response["message"] = "Session user not found!"
#         return
#
#     # Check if user has permission to create Attendance Location
#     if not frappe.has_permission(
#         "Attendance Location", "create", user=frappe.session.user
#     ):
#         frappe.throw(
#             _("Not permitted to create Attendance Location"), frappe.PermissionError
#         )
#
#     data: dict = loads(frappe.request.data)
#     attendance_location_doc = frappe.new_doc("Attendance Location")
#     attendance_location_doc.latitude = data.get("latitude")
#     attendance_location_doc.longitude = data.get("longitude")
#     attendance_location_doc.meters = data.get("meters")
#     attendance_location_doc.location_name = data.get("location_name")
#
#     # Remove ignore_permissions=True to respect permission system
#     attendance_location_doc.save()
#     frappe.db.commit()
#
#     frappe.response["message"] = "New Attendance Location added successfully!"
#     frappe.response["data"] = attendance_location_doc
