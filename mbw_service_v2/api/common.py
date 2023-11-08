from math import sin, cos, sqrt, atan2
import json
import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import cstr
import urllib.parse
import http.cookies
from datetime import datetime, timedelta
import base64
from frappe.core.doctype.file.utils import delete_file
from frappe.utils.file_manager import (
    save_file
)
from frappe.desk.query_report import (
    normalize_result, get_report_result, get_reference_report)
from frappe.core.utils import ljust_list
from pypika import Query, Table, Field, Order
import array

BASE_URL = frappe.utils.get_request_site_address()





# ==================================================================================================
ShiftType = frappe.qb.DocType('Shift Type')
ShiftAssignment = frappe.qb.DocType('Shift Assignment')
# lấy ca hiện tại và trạng thái của nó


def get_shift_type_now(employee_name):
    time_now = datetime.now()

    shift_type_now = today_list_shift(employee_name, time_now)
    shift_status = "Bạn không có ca hôm nay"
    time_query = time_now.replace(hour=0, minute=0, second=0)
    time_query_next_day =  time_now.replace(hour=23, minute=59, second=59)
    if len(shift_type_now) > 0:
        EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
        last_checkin_today = (frappe.qb.from_(EmployeeCheckin)
                              .limit(4)
                              .where((EmployeeCheckin.time >= time_query) & (EmployeeCheckin.time <= time_query_next_day))
                              .orderby(EmployeeCheckin.time,order= Order.desc)
                              .select('*')
                              .run(as_dict=True))
        if not last_checkin_today or last_checkin_today[0].get("log_type") == "OUT":
            shift_type_now = shift_now(employee_name, time_now)
            shift_status = False
        else:
            shift_type_now = frappe.db.get_value('Shift Type', {"name": last_checkin_today[0].get(
                "shift")}, ["name", "start_time", "end_time","allow_check_out_after_shift_end_time", "begin_check_in_before_shift_start_time"], as_dict=1)
            shift_status = last_checkin_today[0].get("log_type")
            pass

    else:
        shift_type_now = False
    return {
        "shift_type_now": shift_type_now,
        "shift_status": shift_status
    }

# lấy danh sách ca theo từng ngày


def today_list_shift(employee_name, time_now):
    query = (ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date)
    if not ShiftAssignment.end_date.isnull() :
        query = (ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date) & (time_now.date() <= ShiftAssignment.end_date)
    return (frappe.qb.from_(ShiftType)
            .inner_join(ShiftAssignment)
            .on(ShiftType.name == ShiftAssignment.shift_type)
            .where(((ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date) )or ((ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date) & (ShiftAssignment.start_date == None) ))
            .select(ShiftAssignment.employee, ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
            .run(as_dict=True)
            )

def inshift(employee_name,time_now) :
    data = (frappe.qb.from_(ShiftType)
                      .inner_join(ShiftAssignment)
                      .on(ShiftType.name == ShiftAssignment.shift_type)
                      .where(
                          (ShiftAssignment.employee == employee_name) & 
                          (time_now.time() >= ShiftType.start_time) & 
                          (time_now.time() <= ShiftType.end_time) & 
                            (
                                ((time_now.date() >= ShiftAssignment.start_date) & (time_now.date() <= ShiftAssignment.end_date)) |
                                ((time_now.date() >= ShiftAssignment.start_date) | (ShiftAssignment.end_date == False))
                            )
                             )
                      .select(ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                      .run(as_dict=True)
                )
    print("trong ca",data)
    if len(data) == 0:
        return False
    return data[0]

    
def nextshift(employee_name,time_now) :
    data = (frappe.qb.from_(ShiftType)
                        .inner_join(ShiftAssignment)
                        .on(ShiftType.name == ShiftAssignment.shift_type)
                        .where((ShiftAssignment.employee == employee_name) & (time_now.time() <= ShiftType.start_time) & (time_now.date() >= ShiftAssignment.start_date) & (time_now.date() <= ShiftAssignment.end_date))
                        .select(ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                        .run(as_dict=True)
                        )
    print("ca tiep",data)
    if len(data) == 0:
        return False
    return data[0]


def shift_now(employee_name, time_now):
    in_shift = inshift(employee_name, time_now)

    if not in_shift:
        next_shift = nextshift(employee_name, time_now)
        if not next_shift:
            return False
        return next_shift
    return in_shift


# ======================================================================================


# lấy báo cáo nhân viên

def get_report_doc(report_name):
    doc = frappe.get_doc("Report", report_name)
    doc.custom_columns = []
    doc.custom_filters = []

    if doc.report_type == "Custom Report":
        custom_report_doc = doc
        doc = get_reference_report(doc)
        doc.custom_report = report_name
        if custom_report_doc.json:
            data = json.loads(custom_report_doc.json)
            if data:
                doc.custom_columns = data.get("columns")
                doc.custom_filters = data.get("filters")
        doc.is_custom_report = True

    if not doc.is_permitted():
        gen_response(403, "You don't have access to Report " + report_name, [])

    if not frappe.has_permission(doc.ref_doctype, "report"):
        gen_response(403, "You don't have permission", [])
    return doc


# Tính khoảng cách giữa hai vị trí
R = 6373.0

from geopy.distance import great_circle
def distance_of_two(long_client, lat_client, long_compare, lat_compare):
    point1 = ( lat_client,long_client)
    point2 = (lat_compare,long_compare)
    return great_circle(point1, point2).meters

# định nghĩa trả về


def gen_response(status, message, result=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(
            str(message), features="lxml").get_text()
    else:
        frappe.response["message"] = message
    frappe.response["result"] = result


def exception_handel(e):
    frappe.log_error(title="ESS Mobile App Error",
                     message=frappe.get_traceback())
    if hasattr(e, "http_status_code"):
        return gen_response(e.http_status_code, cstr(e))
    else:
        return gen_response(500, cstr(e))


def generate_key(user):
    user_details = frappe.get_doc("User", user)
    api_secret = api_key = ""
    if not user_details.api_key and not user_details.api_secret:
        api_secret = frappe.generate_hash(length=15)
        # if api key is not set generate api key
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
        user_details.api_secret = api_secret
        user_details.save(ignore_permissions=True)
    else:
        api_secret = user_details.get_password("api_secret")
        api_key = user_details.get("api_key")
    return {"api_secret": api_secret, "api_key": api_key}


def get_employee_by_user(user, fields=["name"]):
    if isinstance(fields, str):
        fields = [fields]
    emp_data = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        fields,
        as_dict=1,
    )
    return emp_data


def get_employee_by_name(name, fields=["name"]):
    if isinstance(fields, str):
        fields = [fields]
    emp_data = frappe.db.get_value(
        "Employee",
        {"name": name},
        fields,
        as_dict=1,
    )
    return emp_data


def validate_employee_data(employee_data):
    if not employee_data.get("company"):
        return gen_response(
            500,
            "Company not set in employee doctype. Contact HR manager for set company",
        )


def get_user_id():
    headers = frappe.local.request.headers.get("Authorization")
    usrPass = headers.split(" ")[1]
    str_b64Val = base64.b64decode(usrPass).decode('utf-8')
    list_key = str_b64Val.split(':')
    api_key = list_key[0]
    user_id = frappe.db.get_value('User', {"api_key": api_key})
    return user_id


def get_employee_id():
    try:
        user_id = get_user_id()
        return get_employee_by_user(user_id).get("name")
    except:
        return ""


def get_ess_settings():
    return frappe.get_doc(
        "Employee Self Service Settings", "Employee Self Service Settings"
    )


def get_global_defaults():
    return frappe.get_doc("Global Defaults", "Global Defaults")


def remove_default_fields(data):
    # Example usage:
    # remove_default_fields(
    #     json.loads(
    #         frappe.get_doc("Address", "name").as_json()
    #     )
    # )
    for row in [
        "owner",
        "creation",
        "modified",
        "modified_by",
        "docstatus",
        "idx",
        "doctype",
        "links",
    ]:
        if data.get(row):
            del data[row]
    return data


def prepare_json_data(key_list, data):
    return_data = {}
    for key in data:
        if key in key_list:
            return_data[key] = data.get(key)
    return return_data


def get_info_employee(name, fields=['*']):
    info = frappe.db.get_value("Employee", name, fields, as_dict=1)
    shift_type_now = get_shift_type_now(info.get('employee'))
    info['shift'] = shift_type_now
    return info


def get_language():
    lang_ = frappe.local.request.headers.get("Language")
    lang = "vi" if not lang_ else lang_

    return lang


def post_image(name_image, faceimage, doc_type, doc_name):
    # save file and insert Doctype File
    file_name = name_image + "_" + str(datetime.now()) + "_.png"
    imgdata = base64.b64decode(faceimage)

    doc_file = save_file(file_name, imgdata, doc_type, doc_name,
                         folder=None, decode=False, is_private=0, df=None)

    # delete image copy
    path_file = "/files/" + file_name
    delete_file(path_file)
    file_url = BASE_URL + doc_file.get('file_url')
    return file_url


@frappe.read_only()
def generate_report_result(
        report, filters=None, user=None, custom_columns=None, is_tree=False, parent_field=None
):
    user = user or frappe.session.user
    filters = filters or []

    if filters and isinstance(filters, str):
        filters = json.loads(filters)

    res = get_report_result(report, filters) or []

    columns, result, message, chart, report_summary, skip_total_row = ljust_list(
        res, 6)

    report_column_names = [col["fieldname"] for col in columns]

    # convert to list of dicts
    result = normalize_result(result, columns)

    return result


def get_info_user():
    employee = get_employee_by_name(get_employee_id(), ['user_id'])
    user = frappe.get_doc('User', employee.get('user_id'))
    return user


def validate_image(user_image):
    if user_image and "http" not in user_image:
        user_image = BASE_URL + user_image
    return user_image


def validate_datetime(date_text):
    try:
        date = datetime.fromtimestamp(int(date_text)).date()
        return date
    except ValueError:
        raise ValueError("Incorrect date format, should be int")


def validate_empty(string):
    return (string and string.strip())


def delta_to_time_now(time):
    time_now = datetime.now()
    total_second = time.total_seconds()
    hour = int(total_second/3600)
    minute = int((total_second - hour*3600)/60)
    second = int(total_second - hour*3600 - minute*60)
    return int(time_now.replace(hour=hour, minute=minute, second=second).timestamp())


def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - timedelta(days=next_month.day)





def group_fields(data,fields):
    list_fields = []
    print(list_fields)
    for x in data:
        if not x[fields] in list_fields: list_fields.append(x[fields])
    new_group = {}
    for y in list_fields:
        new_group[y] = []
        for x in data:
            if x[fields] == y : new_group[y].append(x)
    return new_group

def valid_number(string):
	try:
		float(string)
		return True
	except ValueError:
		return False

from base64 import b64encode

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'



