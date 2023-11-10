import frappe
from mbw_service_v2.api.common import (
    gen_response,
    exception_handel,
    validate_image,
    BASE_URL,
    get_user_id,
    get_employee_by_user,
    get_language
)
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from datetime import datetime
from pypika import Order, CustomFunction
import json
from mbw_service_v2.config_translate import i18n

@frappe.whitelist(methods='GET')
def get_list_sync(**kwargs):
    try:
        list_sync = frappe.db.get_all(
            'DMS Log', fields=['*'], page_length=20)
        result = {
            "data": list_sync
        }

        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
