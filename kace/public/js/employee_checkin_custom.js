
frappe.ui.form.on('Employee Checkin', {
    refresh(frm) {
        // frm.set_df_property("custom_map_location", "options", `<div style="width: 100%;"><iframe width="100%" height="600" frameborder="0" scrolling="no" marginheight="0"
        // marginwidth="0" src="https://maps.google.com/maps?width=100%25&amp;height=600&amp;hl=en&amp;q=${frm.doc.custom_latitude}, ${frm.doc.custom_longitude}&amp;t=&amp;z=14&amp;ie=UTF8&amp;iwloc=B&amp;output=embed"><a
        // href="https://www.gps.ie/">gps trackers</a></iframe></div>`)
        frappe.db.get_single_value(
            "HR Settings",
            "allow_geolocation_tracking",
        ).then(allow_geolocation_tracking => {
            if (!allow_geolocation_tracking) {
                hide_field(["fetch_geolocation", "custom_latitude", "custom_longitude", "geolocation"]);
                return;
            }
            show_field(["fetch_geolocation", "custom_latitude", "custom_longitude", "geolocation"]);
        });
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
    fetch_geolocation: (frm) => {
        hrms.fetch_geolocation(frm);
    },
    auto_fetch_geolocation(frm) {
        if(!frm.is_new() ) return;
        
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
                frm.set_value("geolocation", geojson);

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
})