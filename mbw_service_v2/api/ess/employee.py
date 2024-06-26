from pypika import Query, Table, Field
from math import sin, cos, sqrt, atan2
import json
import os
import io
import calendar
import frappe
import json
from frappe import _

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    distance_of_two,
    get_language,
    validate_image
)

import requests
import base64
from datetime import datetime
from frappe.core.doctype.file.utils import delete_file
from frappe.utils.file_manager import (
    save_file, save_file_on_filesystem
)
from frappe.utils import get_files_path

from mbw_service_v2.config_translate import i18n


# Take employee timekeeping for a period of time
@frappe.whitelist()
def get_list_cham_cong(**kwargs):
    try:
        kwargs = frappe._dict(kwargs)
        my_filter = {}
        start_time = datetime.fromtimestamp(int(kwargs.get('start_time')))
        end_time = datetime.fromtimestamp(int(kwargs.get('end_time')))
        if start_time and end_time:
            my_filter["time"] = ['between', [start_time, end_time]]
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 0 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page')) - 1
        start = page * page_size

        EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
        ShiftType = frappe.qb.DocType("Shift Type")

        shift_type = (frappe.qb.from_(EmployeeCheckin)
                      .inner_join(ShiftType)
                      .on(EmployeeCheckin.shift == ShiftType.name)
                      .where((EmployeeCheckin.time >= start_time) & (EmployeeCheckin.time <= end_time))
                      .select(EmployeeCheckin.shift, EmployeeCheckin.log_type, EmployeeCheckin.time, EmployeeCheckin.device_id, ShiftType.start_time, ShiftType.end_time).run(as_dict=True)
                      )
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), shift_type)
    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# list of applications from employees
@frappe.whitelist()
def get_list_don_tu(**kwargs):
    try:
        kwargs = frappe._dict(kwargs)
        my_filter = {}
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        if start_time:
            my_filter["from_date"] = ['>=', start_time]
        if end_time:
            my_filter["to_date"] = ['<=', end_time]
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 0 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page')) - 1
        start = page * page_size

        leave_allocation = frappe.db.get_list('Leave Allocation',
                                              filters=my_filter,
                                              fields=[
                                                  'employee_name', 'leave_type', 'docstatus', 'from_date', 'to_date'],
                                              order_by='from_date desc',
                                              start=start,
                                              page_length=page_size,
                                              )
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), leave_allocation)
    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# List of employees
@frappe.whitelist(methods='GET')
def get_list_employee(**kwargs):
    try:
        page_size = 20 if not kwargs.get('page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        query_filter = {'status': 'Active'}
        total_doc = frappe.db.count('Employee', {"status": "Active"})
        
        print(query_filter,query_filter)
        list_employee = frappe.db.get_list(
            'Employee',
            filters=query_filter,
            fields={'name', 'employee_name', 'designation', "image",
                    'cell_number', 'user_id as email', 'UNIX_TIMESTAMP(date_of_birth) as date_of_birth'},
            start=start,
            page_length=page_size,
            ignore_permissions=True
        )

        for doc in list_employee:
            user_image = doc.get('image')
            doc['image'] = validate_image(user_image)

        result = {
            "data": list_employee,
            "total_doc": total_doc
        }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        return e
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# application details from staff
@frappe.whitelist(methods='GET')
def get_don_chi_tiet(name):
    data = frappe.get_doc('Leave Allocation', name
                          )
    gen_response(200, i18n.t('translate.successfully', locale=get_language()), data)


# Get employee information
@frappe.whitelist()
def get_info_employee():
    try:
        name = get_employee_id()
        info = frappe.db.get_value("Employee", name, ['*'], as_dict=1)
        time_now = datetime.now()
        EmployeeCheckin = frappe.qb.DocType('Employee Checkin')
        ShiftType = frappe.qb.DocType('Shift Type')
        ShiftAssignment = frappe.qb.DocType('Shift Assignment')

        last_checkin = (frappe.qb.from_()

                        )

        last_checkin_type = frappe.get_last_doc("Employee Checkin")
        info['shift_status'] = last_checkin_type.get(
            'log_type') if last_checkin_type else "OUT"
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), info)

    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# Timekeeping service
@frappe.whitelist()
def checkin_shift(**data):
    try:
        employee = get_employee_id()
        time_check = datetime.strptime(
            data.get('time'), "%Y-%m-%d %H:%M:%S").time()

        new_check = frappe.new_doc("Employee Checkin")
        data["device_id"] = json.dumps({"longitude": data.get(
            "longitude"), "latitude": data.get("latitude")})
        for field, value in dict(data).items():
            setattr(new_check, field, value)
        new_check.insert()
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), new_check)
    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        frappe.clear_messages()
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
