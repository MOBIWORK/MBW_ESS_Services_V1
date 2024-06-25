// Make sure we have a dictionary to add our custom settings
const map_settings = frappe.provide("frappe.utils.map_defaults");
// // Use a different map: satellite instead of streets
map_settings.center =  [21.056248,105.777547]
map_settings.maxzoom =  14
map_settings.tiles = "https://api.ekgis.vn/v2/maps/raster/osm/bright/{z}/{x}/{y}.png?api_key=wtpM0U1ZmE2s87LEZNSHf63Osc1a2sboaozCQNsy" ;
map_settings.options.attribution = "Vector &copy; eKGis &mdash; Source: eKMap Service";