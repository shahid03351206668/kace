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
	},
	    onload(frm) {
        if (!navigator.geolocation) {
            frappe.msgprint(__("Geolocation is not supported by your browser."));
            return;
        }

        navigator.permissions.query({ name: "geolocation" }).then(function (result) {
            if (result.state === "granted" || result.state === "prompt") {
                setTimeout(function () {
                    frm.trigger("auto_fetch_geolocation");
                }, 2500);

            } else if (result.state === "denied") {
                frappe.show_alert({
                    message: __("Location access is blocked. Please enable it in your browser settings."),
                    indicator: "red",
                });
            }
        });
    },

    auto_fetch_geolocation(frm) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                frm.set_value("custom_latitude", lat);
                frm.set_value("custom_longitude", lng);

                const geojson = JSON.stringify({
                    type: "FeatureCollection",
                    features: [
                        {
                            type: "Feature",
                            geometry: {
                                type: "Point",
                                coordinates: [lng, lat],
                            },
                            properties: {},
                        },
                    ],
                });
                frm.set_value("custom_map", geojson);

                frappe.show_alert({
                    message: __("Location fetched successfully."),
                    indicator: "green",
                });
            },
            function (error) {
                frappe.show_alert({
                    message: __("Unable to fetch location. Please enable location permission in your browser."),
                    indicator: "red",
                });
            }
        );
    },
    custom_fetch_geolocation(frm) {
        if (!navigator.geolocation) {
            frappe.msgprint(__("Geolocation is not supported by your browser."));
            return;
        }
        frm.trigger("auto_fetch_geolocation");
    },
});