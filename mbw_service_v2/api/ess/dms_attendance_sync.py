import frappe
from mbw_service_v2.api.common import (
    gen_response,
    exception_handel,
    validate_image,
    BASE_URL,
    get_user_id,
    get_employee_by_user,

)
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from datetime import datetime
from pypika import Order, CustomFunction
import json


@frappe.whitelist(methods='GET')
def get_list_sync(**kwargs):
    try:
        list_sync = frappe.db.get_all(
            'DMS Log', fields=['*'], page_length=20)
        result = {
            "data": list_sync
        }

        message = "Thành công."
        gen_response(200, message, result)
    except Exception as e:
        print(e)
        message = "Có lỗi xảy ra"
        gen_response(500, message, [])
