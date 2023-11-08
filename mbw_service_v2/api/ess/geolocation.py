import frappe
from mbw_service_v2.utils import CONFIG_KEYS
import requests
from mbw_service_v2.api.common import (
    gen_response
)
import json


@frappe.whitelist(methods="GET", allow_guest=True)
def get_address_location(**kwargs):
    try:
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        api_key = CONFIG_KEYS.get("API_KEY_MAP")

        # call geolocation
        url = f"https://api.ekgis.vn/v1/place/geocode/reverse/address?latlng={lat},{lon}&gg=1&api_key={api_key}"

        response = requests.get(url)
        return gen_response(200, "", json.loads(response.text))
    except Exception as e:
        return e

@frappe.whitelist(methods="GET", allow_guest=True)
def get_coordinates_location(**kwargs):
    try:
        address = kwargs.get("address")
        api_key = CONFIG_KEYS.get("API_KEY_MAP")

        # call geolocation
        url = f"https://api.ekgis.vn/v1/place/geocode/forward?address={address}&gg=1&api_key={api_key}"
    
        response = requests.get(url)
        return gen_response(200, "", json.loads(response.text))
    except Exception as e:
        return e