import frappe
from frappe import _
from frappe.utils import cint, cstr
from itertools import groupby
from hrms.hr.doctype.shift_type.shift_type import ShiftType
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	skip_attendance_in_checkins,
	update_attendance_in_checkins,
	handle_attendance_exception,
)

def get_existing_day_attendance(employee, attendance_date):
	attendance_name = frappe.db.exists(
		"Attendance",
		{
			"employee": employee,
			"attendance_date": attendance_date,
		},
	)

	if attendance_name:
		attendance_doc = frappe.get_doc("Attendance", attendance_name)
		return attendance_doc
	return None

def mark_attendance_and_link_log(
	logs,
	attendance_status,
	attendance_date,
	working_hours=None,
	late_entry=False,
	early_exit=False,
	in_time=None,
	out_time=None,
	shift=None,
):
	"""Creates an attendance and links the attendance to the Employee Checkin.
	Note: If attendance is already present for the given date, the logs are marked as skipped and no exception is thrown.

	:param logs: The List of 'Employee Checkin'.
	:param attendance_status: Attendance status to be marked. One of: (Present, Absent, Half Day, Skip). Note: 'On Leave' is not supported by this function.
	:param attendance_date: Date of the attendance to be created.
	:param working_hours: (optional)Number of working hours for the given date.
	"""
	log_names = [x.name for x in logs]
	employee = logs[0].employee
	if attendance_status == "Skip":
		# skip_attendance_in_checkins(log_names)
		return None

	elif attendance_status in ("Present", "Absent", "Half Day"):
		try:
			frappe.db.savepoint("attendance_creation")
			if attendance := get_existing_day_attendance(employee, attendance_date):
				frappe.db.set_value(
					"Attendance",
					attendance.name,
					{
						"working_hours": working_hours,
						"shift": shift,
						"late_entry": late_entry,
						"early_exit": early_exit,
						"in_time": in_time,
						"out_time": out_time,
						"status": attendance_status,
						"half_day_status": "Absent" if attendance_status == "Half Day" else None,
						"modify_half_day_status": 0,
					},
				)
			else:
				attendance = frappe.new_doc("Attendance")
				attendance.update(
					{
						"doctype": "Attendance",
						"employee": employee,
						"attendance_date": attendance_date,
						"status": attendance_status,
						"working_hours": working_hours,
						"shift": shift,
						"late_entry": late_entry,
						"early_exit": early_exit,
						"in_time": in_time,
						"out_time": out_time,
						"half_day_status": "Absent" if attendance_status == "Half Day" else None,
					}
				)
				attendance.flags.ignore_permissions = True
				attendance.submit()
			if attendance_status == "Absent":
				attendance.add_comment(
					text=_("Employee was marked Absent for not meeting the working hours threshold.")
				)
			update_attendance_in_checkins(log_names, attendance.name)
			return attendance
		except frappe.ValidationError as e:
			handle_attendance_exception(log_names, e)
	else:
		frappe.throw(_("{} is an invalid Attendance Status.").format(attendance_status))



class ShiftTypeCustom(ShiftType):
	def get_employee_checkins(self, date_to_check=None):
		process_attendance_after = cstr(self.process_attendance_after)
		if date_to_check:
			process_attendance_after = f"{date_to_check} 00:00:00"
		last_sync_of_checkin = cstr(self.last_sync_of_checkin)
		if date_to_check:
			last_sync_of_checkin = f"{date_to_check} 23:59:59"
		return (
			frappe.db.get_all(
				"Employee Checkin",
				fields=[
					"name",
					"employee",
					"log_type",
					"time",
					"shift",
					"shift_start",
					"shift_end",
					"shift_actual_start",
					"shift_actual_end",
					"device_id",
				],
				filters={
					# "skip_auto_attendance": 0,
					# "attendance": ("is", "not set"),
					"time": (">=", process_attendance_after),
					"shift_actual_end": ("<", last_sync_of_checkin),
					"shift": self.name,
					"offshift": 0,
				},
				order_by="employee,time",
			)
			or []
		)

	@frappe.whitelist()
	def process_auto_attendance(self, date_to_check=None):
		if (
			not cint(self.enable_auto_attendance)
			or not self.process_attendance_after
			or not self.last_sync_of_checkin
		):
			return
		logs = self.get_employee_checkins(date_to_check)
		group_key = lambda x: (x["employee"], x["shift_start"])  # noqa
		for key, group in groupby(sorted(logs, key=group_key), key=group_key):
			single_shift_logs = list(group)
			attendance_date = key[1].date()
			employee = key[0]
			if not self.should_mark_attendance(employee, attendance_date):
				continue

			(
				attendance_status,
				working_hours,
				late_entry,
				early_exit,
				in_time,
				out_time,
			) = self.get_attendance(single_shift_logs)
			mark_attendance_and_link_log(
				single_shift_logs,
				attendance_status,
				attendance_date,
				working_hours,
				late_entry,
				early_exit,
				in_time,
				out_time,
				self.name,
			)
		# commit after processing checkin logs to avoid losing progress
		frappe.db.commit()  # nosemgrep
		# assigned_employees = self.get_assigned_employees(self.process_attendance_after, True)
		# # mark absent in batches & commit to avoid losing progress since this tries to process remaining attendance
		# # right from "Process Attendance After" to "Last Sync of Checkin"
		# for batch in create_batch(assigned_employees, EMPLOYEE_CHUNK_SIZE):
		# 	for employee in batch:
		# 		self.mark_absent_for_dates_with_no_attendance(employee)
		# 		self.mark_absent_for_half_day_dates(employee)

		# 	frappe.db.commit()  # nosemgrep
