frappe.ui.form.on('Attendance Location', {
    refresh(frm) {},

    map(frm) {
        const { map } = frm.doc;
        try {
            const coordinates = JSON.parse(map).features[0].geometry.coordinates;
            const lat = coordinates[0];
            const lng = coordinates[1];

            frm.set_value("latitude", lat);
            frm.set_value("longitude", lng);

        } catch (error) {

        }
    },

    get_employees: function (frm) {
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
                        if (!frm.doc?.item?.find(i => i.employee == row.employee)) {
                            cur_frm.add_child("item", row);
                        }
                    }
                    frm.refresh_field("item");
                }
            }
        });
    }
});
