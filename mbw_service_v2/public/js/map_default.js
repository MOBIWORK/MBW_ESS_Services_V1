// Make sure we have a dictionary to add our custom settings
const map_settings = frappe.provide("frappe.utils.map_defaults");

// // Center and zoomlevel can be copied from the URL of
// // the map view at openstreetmap.org.

// // New default location (middle of germany).
map_settings.center = [105.777775,21.055938];
// // new zoomlevel: see the whole country, not just a single city
map_settings.zoom = 20;

// // Use a different map: satellite instead of streets
map_settings.tiles = "https://api.ekgis.vn/v2/maps/raster/osm/bright/{z}/{x}/{y}.png?api_key=wtpM0U1ZmE2s87LEZNSHf63Osc1a2sboaozCQNsy" ;
map_settings.options.attribution = "Tiles &copy; Esri &mdash; Source: Ekgis Community";