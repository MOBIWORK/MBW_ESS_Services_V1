// Make sure we have a dictionary to add our custom settings
const map_settings = frappe.provide("frappe.utils.map_defaults");
// // Use a different map: satellite instead of streets
map_settings.center =  [105.777547,21.056248]
map_settings.tiles = "https://api.ekgis.vn/v2/maps/osmplus/{z}/{x}/{y}.pbf?api_key=wtpM0U1ZmE2s87LEZNSHf63Osc1a2sboaozCQNsy" ;
map_settings.options.attribution = "Tiles &copy; Esri &mdash; Source: Ekgis Community";
console.log("bbbbbbbb", "https://api.ekgis.vn/v2/maps/osmplus/{z}/{x}/{y}.pbf" );