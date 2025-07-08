import frappe


def main():
    frappe.enqueue(fix_states_enque, queue="long")

def fix_states_enque():
    docs = frappe.db.get_all("Sales Invoice")
    states = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    docs = frappe.db.get_all("Sales Invoice", fields=["name", "docstatus", "doc_status"])
    for d in docs:
        if d.doc_status != states.get(d.docstatus):
            doc = frappe.get_doc("Sales Invoice", d.name)
            doc.doc_status = states.get(doc.docstatus)
            doc.save()

# def submit_enque():
#     names = frappe.db.sql(
#         f"""  SELECT name FROM `tabSales Invoice` WHERE posting_date = '2024-08-31' AND docstatus = 0 """,
#         as_dict=True,
#     )

#     for name in names:
#         try:
#             sl_inv = frappe.get_doc("Sales Invoice", name.name)
#             sl_inv.submit()
#             frappe.db.commit()
#         except Exception as e:
#             frappe.log_error("invoice sumbittion error", e)
#             ...
