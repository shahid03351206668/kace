frappe.ui.form.on("Attendance Request", {
    custom_map(frm) {
		const { custom_map } = frm.doc;
		try {
			const coordinates = JSON.parse(custom_map).features[0].geometry.coordinates;
			const lng = coordinates[0];  
			const lat = coordinates[1];  

			frm.set_value("custom_latitude", lat);
			frm.set_value("custom_longitude", lng);

		} catch (error) {
			console.error("Failed to parse map coordinates:", error);
		}
	}
});