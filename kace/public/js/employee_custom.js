frappe.ui.form.on('Employee', {
    onload(frm) {
        set_face_verification_default(frm);
    },
    refresh(frm) {
        create_custom_button(frm)
        frm.add_custom_button("Verify Face", function () {
            const dialog = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Message',
                        fieldname: 'message',
                        fieldtype: 'Small Text'
                    },
                ],
                size: 'small',
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.dom.freeze()
                    frappe.db.insert({
                        doctype: "Face Verification",
                        employee: frm.doc.name,
                        ...values
                    }).then((res) => {
                        frappe.dom.unfreeze();
                        frappe.show_alert({
                            message: __('Face verification send successfully'),
                            indicator: 'green'
                        }, 5);
                        dialog.hide();
                    }).catch((error) => {
                        console.error(error)
                        frappe.dom.unfreeze();
                    })
                }
            });

            dialog.show();

        })
    }
})


function set_face_verification_default(frm) {
    frappe.db.get_single_value('Kace Settings', 'default_face_verification').then(value => {
        if (value) {
            frm.set_value('face_verification', value);
        }
    });
}


function create_custom_button(frm) {
    frm.add_custom_button('Send Alert', () => {
        frappe.call({
            method: "kace.kace_notification.send_notification",
            freeze: true,
            args: { "user_id": frm.doc.user_id },
            callback: function (res) {
                frappe.show_alert({
                    message: __('Notification alert send successfully'),
                    indicator: 'green'
                }, 5);
            }
        })
    })
}