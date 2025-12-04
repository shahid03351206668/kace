frappe.ui.form.on('Notification Schedule', {
    refresh(frm) {
        // your code here
    },
    get_employee: function (frm) {
        let filters = {
            "employee": frm.doc.employee || null,
            "branch": frm.doc.branch || null,
            "designation": frm.doc.designation || null,
            "department": frm.doc.department || null
        };

        frappe.call({
            method: 'kace.kace.doctype.attendance_location.attendance_location.get_employee_data',
            freeze: true,
            args: { "filters": filters },
            callback: function (response) {
                if (response?.message) {
                    for (const row of response.message) {
                        // console.log(frm.doc?.item?.find(i => i.employee == row.employee))
                        if (!frm.doc?.employees?.find(i => i.employee == row.employee)) {
                            frm.add_child("employees", { "employee": row.employee });
                        }
                    }
                    frm.refresh_field("employees");
                }
            }
        });

    }
})