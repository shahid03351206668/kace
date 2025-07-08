import frappe


def send_employee_checkin_notification():
    employee_data = frappe.db.sql(
        "select c.time, p.name as employee, p.user_id FROM `tabEmployee Notification Schedule` c INNER JOIN `tabEmployee` p ON c.parent = p.name WHERE time >= NOW() ",
        as_dict=True,
    )

    print(employee_data)
    # for i in employee_data:
    #     employee = i.get("employee")
    #     user_id = i.get("user_id")
    #     time = i.get("time")

    #     if time:
    #         time = time.split(":")
    #         hour = time[0]
    #         minute = time[1]
    #         frappe.enqueue(
    #             "kace_notification.send_notification",
    #             employee=employee,
    #             user_id=user_id,
    #             hour=hour,
    #             minute=minute,
    #             now=frappe.utils.now_datetime(),
    #             queue="long",
    #         )
