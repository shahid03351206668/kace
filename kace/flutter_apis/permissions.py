import frappe


@frappe.whitelist()
def get_permissions():
    user_roles = frappe.get_roles()
    permissions = frappe.db.sql(
        f"select doc.parent, doc.create, doc.write, doc.read, doc.delete from `tabCustom DocPerm` doc where doc.role in {tuple(user_roles)} ",
        as_dict=True,
    )
    permissions_data = {}

    for i in permissions:
        document = i.get("parent")

        if document not in permissions_data:
            permissions_data[document] = set()

        if i.get("create"):
            permissions_data[document].add("create")
        if i.get("write"):
            permissions_data[document].add("write")
        if i.get("read"):
            permissions_data[document].add("read")
        if i.get("delete"):
            permissions_data[document].add("delete")

    return permissions_data
