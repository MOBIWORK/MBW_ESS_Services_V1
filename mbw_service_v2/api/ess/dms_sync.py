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
            'ESS Log', fields=['*'], page_length=20)
        result = {
            "data": list_sync
        }

        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])


import math
@frappe.whitelist(methods='GET')
def get_list_kpi_sync(**kwargs):
    try:
        pageSize = 20
        pageNumber = kwargs.get('page') if kwargs.get('page') else 1
        limit_start = (pageNumber - 1) * pageSize
        total_sync = frappe.db.count('ESS Kpi Log')
        total_page =  math.ceil(total_sync/20)
        list_sync = frappe.db.get_all(
            'ESS Kpi Log', fields=['*'],  limit_start=limit_start, limit_page_length=pageSize)
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": list_sync,
            "total_page": total_page
        })
    except Exception as e:
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])



@frappe.whitelist(methods="GET")
def total_bonus_kpi(**data):
    month = data.get("month")
    year = data.get("year")
    employee = data.get("employee")
    info_kpi = frappe.db.get_value("DMS KPI", {"employee": employee,"month": month,"year":year},["bonus_sales","bonus_kpi1"],as_dict=1)
    if info_kpi:
        return float(info_kpi.get("bonus_sales")) + float(info_kpi.get("bonus_kpi1"))
    else :
        return 0