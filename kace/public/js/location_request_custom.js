frappe.ui.form.on('Location Request', {
	refresh(frm) {
	    frm.set_df_property("map_html", "options", `<div style="width: 100%;"><iframe width="100%" height="600" frameborder="0" scrolling="no" marginheight="0"
                    marginwidth="0"
                    src="https://maps.google.com/maps?width=100%25&amp;height=600&amp;hl=en&amp;q=${frm.doc.latitude}, ${frm.doc.longitude}&amp;t=&amp;z=14&amp;ie=UTF8&amp;iwloc=B&amp;output=embed"><a
                        href="https://www.gps.ie/">gps trackers</a></iframe></div>`)

		// your code here
	}
})