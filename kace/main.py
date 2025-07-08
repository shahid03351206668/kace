import frappe
from frappe.utils import cstr, get_first_day, getdate, add_to_date, today


def employee_checkin_custom(self):
    last_sync_of_checkin = None
    last_checkin_data = frappe.db.sql(
        f"""SELECT time, shift_actual_end FROM `tabEmployee Checkin` ORDER BY shift_actual_end DESC, time DESC LIMIT 1"""
    )
    if last_checkin_data:
        last_sync_of_checkin = last_checkin_data[0][1] or last_checkin_data[0][0]
    shift_type_records = frappe.db.get_all("Shift Type", pluck="name")
    for shift in shift_type_records:
        if last_sync_of_checkin:
            frappe.db.set_value(
                "Shift Type",
                shift,
                {
                    "last_sync_of_checkin": last_sync_of_checkin,
                    "process_attendance_after": get_first_day(last_sync_of_checkin),
                },
                update_modified=False,
            )
            frappe.db.commit()
        frappe.get_doc("Shift Type", shift).run_method('process_auto_attendance', date_to_check=getdate(self.time))

def employee_checkin_validate(self, method=None):
    employee_checkin_custom(self)

def employee_checkin_after_insert(self, method=None):
    employee_checkin_custom(self)


def update_employee_attendance():
    employees = frappe.db.get_all("Employee", pluck="name")
    date_to_check = add_to_date(today(), days=-1)
    if employees and date_to_check:
        for employee in employees:
            attendance_doc = frappe.db.sql(f"""SELECT name FROM `tabAttendance` Where docstatus = 1 AND employee = '{employee}' AND attendance_date = '{date_to_check}'""", as_dict=1)
            if not attendance_doc:
                new_attendance_record = frappe.new_doc("Attendance")
                new_attendance_record.employee = employee
                new_attendance_record.company = frappe.db.get_value("Employee", cstr(employee), "company")
                new_attendance_record.status = 'Absent'
                new_attendance_record.attendance_date = date_to_check
                new_attendance_record.flags.ignore_permissions=True
                new_attendance_record.save()
                new_attendance_record.submit()
