import frappe
import json
from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    get_language,
    get_shift_type_now,
    today_list_shift,
    delta_to_time_now,
    group_fields
)

from datetime import datetime
from mbw_service_v2.translations.language import translations
from pypika import Field,functions, Order, CustomFunction
# Dịch vụ chấm công


@frappe.whitelist(methods="POST")
def checkin_shift(**data):
    try:
        # employee = get_employee_id()
        # time_check = datetime.fromtimestamp(int(data.get('time')))  
        time_check_server = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")    
        new_check = frappe.new_doc("Employee Checkin")
        data["device_id"] = json.dumps({"longitude": data.get(
            "longitude"), "latitude": data.get("latitude")})
        # data["time"] = time_check_server
        for field, value in dict(data).items():
            setattr(new_check, field, value)
        setattr(new_check,"image_attach",data.get("image"))
        new_check.insert()
        message = translations.get("create_success").get(get_language())
        gen_response(200,message,new_check)
    except frappe.DoesNotExistError:
        message = translations.get("error").get(get_language())
        gen_response(404, message, []) 

# danh sách chấm công nhân viên

@frappe.whitelist(methods='GET')
def get_list_cham_cong(**kwargs):
    try:
        kwargs = frappe._dict(kwargs)
        date = datetime.fromtimestamp(int(kwargs.get('date')))
        start_time = date.replace(hour=0,minute=0)
        end_time = date.replace(hour=23,minute=59)
        EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
        ShiftType = frappe.qb.DocType("Shift Type")
        Attendance = frappe.qb.DocType("Attendance")
        shift_type = (frappe.qb.from_(EmployeeCheckin)
                      .inner_join(ShiftType)
                      .on(EmployeeCheckin.shift == ShiftType.name)
                      .inner_join(Attendance)
                      .on(Attendance.employee == EmployeeCheckin.employee)
                      .where((EmployeeCheckin.time >= start_time) & (EmployeeCheckin.time <= end_time) & (Attendance.attendance_date == date.date()))
                      .select(EmployeeCheckin.shift, EmployeeCheckin.log_type, EmployeeCheckin.time, EmployeeCheckin.device_id, ShiftType.start_time, ShiftType.end_time)
                      .run(as_dict=True)
                      )
        new_shift = group_fields(shift_type, "shift")
        message = translations.get("successfully").get(get_language())
        gen_response(200, message, new_shift)
    except Exception as e:
        # message = translations.get("error").get(get_language())
        # gen_response(500, message, [])
        exception_handel(e)

@frappe.whitelist(methods="GET")
def get_shift_now():
    try:
        print("vao day")
        name= get_employee_id()
        shift_now = get_shift_type_now(name)
        if shift_now["shift_type_now"]:
            shift_now["shift_type_now"]["start_time_today"] = delta_to_time_now(shift_now["shift_type_now"]["start_time"])
            shift_now["shift_type_now"]["end_time_today"] =delta_to_time_now(shift_now["shift_type_now"]["end_time"])
        gen_response(200,"",shift_now) 
    except Exception as e:
        exception_handel(e)


@frappe.whitelist(methods="GET")
def get_shift_list():
    try:
        name= get_employee_id()
        time_now = datetime.now()

        list_shift = today_list_shift(name,time_now)
        for x in list_shift:
            x["start_time_today"] = delta_to_time_now(x["start_time"])
            x["end_time_today"] = delta_to_time_now(x['end_time'])
        gen_response(200,"",list_shift) 
    except Exception as e:
        exception_handel(e)

@frappe.whitelist(methods="GET")
def get_list_shift_request(**kwargs):
    try:
        employeID = get_employee_id()
        status = kwargs.get('status')
        # start_time = kwargs.get('start_time')
        # end_time = kwargs.get('end_time')
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        ShiftType = frappe.qb.DocType('Shift Type')
        Employee = frappe.qb.DocType('Employee')
        ShiftRequest = frappe.qb.DocType('Shift Request')
        # if start_time:
        #     start_time = datetime.fromtimestamp(int(start_time))
        # if end_time:
        #     end_time = datetime.fromtimestamp(int(end_time))
        query_code = (ShiftRequest.employee == employeID)
        if status:
            query_code = query_code & ShiftRequest.status == status
        # if (start_time) and (end_time):
        #     query_code = query_code & (ShiftRequest.creation.between(start_time, end_time))
        queryShift = (frappe.qb.from_(ShiftRequest)
                      .inner_join(ShiftType)
                      .on(ShiftRequest.shift_type == ShiftType.name)
                      .inner_join(Employee)
                      .on(ShiftRequest.approver == Employee.user_id)
                      .where(query_code)
                      .offset(start)
                      .limit(page_size)
                      .orderby(ShiftRequest.creation, order=Order.desc)
                      .select(ShiftRequest.name, UNIX_TIMESTAMP(ShiftRequest.creation).as_("creation"),UNIX_TIMESTAMP(ShiftRequest.from_date).as_("from_date"), UNIX_TIMESTAMP(ShiftRequest.to_date).as_("to_date"), ShiftRequest.shift_type, ShiftType.start_time, ShiftType.end_time,ShiftRequest.status, ShiftRequest.approver,Employee.employee_name ,Employee.image).run(as_dict=True)
                      )
        queryOpen = frappe.db.count('Shift Request', {'status': 'Draft', 'employee': employeID})
        queryApprover = frappe.db.count('Shift Request', {'status': 'Approved', 'employee': employeID})
        queryReject = frappe.db.count('Shift Request', {'status': 'Rejected', 'employee': employeID})
        # shift_assignment = frappe.db.get_list('Shift Assignment', filters=myfilter , fields=["*"])
        return gen_response(200, " ", {
            "data": queryShift,
            "queryOpen": queryOpen,
            "queryApprover": queryApprover,
            "queryReject": queryReject
        })
    except Exception as e:
        exception_handel(e)

from frappe.desk.search import search_link, build_for_autosuggest, search_widget

# create shift assignment
@frappe.whitelist(methods="POST")
def create_shift_request(**data) :
    try: 
        new_shift_request = frappe.new_doc('Shift Request')
        from_date = datetime.fromtimestamp(int(data.get("from_date"))).date() if data.get("from_date") else False
        to_date = datetime.fromtimestamp(int(data.get("to_date"))).date() if data.get("to_date") else False
        if not from_date or not to_date:
            gen_response(500, "invalid from_date or to date",[])
        if from_date > to_date: 
            gen_response(500,"From Date can large than To Date") 
        data['from_date'] = from_date
        data['to_date'] = to_date
        for field, value in data.items():
            setattr(new_shift_request, field, value)
        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        approver_info = (frappe.qb.from_(User)
                         .inner_join(Employee)
                         .on(User.email == Employee.user_id)
                         .where(User.email ==  data.get("approver"))
                         .select(User.full_name,Employee.image,User.email)
                         .run(as_dict=True)
                         )
 
        new_shift_request.insert()
        gen_response(201,"Success",{
            "shift_request": new_shift_request,
            "approver_info": approver_info[0]
        })
    except Exception as e:
        exception_handel(e)

# tất cả các ca
@frappe.whitelist(methods='GET')
def all_shift():
    try:
        # search_link(
        #     doctype='Shift Type',
        #     txt='',
        #     reference_doctype="Shift Request",
        #     ignore_user_permissions=False,
        # )
        search_widget(
            doctype='Shift Type',
            txt= ''.strip(),
            query = None,
            searchfield=None,
            page_length=100,
            filters=None,
            reference_doctype="Shift Request",
            ignore_user_permissions=False,
        )

        frappe.response["result"] = build_for_autosuggest(frappe.response["values"], doctype='Shift Type')
        del frappe.response["values"]
    except Exception as e:
        exception_handel(e)

from frappe.client import validate_link
import json
# thông tin người phê duyệt
@frappe.whitelist(methods='GET')
def get_approved():
    try:
        employee = get_employee_id()
        approver = validate_link(doctype='Employee',docname= employee,fields=json.dumps(["employee_name","department","shift_request_approver"]))
        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        approver_info = (frappe.qb.from_(User)
                         .inner_join(Employee)
                         .on(User.email == Employee.user_id)
                         .where(User.email ==  approver['shift_request_approver'])
                         .select(User.full_name,Employee.image,User.email)
                         .run(as_dict=True)
                         )
 
        gen_response(200,"",approver_info)
    except Exception as e:
        exception_handel(e)
