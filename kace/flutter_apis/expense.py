import re
from datetime import datetime

# from frappe.utils import Z
from json import loads

import frappe
from frappe.utils import cint, cstr, flt, getdate, pretty_date

from .main import create_log, get_user_details, make_response


@frappe.whitelist()
def get_notifications_log():
    try:
        frappe.clear_cache()
        user_details = get_user_details()
        if not user_details:
            return make_response(success=False, message="Invalid user!")

        user_name = user_details.get("name")
        notifications = frappe.db.sql(
            """
            SELECT
                name,
                subject,
                email_content,
                creation
            FROM
                `tabNotification Log` 
            WHERE
                (from_user = %s or for_user = %s)
            ORDER BY
                creation DESC
            LIMIT 1""",
            (user_name, user_name),
            as_dict=True,
        )

        TAG_RE = re.compile(r"<[^>]+>")
        for row in notifications:
            row["creation"] = row["creation"].strftime("%Y-%m-%d %H:%M:%S")
            row["subject"] = TAG_RE.sub("", cstr(row["subject"]))
            row["message"] = TAG_RE.sub("", cstr(row["email_content"]))

        return notifications
    except Exception as e:
        frappe.log_error("Notification Failed", str(e))
        return make_response(success=False, message="Failed to fetch notifications")


@frappe.whitelist()
def get_expenses():
    try:
        user_details = get_user_details()
        if user_details:
            parent_data = (
                frappe.get_list(
                    "Expense Claim",
                    fields=[
                        "name as id",
                        "employee",
                        "status",
                    ],
                    filters={"employee": user_details.get("employee")},
                    order_by="creation desc",
                )
                or []
            )
            if parent_data:
                expense_claim = {row.get("id"): row for row in parent_data}
                expense_detail = "','".join(list(expense_claim.keys()))
                expense_details_data = frappe.db.sql(
                    f"""SELECT idx, parent, expense_date, expense_type,
					description, amount from `tabExpense Claim Detail` WHERE 
					parent in ('{expense_detail}') order by idx""",
                    as_dict=1,
                    debug=1,
                )
                # deductions_data = frappe.db.sql(
                # 	f"""SELECT idx, parent, amount,salary_component, parentfield from `tabSalary Detail` WHERE parentfield = 'deductions' and
                # 	parent in ('{salary_slip_detail}') order by idx""",
                # 	as_dict=1,
                # )
                for ch in expense_details_data:
                    row = expense_claim.get(ch.parent, {})
                    if row:
                        if not row.get("expense_details"):
                            row["expense_details"] = []
                        row["expense_details"].append(ch)

                make_response(
                    success=True, data=[row for name, row in expense_claim.items()]
                )
            else:
                make_response(success=False, message="No Expense Claim Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
        # for ch in deductions_data:
        # 	row = salary_slip.get(ch.parent, {})
        # 	if row:
        # 		if not row.get("deductions"):
        # 			row["deductions"] = []
        # 		row["deductions"].append(ch)


@frappe.whitelist()
def add_expense():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.request.data
            if data:
                data = loads(data)
                ec = frappe.new_doc("Expense Claim")
                ec.employee = user_details.get("employee")
                ec.approval_status = data.get("approval_status")
                ec.status = data.get("status")
                for row in data.get("expenses", []):
                    ec.append("expenses", row)
                ec.run_method("set_missing_values")
                ec.save()
                ec.submit()
                frappe.db.commit()
                make_response(success=True, data={"id": ec.name})
            else:
                make_response(success=False, message="Data not Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
