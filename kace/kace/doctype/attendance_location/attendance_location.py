# Copyright (c) 2025, CodesSoft and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document


class AttendanceLocation(Document):
    pass


@frappe.whitelist(allow_guest=True)
def get_employee_data(filters):
    if filters:
        filters = json.loads(filters)
    conditions = ""
    if filters.get("employee"):
        conditions += f""" and name = '{filters.get("employee")}' """

    if filters.get("designation"):
        conditions += f""" and designation = '{filters.get("designation")}' """

    if filters.get("branch"):
        conditions += f""" and branch = '{filters.get("branch")}' """

    if filters.get("department"):
        conditions += f""" and department = '{filters.get("department")}' """

    data = frappe.db.sql(
        f"""
		SELECT name as employee, employee_name,designation,department, branch
		FROM `tabEmployee` 
		WHERE status = 'Active'
		{conditions} """,
        as_dict=1,
        debug=True,
    )

    return data
