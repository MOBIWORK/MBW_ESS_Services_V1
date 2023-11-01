from pypika import Query, Table, Field
from math import sin, cos, sqrt, atan2
import json
import os
import io
import calendar
import frappe
import json
from frappe import _

from mbw_service.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    distance_of_two,
    get_language,
    validate_image,
    valid_number
)

import requests
import base64
from datetime import datetime

from frappe.utils import get_files_path
from mbw_service.translations.language import translations

FIELDS_VALID = [
    {
        "key": "kpi_name",
        "type": str,
        "default": ""
    },
    {
        "key": "kpi_year",
        "type": int,
        "default": 0
    },
    {
        "key": "kpi_month",
        "type": int,
        "default": 0
    },
    {
        "key": "doanh_thu",
        "type": float,
        "default": 0
    },
    {
        "key": "doanh_thu",
        "type": float,
        "default": 0
    },
    {
        "key": "vieng_tham",
        "type": int,
        "default": 0
    }
]


@frappe.whitelist(methods="POST", allow_guest=True)
def insert(**kwargs):
    try:
        employee_id = kwargs.get('employee_id')
        check_employee = frappe.db.exists("Employee", employee_id)
        if not check_employee:
            return gen_response(status=404, message="Không tìm thấy mã nhân viên.", result=kwargs)

        # valid field
        for key in kwargs:
            if key in [item.get('key') for item in FIELDS_VALID if item.get('type' in [int, float])]:
                if not valid_number(kwargs[key]):
                    return gen_response(status=422, message=f"Trường {key} phải là số", result=kwargs)
                else:
                    type_field = next(
                        item for item in FIELDS_VALID if item["key"] == key).get('type')
                    kwargs[key] = type_field(kwargs[key])

        for field in FIELDS_VALID:
            key = field.get('key')
            if not kwargs.get(key):
                kwargs[key] = field.get("default")

        # them moi kpi
        doc_new = frappe.new_doc('KPI Integration Data')
        doc_new.parenttype = "Employee"
        doc_new.parentfield = "kpi_data"
        doc_new.parent = employee_id

        doc_new.kpi_name = kwargs.get("kpi_name")
        doc_new.kpi_year = kwargs.get("kpi_year")
        doc_new.kpi_month = kwargs.get("kpi_month")
        doc_new.doanh_thu = kwargs.get("doanh_thu")
        doc_new.doanh_so = kwargs.get("doanh_so")
        doc_new.vieng_tham = kwargs.get("vieng_tham")
        doc_new.insert(ignore_permissions=True)

        return gen_response(status=200, message="Thành công.", result=doc_new)
    except Exception as e:
        return gen_response(status=500, message=str(e), result={})
