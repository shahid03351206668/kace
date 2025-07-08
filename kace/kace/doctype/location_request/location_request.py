# Copyright (c) 2025, CodesSoft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LocationRequest(Document):

    def on_submit(self):
        attendance_location_doc = frappe.new_doc("Attendance Location")
        attendance_location_doc.location_name = self.location_name
        attendance_location_doc.longitude = self.longitude
        attendance_location_doc.latitude = self.latitude
        attendance_location_doc.meters = self.meters
        employee_list = {"employee": self.employee}
        attendance_location_doc.append("item", employee_list)
        attendance_location_doc.run_method("set_missing_values")
        attendance_location_doc.save()

        frappe.db.commit()
