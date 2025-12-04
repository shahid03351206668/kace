frappe.ui.form.on('Kace Settings', {
	refresh(frm) {
		// your code here
	},
	send_notification(frm) {
		frappe.call({
			method: "kace.kace_notification.send_employee_checkin_notification",
			freeze: true,
			callback(r) {
				frappe.show_alert({
					message: __('Notification Sent'),
					indicator: 'green'
				});
			}
		})
	}
})

