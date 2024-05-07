// Copyright (c) 2023, chuyendev and contributors
// For license information, please see license.txt

function setDefaultViewMap(frm) {
  // set view map
  let map = frm.get_field("map").map;
  let longitude = frm.doc.longitude || 109.358;
  let latitude = frm.doc.latitude || 15.961;
  map.setView([latitude, longitude], 5);
}

function setFieldValue(frm, latitude = 0, longitude = 0, address) {
  frm.set_value("longitude", longitude);
  frm.set_value("latitude", latitude);
  frm.set_value("address", address);
}

frappe.ui.form.on("ESS ESS TimeSheet Position", {
  refresh: function (frm) {
    setDefaultViewMap(frm);
  },

  map: async function (frm) {
    let mapdata_point = JSON.parse(frm.doc.map)?.features;
    if (mapdata_point) {
      let last_point = mapdata_point[mapdata_point.length - 1];      
      if (last_point && last_point.geometry.type == "Point") {
        let lat = last_point.geometry.coordinates[1];
        let lon = last_point.geometry.coordinates[0];
        let address = "";

        await frappe.call({
          type: "GET",
          method: "mbw_service_v2.api.ess.geolocation.get_address_location",
          args: {
            lat: lat,
            lon: lon,
          },
          callback: function (r) {
            address = r.result.results;
          },
          error: function (xhr, textStatus, error) {
            // Xử lý lỗi
            frappe.msgprint({
              title: __("Error"),
              indicator: "red",
              message: __(xhr.responseJSON.message),
            });
          },
        });
        frm.set_value("map", JSON.stringify([last_point]));
        setFieldValue(frm, lat, lon, address);
      } else {
        setDefaultViewMap(frm);
        setFieldValue(frm);
      }
    }
  },
  address: async function (frm) {
    frm.fields_dict.address.$input.on("blur", async function () {
      let address_text = frm.doc.address;
      await frappe.call({
        type: "GET",
        method: "mbw_service_v2.api.ess.geolocation.get_coordinates_location",
        args: {
          address: address_text,
        },
        callback: function (r) {
          let rs = r.result.results;
          if (rs) {
            let {
              geometry: { location },
            } = rs[0];
            console.log("location", location);
            frm.set_value(
              "map",
              JSON.stringify([
                {
                  type: "Feature",
                  properties: {},
                  geometry: {
                    type: "Point",
                    coordinates: [location.lng, location.lat],
                  },
                },
              ])
            );
          }
        },
      });
    });
  },
});
