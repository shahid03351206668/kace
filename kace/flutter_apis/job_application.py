from json import loads

import frappe
from frappe.utils.file_manager import save_file

from .main import get_user_details


@frappe.whitelist()
def add_new_job_applicant():
    user_details = get_user_details()
    if not user_details:
        frappe.response["message"] = "Session User not found!"
        return

    try:
        data = loads(frappe.request.data)

        job_applicant_doc = frappe.new_doc("Job Applicant")
        job_applicant_doc.applicant_name = data.get("applicant_name")
        job_applicant_doc.email_id = data.get("email_address")
        job_applicant_doc.phone_number = data.get("phone_number")
        job_applicant_doc.job_title = data.get("job_opening")
        job_applicant_doc.designation = data.get("designation")
        job_applicant_doc.status = data.get("status") or "Open"
        job_applicant_doc.source = data.get("source")
        job_applicant_doc.cover_letter = data.get("cover_letter")

        job_applicant_doc.insert()

        if data.get("resume_file"):
            file_doc = save_file(
                data["resume_file"]["filename"],
                data["resume_file"]["base64"],
                "Job Applicant",
                job_applicant_doc.name,
                decode=True,
                is_private=1,
                df="resume_attachment",
            )

            job_applicant_doc.resume_attachment = file_doc.file_url
            job_applicant_doc.save()

        frappe.db.commit()
        frappe.response["success"] = True
        frappe.response["message"] = "Job Applicant has been created successfully!"
        frappe.response["data"] = job_applicant_doc.as_dict()

    except Exception as e:
        frappe.db.rollback()
        frappe.response["success"] = False
        frappe.response["message"] = str(e)


# @frappe.whitelist()
# def add_new_job_applicant():
#     user_details = get_user_details()
#     if not user_details:
#         frappe.response["message"] = "Session User not found!"
#         return
#
#     try:
#         # Handle form data
#         data = frappe.form_dict
#
#         # Create the Job Applicant document
#         job_applicant_doc = frappe.new_doc("Job Applicant")
#         job_applicant_doc.applicant_name = data.get("applicant_name")
#         job_applicant_doc.email_id = data.get("email_address")
#         job_applicant_doc.phone_number = data.get("phone_number")
#         job_applicant_doc.job_title = data.get("job_title")
#         job_applicant_doc.designation = data.get("designation")
#         job_applicant_doc.status = data.get("status") or "Open"
#         job_applicant_doc.source = data.get("source")
#         job_applicant_doc.cover_letter = data.get("cover_letter")
#
#         # Save the document first to generate ID
#         job_applicant_doc.insert()
#
#         # Handle file upload if resume is provided
#         if "resume_file" in frappe.request.files:
#             file_doc = frappe.get_doc(
#                 {
#                     "doctype": "File",
#                     "attached_to_doctype": "Job Applicant",
#                     "attached_to_name": job_applicant_doc.name,
#                     "attached_to_field": "resume_attachment",  # Specifying the field name
#                     "folder": "Home/Attachments",
#                     "file_name": frappe.request.files["resume_file"].filename,
#                     "is_private": 1,
#                     "content": frappe.request.files["resume_file"].read(),
#                 }
#             )
#             file_doc.save()
#
#             # Update the Job Applicant with the file URL
#             job_applicant_doc.resume_attachment = file_doc.file_url
#             job_applicant_doc.save()
#
#         frappe.db.commit()
#         frappe.response["success"] = True
#         frappe.response["message"] = "Job Applicant has been created successfully!"
#         frappe.response["data"] = job_applicant_doc.as_dict()
#
#     except Exception as e:
#         frappe.db.rollback()
#         frappe.response["success"] = False
#         frappe.response["message"] = str(e)
