import json
from datetime import datetime, timedelta
from json import loads
import json
from frappe.utils import get_time

import frappe
from frappe.utils import cint, cstr, flt, get_datetime, getdate
from frappe.utils.file_manager import save_file

from .main import create_log, get_user_details, make_response

# from ..kace_notification import timedelta_to_time


@frappe.whitelist()
def get_attendance(filters=None):
    user = get_user_details()

    if not filters:
        filters = {}

    if not user:
        frappe.response["message"] = "session user not found!"
        frappe.response["success"] = False
        return
    try:
        filters = json.loads(filters) if isinstance(filters, str) else filters
    except Exception:
        filters = {}

    query_conds = ""
    list_filters = {}
    if filters.get("start_date"):
        list_filters["attendance_date"] = [">=", filters.get("start_date")]
        query_conds += f""" and attendance_date >= '{filters.get("start_date")}' """

    if filters.get("end_date"):
        query_conds += f""" and attendance_date <= '{filters.get("end_date")}' """
        list_filters["attendance_date"] = ["<=", filters.get("end_date")]

    user_records = frappe.get_list("Attendance", filters=list_filters)
    user_records = [i.name for i in user_records]
    user_records.append("ABCD")
    user_records.append("EFGH")
    attendance_data = frappe.db.sql(
        f"""select employee, status, in_time as check_in, out_time as check_out, attendance_date as date from `tabAttendance` where 1=1  and name in {tuple(user_records)} and employee = '{user.get("employee")}' {query_conds} order by attendance_date desc""",
        as_dict=True,
        # debug=True,
    )

    attendance_stats = {
        "Total": len(attendance_data),
        "Present": len([row for row in attendance_data if row.status == "Present"]),
        "Absent": len([row for row in attendance_data if row.status == "Absent"]),
    }

    frappe.response["graph"] = attendance_stats
    frappe.response["data"] = attendance_data


# @frappe.whitelist()
# def get_attendance(filters=""):
#     try:
#         data = []
#         user_details = get_user_details()
#         try:
#             filters: dict = loads(filters)
#         except Exception:
#             filters = filters

#         if user_details:
#             query_conds = ""
#             startdate_object = None
#             enddate_object = None
#             if filters.get("start_date"):
#                 startdate_object = datetime.strptime(
#                     filters.get("start_date"), "%Y-%m-%d"
#                 )
#                 query_conds += f""" and  DATE(time) >= '{filters.get("start_date")}' """

#             if filters.get("end_date"):
#                 enddate_object = datetime.strptime(filters.get("end_date"), "%Y-%m-%d")
#                 query_conds += f""" and  DATE(time) <= '{filters.get("end_date")}' """

#             # checkins = """ select time from `tabEmployee Checkin` where
#             # log_type = "IN" and employee = ec.employee and DATE(time) = DATE(ec.time) Order BY time ASC limit 1"""
#             # checkouts = """ select time from `tabEmployee Checkin` where
#             # log_type = "OUT" and employee = ec.employee and DATE(time) = DATE(ec.time)  Order BY time DESC limit 1 """

#             # main_checks = f""" select DATE(ec.time) as date, ec.employee, ({checkins}) as check_in, ({checkouts}) as check_out
#             # from `tabEmployee Checkin` ec where ec.employee = '{user_details.get("employee")}' Group By DATE(ec.time), ec.employee Order By DATE(ec.time) DESC"""

#             data = frappe.db.sql(
#                 f"""
#                 select
#                     DATE (ec.time) as date,
#                     ec.employee,
#                     (
#                         select
#                             time
#                         from
#                             `tabEmployee Checkin`
#                         where
#                             log_type = "IN"
#                             and employee = ec.employee
#                             and DATE (time) = DATE (ec.time)
#                         Order BY
#                             time ASC
#                         limit
#                             1
#                     ) as check_in,
#                     (
#                         select
#                             time
#                         from
#                             `tabEmployee Checkin`
#                         where
#                             log_type = "OUT"
#                             and employee = ec.employee
#                             and DATE (time) = DATE (ec.time)
#                         Order BY
#                             time DESC
#                         limit
#                             1
#                     ) as check_out
#                 from
#                     `tabEmployee Checkin` ec
#                 where
#                     ec.employee = '{user_details.get("employee")}'
#                     {query_conds}
#                 Group By
#                     DATE (ec.time),
#                     ec.employee
#                 Order By
#                     DATE (ec.time) DESC """,
#                 as_dict=1,
#             )

#         Presents = len(["Present" for row in data if (row.check_in or row.check_out)])
#         # _Presents = len(["Present" for row in data])

#         response = {
#             "Total": len(data),
#             "Absent": len(data) - Presents,
#             "Present": Presents,
#         }
#         if startdate_object and enddate_object:
#             response.update(
#                 {"Total": (enddate_object.date() - startdate_object.date()).days + 1}
#             )

#         response["Absent"] = response["Total"] - response["Present"]

#         frappe.response["graph"] = response
#         frappe.response["data"] = data
#         return
#         # make_response(success=True, data=data)
#     except Exception as e:
#         make_response(success=False, message=str(e))


@frappe.whitelist(allow_guest=True)
def add_leaves():
    user_details = get_user_details()
    data: dict = loads(frappe.request.data)

    if user_details:
        leave_doc = frappe.new_doc("Leave Application")
        leave_doc.employee = user_details.get("employee")
        leave_doc.leave_type = data.get("leave_type")
        leave_doc.description = data.get("reason")
        leave_doc.to_date = datetime.strptime(data.get("to_date"), "%Y-%m-%d")
        leave_doc.from_date = datetime.strptime(data.get("from_date"), "%Y-%m-%d")

        if data.get("half_day"):
            leave_doc.half_day = bool(data.get("half_day"))
        leave_doc.save(ignore_permissions=True)

        frappe.db.commit()
        frappe.response["message"] = "Leave added successfully!"
        frappe.response["data"] = leave_doc
    else:
        frappe.response["message"] = "session user not found!"


def compare_time_formats(datetime_str, time_str, log_in_type):
    datetime_str = cstr(datetime_str)
    time_str = cstr(time_str)
    log_in_type = log_in_type

    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    compare_time_only = datetime.strptime(time_str, "%H:%M:%S").time()
    compare_datetime = datetime.combine(dt.date(), compare_time_only)

    time_difference = dt - compare_datetime
    diff_minutes = time_difference.total_seconds() / 60

    if log_in_type == "IN":
        if diff_minutes <= 15:
            return "Normal"
        else:
            return "Late Arrival"
    elif log_in_type == "OUT":
        if diff_minutes < 0:
            return "Early Check Out"
        else:
            return "Normal"


# validate employee checkin with same log type on some date
def validate_duplicate_checkin(employee, log_type, date):
    checkin_record = frappe.db.exists(
        "Employee Checkin",
        {
            "employee": employee,
            "log_type": log_type,
            "time": [
                ">=",
                date - timedelta(minutes=15),
            ],
        },
    )

    if checkin_record:
        return False, "Checkin record already exists for this employee"

    return True, ""


def validate_checkout_record(employee, date, log_type):
    if log_type != "OUT":
        return True, ""

    shift_type = frappe.db.get_value("Employee", employee, "default_shift")
    start_time, end_time = frappe.db.get_value(
        "Shift Type", shift_type, ["start_time", "end_time"]
    )

    checkin_record = frappe.db.sql(
        "select name, time from `tabEmployee Checkin` where employee = %s and log_type = 'IN' ORDER BY time desc limit 1",
        (employee),
    )

    if not checkin_record:
        return True, ""

    checkin_time = checkin_record[0][1]
    total_hours = (date - checkin_time).total_seconds() / 3600

    # Calculate expected shift hours
    if end_time < start_time:  # Shift spans across midnight
        shift_hours = (end_time + timedelta(days=1) - start_time).total_seconds() / 3600
    else:
        shift_hours = (end_time - start_time).total_seconds() / 3600

    # Validate checkout time
    if total_hours < shift_hours:
        return False, "Early CheckOut"

    return True, ""


# def validate_checkin_records(type, employee, date):
# 	settings = frappe.get_doc("Kace Settings", "Kace Settings")
# 	shift = frappe.db.get_value("Employee", employee, "default_shift")

# 	shift = frappe.get_doc("Shift Type", shift)

# 	# shift_start_time = datetime.combine(frappe.utils.getdate(), shift.start_time)
# 	# shift_end_time = datetime.combine(frappe.utils.getdate(), shift.end_time)

# 	shift_start_time = get_datetime(f"{getdate()} {shift.start_time}")
# 	shift_end_time = get_datetime(f"{getdate()} {shift.end_time}")

# 	if type == "OUT":
# 		checkin_record = frappe.db.sql(
# 			f"select name, time from `tabEmployee Checkin` where employee = '{employee}' and log_type = 'IN' order by time desc limit 1"
# 		)

# 		if not checkin_record:
# 			return (
# 				False,
# 				"Checkin record not found to validate this checkout record but attendance added",
# 			)

# 		checkin_time = checkin_record[0][1]
# 		diff = (date - checkin_time).total_seconds() / 3600

# 		if diff < cint(settings.min_hours) / 3600:
# 			return False, "Early Check Out"

# 		if (
# 			cint(shift.early_exit_grace_period)
# 			and shift_end_time + timedelta(minutes=cint(shift.early_exit_grace_period))
# 			< checkin_time
# 		):
# 			return (
# 				True,
# 				"Checkin time is greater than checkout time but attendance added",
# 			)
# 	elif type == "IN":
# 		if cint(shift.late_entry_grace_period) and date > shift_start_time + timedelta(
# 			minutes=cint(shift.late_entry_grace_period)
# 		):
# 			return True, "Late Attendance Marked"

# 	frappe.log_error("late attendance",f"{date} > {shift_start_time + timedelta(minutes=cint(shift.late_entry_grace_period)) }")
# 	return True, "Attendance Marked"


def validate_checkin_records(type, employee, date, checkin_time_only=None):
    settings = frappe.get_doc("Kace Settings", "Kace Settings")
    shift_name = frappe.db.get_value("Employee", employee, "default_shift")
    if not shift_name:
        return False, "Employee has no default shift assigned"

    shift = frappe.get_doc("Shift Type", shift_name)

    shift_start_time = get_datetime(f"{getdate()} {shift.start_time}")
    shift_end_time = get_datetime(f"{getdate()} {shift.end_time}")

    if type == "OUT":
        # Block checkout after the shift end time
        # if date > shift_end_time:
        #     return False, "Cannot check out after the shift end time"

        checkin_record = frappe.db.sql(
            "SELECT name, time FROM `tabEmployee Checkin` WHERE employee = '%s' AND log_type = 'IN' ORDER BY time DESC LIMIT 1"
            % employee,
        )

        if not checkin_record:
            return (
                False,
                "Checkin record not found to validate this checkout record, attendance cannot be added",
            )
        checkin_time = checkin_record[0][1]
        diff = (date - checkin_time).total_seconds() / 3600
        shift_end_time_formatted = get_time(shift.end_time)
        
        
        if checkin_time_only < shift_end_time_formatted:
            if diff < cint(settings.min_hours) / 3600:
                # my_custom_time = cint(settings.min_hours) / 3600
                return False, "Minimum working hours not met"
            return True, "Early Check Out"

        

        

        # Your original early exit grace period logic stays here
        if (
            cint(shift.early_exit_grace_period)
            and shift_end_time + timedelta(minutes=cint(shift.early_exit_grace_period))
            < checkin_time
        ):
            return (
                True,
                "Checkin time is greater than checkout time but attendance added",
            )

    elif type == "IN":
        if cint(shift.begin_check_in_before_shift_start_time):
            if shift_start_time > date and date > (
                shift_start_time - timedelta(minutes=cint(shift.begin_check_in_before_shift_start_time))
            ):
                return True, "Early Check In"
        
        if date > shift_end_time:
            return False, "Cannot check in after shift end time"
        
        if cint(shift.late_entry_grace_period) and date > (
            shift_start_time + timedelta(minutes=cint(shift.late_entry_grace_period))
        ):
            return True, "Late Arrival"

    return True, "Attendance added"


@frappe.whitelist(allow_guest=True)
def add_attendence():
    request_data = json.loads(frappe.request.data)
    user = get_user_details()

    if not request_data:
        frappe.response["message"] = "Data not found"
        return

    log_type = request_data.get("type")
    employee = user.get("employee")
    checkin_time = datetime.strptime(
        f"{request_data['date']} {request_data['time']}", "%Y-%m-%d %H:%M:%S"
    )
    checkin_time_only = get_time(request_data['time'])

    employee_default_shift = frappe.db.get_value("Employee", employee, "default_shift")

    if not employee_default_shift:
        frappe.response["message"] = "Add Employee Default Shift"
        return

    status, message = validate_checkin_records(log_type, employee, checkin_time, checkin_time_only)
    if not status:
        frappe.response["message"] = message
        return

    checkin_doc = frappe.new_doc("Employee Checkin")
    checkin_doc.employee = employee
    checkin_doc.log_type = log_type
    checkin_doc.time = checkin_time
    checkin_doc.custom_location_name = request_data.get("location_name")
    checkin_doc.device_id = request_data.get("location")
    checkin_doc.custom_latitude = request_data.get("latitude")
    checkin_doc.custom_longitude = request_data.get("longitude")
    checkin_doc.latitude = request_data.get("latitude")
    checkin_doc.logitude = request_data.get("longitude")
    checkin_doc.flags.ignore_permissions = True
    checkin_doc.save()

    if request_data.get("front_image"):
        file = save_file(
            request_data["front_image"]["name"],
            request_data["front_image"]["base64"],
            "Employee Checkin",
            checkin_doc.name,
            decode=True,
            is_private=0,
            df="custom_front_image",
        )
        frappe.db.set_value(
            "Employee Checkin", checkin_doc.name, {"custom_front_image": file.file_url}
        )

    if request_data.get("rear_image"):
        file = save_file(
            request_data["rear_image"]["name"],
            request_data["rear_image"]["base64"],
            "Employee Checkin",
            checkin_doc.name,
            decode=True,
            is_private=0,
            df="custom_rear_image",
        )

        frappe.db.set_value(
            "Employee Checkin", checkin_doc.name, {"custom_rear_image": file.file_url}
        )

    frappe.response["message"] = message or "Attendance added"
    frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def add_attendence_notification():
    request_data = None
    try:
        request_data = json.loads(frappe.request.data)
    except json.JSONDecodeError:
        request_data = None

    if not request_data:
        frappe.response["message"] = "Data not found, please provide valid json data"
        return

    user = get_user_details()
    if not request_data:
        frappe.response["message"] = "Data not found"
        return

    employee = user.get("employee") if user else request_data.get("employee")
    notification_time = datetime.strptime(
        f"{request_data['notification_time']}", "%Y-%m-%d %H:%M:%S"
    )

    allowed_difference_seconds = cint(
        frappe.db.get_value(
            "Kace Settings", "Kace Settings", "notification_checkin_time"
        )
    )

    time_to_diff = frappe.utils.now_datetime() + timedelta(
        seconds=allowed_difference_seconds
    )

    if notification_time > time_to_diff:
        frappe.response["message"] = "Notification time is in the past"
        frappe.response["status"] = "error"
        return

    checkin_doc = frappe.new_doc("Notification Checkin")
    checkin_doc.employee = employee
    checkin_doc.log_type = "IN"
    checkin_doc.time = frappe.utils.now_datetime()
    checkin_doc.location_name = request_data.get("location_name")
    checkin_doc.device_id = request_data.get("location")
    checkin_doc.latitude = request_data.get("latitude")
    checkin_doc.longitude = request_data.get("longitude")
    checkin_doc.flags.ignore_permissions = True
    checkin_doc.save()

    frappe.db.commit()
    frappe.response["message"] = "Attendance added"


@frappe.whitelist(allow_guest=True)
def add_attendence_kiosk():
    request_data = json.loads(frappe.request.data)
    # user = get_user_details()

    if not request_data:
        frappe.response["message"] = "Data not found"
        return

    log_type = request_data.get("type")
    employee = request_data.get("employee")
    checkin_time = datetime.strptime(
        f"{request_data['date']} {request_data['time']}", "%Y-%m-%d %H:%M:%S"
    )

    employee_default_shift = frappe.db.get_value("Employee", employee, "default_shift")

    if not employee_default_shift:
        frappe.response["message"] = "Add Employee Default Shift"
        return
    checkin_time_only = get_time(request_data['time'])


    status, message = validate_checkin_records(log_type, employee, checkin_time, checkin_time_only)
    if not status:
        frappe.response["message"] = message
        return

    checkin_doc = frappe.new_doc("Employee Checkin")
    checkin_doc.employee = employee
    checkin_doc.log_type = log_type
    checkin_doc.time = checkin_time
    checkin_doc.custom_location_name = request_data.get("location_name")
    checkin_doc.device_id = request_data.get("location")
    checkin_doc.custom_latitude = request_data.get("latitude")
    checkin_doc.custom_longitude = request_data.get("longitude")

    checkin_doc.flags.ignore_permissions = True
    checkin_doc.save()

    if request_data.get("front_image"):
        file = save_file(
            request_data["front_image"]["name"],
            request_data["front_image"]["base64"],
            "Employee Checkin",
            checkin_doc.name,
            decode=True,
            is_private=0,
            df="custom_front_image",
        )
        frappe.db.set_value(
            "Employee Checkin", checkin_doc.name, {"custom_front_image": file.file_url}
        )

    if request_data.get("rear_image"):
        file = save_file(
            request_data["rear_image"]["name"],
            request_data["rear_image"]["base64"],
            "Employee Checkin",
            checkin_doc.name,
            decode=True,
            is_private=0,
            df="custom_rear_image",
        )

        frappe.db.set_value(
            "Employee Checkin", checkin_doc.name, {"custom_rear_image": file.file_url}
        )

    frappe.response["message"] = message or "Attendance added"
    frappe.db.commit()