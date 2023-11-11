import frappe
from mbw_service_v2.utils import CONFIG_GEO_ADDRESS, CONFIG_GEO_LOCATION
import requests
from mbw_service_v2.api.common import (
    gen_response,
    get_language
)
import json
from mbw_service_v2.config_translate import i18n


@frappe.whitelist(methods="GET", allow_guest=True)
def get_address_location(**kwargs):
    try:
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        settings = frappe.db.get_singles_dict("MBW Employee Settings")
        geo_service = settings.get("geo_service")

        if geo_service == "Ekgis" : 
            key = settings.get("api_key_ekgis")
            url = f"{CONFIG_GEO_LOCATION.get('EKGIS')}?latlng={lat},{lon}&gg=1&api_key={key}"
        else :
            key = settings.get("api_key_google")
            url = f"{CONFIG_GEO_LOCATION.get('GOOGLE')}?latlng={lat},{lon}&gg=1&api_key={key}"
        
        # call geolocation
        response = requests.get(url)
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), json.loads(response.text))
    except Exception as e:
        return e

@frappe.whitelist(methods="GET", allow_guest=True)
def get_coordinates_location(**kwargs):
    try:
        address = kwargs.get("address")
        settings = frappe.db.get_singles_dict("MBW Employee Settings")
        geo_service = settings.get("geo_service")

        if geo_service == "Ekgis" : 
            key = settings.get("api_key_ekgis")
            url = f"{CONFIG_GEO_ADDRESS.get('EKGIS')}?address={address}&gg=1&api_key={key}"
        else :
            key = settings.get("api_key_google")
            url = f"{CONFIG_GEO_ADDRESS.get('GOOGLE')}?address={address}&gg=1&api_key={key}"
        response = requests.get(url)
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), json.loads(response.text))
    except Exception as e:
        return e