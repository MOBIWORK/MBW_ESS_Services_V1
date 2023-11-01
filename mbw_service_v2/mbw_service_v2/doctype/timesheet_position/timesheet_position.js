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
  
  frappe.ui.form.on("TimeSheet Position", {
	refresh: function (frm) {
	  setDefaultViewMap(frm);
	},
  
	map: async function (frm) {
	  let mapdata = JSON.parse(frm.doc.map).features[0];
	  if (mapdata && mapdata.geometry.type == "Point") {
		let lat = mapdata.geometry.coordinates[1];
		let lon = mapdata.geometry.coordinates[0];
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
		});
  
		setFieldValue(frm, lat, lon, address);
	  } else {
		setDefaultViewMap(frm);
		setFieldValue(frm);
	  }
	},
  });
  