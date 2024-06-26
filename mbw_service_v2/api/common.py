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
from frappe.client import validate_link

BASE_URL = frappe.utils.get_request_site_address()



#get approve 
def get_approver_detail(employee, field) :
    approver = validate_link(doctype='Employee',docname= employee,fields=json.dumps(["employee_name","department",field]))
    print("=====1", approver.get(field))
    Employee = frappe.qb.DocType("Employee")
    User = frappe.qb.DocType("User")
    approver_info = (frappe.qb.from_(User)
                        .inner_join(Employee)
                        .on(User.email == Employee.user_id)
                        .where(User.email ==  approver.get(field))
                        .select(Employee.employee_name.as_("full_name"),Employee.image,User.email)
                        .run(as_dict=True)
                        )
    if len(approver_info) > 0: 
            for approver_c  in approver_info:
                approver_c["image"] = validate_image(approver_c.get("image"))
    else: 
        approver_info = None
    return approver_info
# ==================================================================================================
ShiftType = frappe.qb.DocType('Shift Type')
ShiftAssignment = frappe.qb.DocType('Shift Assignment')
EmployeeCheckin = frappe.qb.DocType("Employee Checkin")

# Take the last shift
def get_last_check_today(employee):
    time_now = datetime.now()
    last_check = (frappe.qb.from_(EmployeeCheckin)
                              .inner_join(ShiftType)
                              .on(EmployeeCheckin.shift == ShiftType.name)
                              .limit(1)
                              .where((EmployeeCheckin.employee ==  employee))
                              .orderby(EmployeeCheckin.time,order= Order.desc)
                              .select('*')
                              .run(as_dict=True))
    if len(last_check) ==0:
        return False
    last_check= last_check[0]
    if last_check.get("time").timestamp() > time_now.replace(hour=0,minute=0,second=0).timestamp() :
        return last_check
    return False

# Check staff shifts
def enable_check_shift(employee,shift,time_now,log_type):

    shift_employee = (frappe.qb.from_(ShiftType)
                      .inner_join(ShiftAssignment)
                      .on(ShiftType.name == ShiftAssignment.shift_type)
                      .where(
                          (ShiftAssignment.employee == employee) & 
                          (ShiftAssignment.status == "Active") & 
                          (ShiftAssignment.docstatus == 1) 
                          & (ShiftType.name == shift)
                             )
                      .select(ShiftAssignment.end_date,ShiftAssignment.start_date,ShiftType.name,ShiftType.total_shift_time, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                      .run(as_dict=True)
                )
    if len(shift_employee) >0: 
        has_shift = False
        for shift in shift_employee:
            if not shift.get("end_date") and not shift.get('start_date'):
                has_shift= shift
            elif not shift.get("end_date") and  shift.get('start_date') :
                if shift.get("start_date") <= time_now.date() :
                    has_shift= shift
            elif  shift.get("end_date") and not shift.get('start_date') :
                if shift.get("end_date") >= time_now.date() :
                    has_shift = shift
            else :
                if shift.get("end_date") >= time_now.date()  and shift.get("start_date") <= time_now.date() :
                    has_shift= shift
        if has_shift :

            if has_shift.begin_check_in_before_shift_start_time:
                print('in')
                if log_type == "OUT":
                    return True
                if (time_now.timestamp() - delta_to_time_now(has_shift.get('start_time')) > has_shift.get('begin_check_in_before_shift_start_time') or time_now.timestamp() - delta_to_time_now(has_shift.get('start_time')) < has_shift.get('total_shift_time')):
                    return True
                return False
            return True
        return False
    return False


def get_shift_type_now(employee_name):
    time_now = datetime.now()

    shift_type_now = today_list_shift(employee_name, time_now)
    shift_status = "Bạn không có ca hôm nay"
    time_query = time_now.replace(hour=0, minute=0, second=0)
    time_query_next_day =  time_now.replace(hour=23, minute=59, second=59)
    if len(shift_type_now) > 0:
        last_checkin_today = (frappe.qb.from_(EmployeeCheckin)
                              .limit(4)
                              .where((EmployeeCheckin.time >= time_query) & (EmployeeCheckin.time <= time_query_next_day))
                              .orderby(EmployeeCheckin.time,order= Order.desc)
                              .select('*')
                              .run(as_dict=True))
        if not last_checkin_today:
            shift_type_now = shift_now(employee_name, time_now)
            shift_status = False
        elif last_checkin_today[0].get("log_type") == "OUT":
            shift_type_now = nextshift(employee_name, time_now)
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


# Get a list of shifts by day
def today_list_shift(employee_name, time_now):
    query = (ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date)
    if not ShiftAssignment.end_date.isnull() :
        query = (ShiftAssignment.employee == employee_name) & (time_now.date() >= ShiftAssignment.start_date) & (time_now.date() <= ShiftAssignment.end_date)
    data =  (frappe.qb.from_(ShiftType)
            .inner_join(ShiftAssignment)
            .on(ShiftType.name == ShiftAssignment.shift_type)
            .where(
                (ShiftAssignment.employee == employee_name) & 
                            (ShiftAssignment.status == "Active") & 
                            (ShiftAssignment.docstatus == 1) 
            )
            .select(ShiftAssignment.start_date,ShiftAssignment.end_date,ShiftAssignment.employee, ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
            .run(as_dict=True)
            )
    data_rs = []
    for shift in data:
            if not shift.get("end_date") and not shift.get('start_date'):
                data_rs.append( shift)
            elif not shift.get("end_date") and  shift.get('start_date') :
                if shift.get("start_date") <= time_now.date() :
                    data_rs.append( shift)
            elif  shift.get("end_date") and not shift.get('start_date') :
                if shift.get("end_date") >= time_now.date() :
                    data_rs.append( shift)
            else :
                if shift.get("end_date") >= time_now.date()  and shift.get("start_date") <= time_now.date() :
                    data_rs.append( shift)
    return data_rs

# is in shift
def inshift(employee_name,time_now) :
    data = (frappe.qb.from_(ShiftType)
                      .inner_join(ShiftAssignment)
                      .on(ShiftType.name == ShiftAssignment.shift_type)
                      .where(
                          (ShiftAssignment.employee == employee_name) & 
                          (ShiftAssignment.status == "Active") & 
                          (ShiftAssignment.docstatus == 1) & 
                          (time_now.time() >= ShiftType.start_time) & 
                          (time_now.time() <= ShiftType.end_time) 
                             )
                      .select(ShiftAssignment.end_date,ShiftAssignment.start_date,ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                      .run(as_dict=True)
                )
    if len(data) == 0:
        return False    
    for shift in data:
        if not shift.get("end_date") and not shift.get('start_date'):
            return shift
        elif not shift.get("end_date") and  shift.get('start_date') :
            if shift.get("start_date") <= time_now.date() :
                return shift
        elif  shift.get("end_date") and not shift.get('start_date') :
            if shift.get("end_date") >= time_now.date() :
                return shift
        else :
            if shift.get("end_date") >= time_now.date()  and shift.get("start_date") <= time_now.date() :
                return shift

# next shift
def nextshift(employee_name,time_now) :
    data = (frappe.qb.from_(ShiftType)
                        .inner_join(ShiftAssignment)
                        .on(ShiftType.name == ShiftAssignment.shift_type)
                        .where(
                            (ShiftAssignment.employee == employee_name) & 
                            (ShiftAssignment.status == "Active") & 
                            (ShiftAssignment.docstatus == 1) 
                            & (time_now.time() <= ShiftType.start_time) 
                            )
                        .orderby(ShiftType.start_time,order= Order.asc)
                        .select(ShiftAssignment.end_date,ShiftAssignment.start_date,ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                        .run(as_dict=True)
                        )
    if len(data) == 0:
        return False
    for shift in data:
        if not shift.get("end_date") and not shift.get('start_date'):
            return shift
        elif not shift.get("end_date") and  shift.get('start_date') :
            if shift.get("start_date") <= time_now.date() :
                return shift
        elif  shift.get("end_date") and not shift.get('start_date') :
            if shift.get("end_date") >= time_now.date() :
                return shift
        else :
            if shift.get("end_date") >= time_now.date()  and shift.get("start_date") <= time_now.date() :
                return shift
    return False
# current shift
def shift_now(employee_name, time_now):
    in_shift = inshift(employee_name, time_now)

    if not in_shift:
        next_shift = nextshift(employee_name, time_now)
        if not next_shift:
            return False
        return next_shift
    return in_shift
# ======================================================================================


# Get employee reports
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


# Calculate the distance between two locations
from geopy.distance import great_circle
def distance_of_two(long_client, lat_client, long_compare, lat_compare):
    point1 = ( lat_client,long_client)
    point2 = (lat_compare,long_compare)
    return great_circle(point1, point2).meters

# return definition
def gen_response(status, message, result=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(
            str(message), features="lxml").get_text()
    else:
        frappe.response["message"] = message
    frappe.response["result"] = result

def cong_va_xoa_trung(mang1, mang2):
    # Cộng hai mảng và chuyển kết quả thành một set để loại bỏ các phần tử trùng nhau
    ket_qua_set = set(mang1 + mang2)

    # Chuyển kết quả trở lại thành một danh sách (nếu cần)
    ket_qua = list(ket_qua_set)

    return ket_qua

def exception_handel(e):
    frappe.log_error(title="ESS Mobile App Error",
                     message=frappe.get_traceback())
    return gen_response(406, cstr(e))
    
    if hasattr(e, "http_status_code"):
        return gen_response(e.http_status_code, cstr(e))
    else:
        return gen_response(406, cstr(e))

# export employee key
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
    columns, result, message, chart, report_summary = ljust_list(
        res,5)
    # print("res==============================cl",columns)
    # print("res==============================rs", result)
    # print("res==============================ms", message,)
    # print("res==============================chart",chart)
    # print("res==============================rp",report_summary)
    
    # report_column_names = [col["fieldname"] for col in columns]

    # convert to list of dicts
    result = normalize_result(chart, columns)

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



def get_ip_network():
    try:
        # # Get the user's IP address from the "X-Forwarded-For" HTTP header
        remote_ip = frappe.get_request_header("X-Forwarded-For")

        if not remote_ip:
            # If X-Forwarded-For is not available, try getting it from REMOTE_ADDR
            remote_ip = frappe.local.request.environ.get('REMOTE_ADDR')

        return remote_ip        
    except Exception as e:
        return e
    
def doc_status(status):
    if status == 0:
        return "Draft"
    elif status == 1:
        return "Submitted"
    else:
        return "Cancelled"
def get_pending_amount(employee,posting_date):
    from frappe.query_builder.functions import Sum
    Advance = frappe.qb.DocType("Employee Advance")
    return (frappe.qb.from_(Advance)
			.select(Sum(Advance.advance_amount - Advance.paid_amount))
			.where(
				(Advance.employee == employee)
				& (Advance.docstatus == 1)
				& (Advance.posting_date <= posting_date)
				& (Advance.status == "Unpaid")).run()
			)