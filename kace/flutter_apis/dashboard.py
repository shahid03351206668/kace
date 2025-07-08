import calendar
from calendar import monthrange
from datetime import datetime
from json import loads

import frappe
from frappe.utils import cint, cstr, flt, getdate

from .leave_application_custom import get_leave_details
from .main import create_log, get_date_time_to_use, get_user_details, make_response


def get_attendance_data(employee, st_date, ed_date):
    query_conds = f""" and  DATE(time) >= '{st_date}' and  DATE(time) <= '{ed_date}' """
    checkins = frappe.db.sql(
        f""" 
        select
            DATE (ec.time) as date,
            ec.employee,
            (
                select
                    time
                from
                    `tabEmployee Checkin`
                where
                    log_type = "IN"
                    and employee = ec.employee
                    and DATE (time) = DATE (ec.time)
                Order BY
                    time ASC
                limit
                    1
            ) as check_in,
            (
                select
                    time
                from
                    `tabEmployee Checkin`
                where
                    log_type = "OUT"
                    and employee = ec.employee
                    and DATE (time) = DATE (ec.time)
                Order BY
                    time DESC
                limit
                    1
            ) as check_out
        from
            `tabEmployee Checkin` ec
        where
            ec.employee = '{employee}'
            {query_conds}
        Group By
            DATE (ec.time),
            ec.employee
        Order By
            DATE (ec.time) DESC """,
        as_dict=1,
    )
    presents = len([i for i in checkins if i.get("check_in") or i.get("check_out")])

    response = {
        "Absent": len(checkins) - presents,
        "Present": presents,
        "Total": monthrange(
            cint(datetime.now().strftime("%Y")),
            cint(datetime.now().strftime("%m")),
        )[1],
    }

    # if st_date and ed_date:

    response["Absent"] = response["Total"] - response["Present"]

    return response


def get_tasks():
    if not frappe.has_permission("Task", "read"):
        return

    return frappe.get_list(
        "Task",
        filters=({"status": ["not in", ["Closed", "Cancelled"]]}),
        fields=[
            "creation",
            "priority",
            "name as id",
            "actual_time",
            "expected_time",
            "exp_end_date",
        ],
        order_by="creation desc",
        page_length=100,
    )


def get_employee_shift(user):
    shift = frappe.db.sql(
        f"""  SELECT start_time, end_time, name FROM `tabShift Type` where name = '{frappe.db.get_value("Employee",user.get("employee"), "default_shift")}' """,
        as_dict=True,
    )
    if shift:
        return shift[0]

    return {}


def get_attendances(user):
    if not frappe.has_permission("Attendance", "read"):
        return
    attendance_data = {
        "Work From Home": 0,
        "Half Day": 0,
        "On Leave": 0,
        "Absent": 0,
        "monthname": datetime.now().strftime("%B"),
        "no_of_days": monthrange(
            cint(datetime.now().strftime("%Y")),
            cint(datetime.now().strftime("%m")),
        )[1],
    }

    attendance_data.update(
        get_attendance_data(
            user.get("employee"),
            frappe.utils.get_first_day(frappe.utils.getdate()),
            frappe.utils.get_last_day(frappe.utils.getdate()),
        )
    )
    return attendance_data


def get_leaves(user):
    leaves = {}
    if not frappe.has_permission(
        "Leave Application", "read"
    ) or not frappe.has_permission("Leave Type", "read"):
        return

    leave_allocation = {}
    leave_data = get_leave_details(user.get("employee"), str(getdate()))

    if not leave_data:
        return leaves

    leave_allocation = leave_data.get("leave_allocation", {})
    for leave_type, leave_type_data in leave_allocation.items():
        if leave_type not in leaves:
            leaves[leave_type] = {
                "total_leaves": 0,
                "leaves_used": 0,
            }
        if leave_type_data:
            leaves[leave_type]["total_leaves"] += leave_type_data.get("total_leaves")
            leaves[leave_type]["leaves_used"] += leave_type_data.get("leaves_taken")

    leaves_data = [
        {
            "leave_type": key,
            "total_leaves": value.get("total_leaves"),
            "leaves_used": value.get("leaves_used"),
        }
        for key, value in leaves.items()
    ]

    return leaves_data


@frappe.whitelist(allow_guest=True)
def get_dashboard_data():
    user = get_user_details()
    datetime_object = get_date_time_to_use()

    if not user:
        frappe.local.response["http_status_code"] = 401
        return "Invalid User!"

    response_data = {
        "salary_details": None,
        "recent_checkin": None,
        "current_task": get_tasks(),
        "current_shift": get_employee_shift(user),
        "leaves_data": get_leaves(user),
        "attendence_graph_data": get_attendances(user),
        "employee_details": frappe.db.get_value(
            "Employee",
            user.get("employee"),
            [
                "employee_type",
                "face_image_registration",
                "face_registration_data",
            ],
            as_dict=True,
        ),
    }

    # Getting expense claim and salary slip details for the current month
    # if frappe.has_permission("Expense Claim", "read"):
    #     response_data["pending_request"] = frappe.db.sql(
    #         "select ec.name as id, ec.status, expense_date, ecd.description, ecd.expense_type, ecd.amount from `tabExpense Claim` ec inner join `tabExpense Claim Detail` ecd on ec.name = ecd.parent where ec.docstatus = 1 and MONTH (ec.posting_date) = %s AND ec.employee = %s",
    #         (datetime_object.month, user.get("employee")),
    #         as_dict=True,
    #     )

    if frappe.has_permission("Salary Slip", "read"):
        salary_details = frappe.get_list(
            "Salary Slip",
            filters={
                "employee": user.get("employee"),
            },
            fields=[
                "posting_date",
                "start_date",
                "total_working_days",
                "gross_pay",
                "net_pay",
                "payment_days",
                "company",
                "absent_days",
            ],
            order_by="start_date desc",
            limit=1,
        )
        for i in salary_details:
            currency_doc = frappe.get_doc(
                "Currency",
                frappe.db.get_value("Company", i.get("company"), "default_currency"),
            )
            i["currency"] = currency_doc.name
            i["currency_symbol"] = currency_doc.symbol

        response_data["salary_details"] = salary_details

        # Add month name to the result
        if response_data["salary_details"]:
            for slip in response_data["salary_details"]:
                slip["month_name"] = frappe.utils.formatdate(slip["start_date"], "MMMM")

    if frappe.has_permission("Employee Checkin", "read"):
        data = frappe.db.sql(
            "SELECT time, log_type FROM `tabEmployee Checkin` WHERE employee = %s ORDER BY time DESC LIMIT 1",
            (user.get("employee"),),
            as_dict=True,
        )

        if data:
            response_data["recent_checkin"] = data[0]

    frappe.response["data"] = response_data
    return

    try:
        user_details = get_user_details()
        if user_details:
            leaves = {}
            leave_allocation = {}
            leave_data = get_leave_details(user_details.employee, str(getdate()))

            if leave_data:
                leave_allocation = leave_data.get("leave_allocation", {})
                for leave_type, leave_type_data in leave_allocation.items():
                    if leave_type not in leaves:
                        leaves[leave_type] = {
                            "total_leaves": 0,
                            "leaves_used": 0,
                        }
                    if leave_type_data:
                        leaves[leave_type]["total_leaves"] += leave_type_data.get(
                            "total_leaves"
                        )
                        leaves[leave_type]["leaves_used"] += leave_type_data.get(
                            "leaves_taken"
                        )

            dt = get_date_time_to_use()
            month = dt.month

            data_get_dict = {
                "pending_request": f"""SELECT ec.name as id, ec.status,expense_date, ecd.description, ecd.expense_type,ecd.amount from `tabExpense Claim` ec inner join `tabExpense Claim Detail` ecd on ec.name = ecd.parent where ec.docstatus=1 and MONTH(ec.posting_date) = {month}  and employee = '{user_details.employee}' """,
                "salary_details": f"""SELECT MONTHNAME(posting_date) as month_name,total_working_days,gross_pay from `tabSalary Slip` where 1 = 1 and MONTH(posting_date) = {month}  and employee = '{user_details.employee}' """,
            }

            for field, query in data_get_dict.items():
                data = frappe.db.sql(query, as_dict=1, debug=True)
                data_get_dict[field] = data

            data_get_dict["current_task"] = frappe.db.get_list(
                "Task",
                fields=[
                    "creation",
                    "priority",
                    "name as id",
                    "actual_time",
                    "expected_time",
                    "exp_end_date",
                ],
                order_by="creation desc",
                page_length=100,
            )

            data_get_dict_counts = {
                "attendance_present": f"""SELECT COUNT(name)from `tabAttendance` where status = 'Present' and MONTH(attendance_date) = {month} """,
                "attendance_absent": f"""SELECT COUNT(name) from `tabAttendance` where status = 'Absent' and MONTH(attendance_date) = {month} """,
            }
            for field, query in data_get_dict_counts.items():
                data = frappe.db.sql(query)
                if data:
                    data_get_dict[field] = data[0][0]

            data_get_dict["leave_balance"] = [
                {
                    "leave_type": k,
                    "total_leaves": v.get("total_leaves"),
                    "leaves_used": v.get("leaves_used"),
                }
                for k, v in leaves.items()
            ]

            # count_data = (
            #     frappe.db.sql(
            #         f""" SELECT status, COUNT(name) as data_count FROM `tabAttendance` WHERE employee = '{user_details.get("employee")}'
            #         AND MONTHNAME(attendance_date) = '{datetime.now().strftime("%B")}'
            # 	GROUP BY status
            # 	""",
            #         as_dict=1,
            #     )
            #     or []
            # )

            graph_data = {
                "Work From Home": 0,
                "Half Day": 0,
                "On Leave": 0,
                "Absent": 0,
                "monthname": datetime.now().strftime("%B"),
                "no_of_days": monthrange(
                    cint(datetime.now().strftime("%Y")),
                    cint(datetime.now().strftime("%m")),
                )[1],
            }

            current_shift = frappe.db.sql(
                f"""  SELECT start_time, end_time,name  FROM `tabShift Type` where name = '{frappe.db.get_value("Employee",user_details.get("employee"), "default_shift")}' """,
                as_dict=True,
            )

            last_employee_checkin = frappe.db.sql(
                f""" SELECT time, log_type FROM `tabEmployee Checkin` WHERE employee = '{user_details.get("employee")}'
                    ORDER BY time DESC LIMIT 1
                 """,
                as_dict=True,
            )
            if last_employee_checkin:
                data_get_dict["recent_checkin"] = last_employee_checkin[0]

            if current_shift:
                data_get_dict["current_shift"] = current_shift[0]

            # for abc in count_data:
            #     graph_data[abc.status] = flt(abc.data_count)
            graph_data.update(
                get_attendance_data(
                    user_details.get("employee"),
                    frappe.utils.get_first_day(frappe.utils.getdate()),
                    frappe.utils.get_last_day(frappe.utils.getdate()),
                )
            )

            data_get_dict["attendence_graph_data"] = graph_data

            data_get_dict["employee_details"] = frappe.db.sql(
                f"""
                SELECT
                employee_type,
                face_verification,
                face_registration_data,
                face_image_registration,
                designation
                FROM
                `tabEmployee`
                WHERE name = '{user_details.get("employee")}'
                """,
                as_dict=True,
            )[0]
            # employee_details["employee_type"] = frappe.db.get_value(
            #     "Employee", user_details.get("employee"), "employee_type"
            # )
            # employee_details["face_verification"] = frappe.db.get_value(
            #     "Employee", user_details.get("employee"), "face_verification"
            # )
            # employee_details["face_registration_data"] = frappe.db.get_value(
            #     "Employee", user_details.get("employee"), "face_registration_data"
            # )
            # employee_details["face_image_registration"] = frappe.db.get_value(
            #     "Employee", user_details.get("employee"), "face_image_registration"
            # )

            # data_get_dict["employee_details"] = employee_details

            data_get_dict["job_applicant_permission"] = (
                "true" if frappe.has_permission("Job Applicant", "read") else "false"
            )

            make_response(success=True, data=data_get_dict)
        else:
            make_response(success=False, message="Invalid User!")
    except Exception as e:
        make_response(success=False, message=str(e))
