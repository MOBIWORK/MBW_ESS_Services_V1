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
    group_fields,
    get_ip_network
)

from datetime import datetime
from mbw_service_v2.translations.language import translations
from pypika import  Order, CustomFunction
# Dịch vụ chấm công


@frappe.whitelist(methods="POST")
def checkin_shift(**data):
    try:
        ip_network = get_ip_network()
        id_position = dict(data).get("timesheet_position")
        wifi_mac = dict(data).get("wifi_mac")
        timesheet_position_detail = frappe.get_doc("TimeSheet Position",id_position)
        name= get_employee_id()
        if timesheet_position_detail:
            wifi_position = timesheet_position_detail.get('wifi')
            mac_position = timesheet_position_detail.get('mac')
            is_limited = timesheet_position_detail.get("is_limited")
            employees = timesheet_position_detail.get("employees")
            if is_limited != "All employee" :
                is_enable_checkin = False
                for employee in employees:
                    if employee.get("employee_id") == name:
                        is_enable_checkin = True
                        break
                if not is_enable_checkin :
                    gen_response(500, "Ban khong the cham cong tai day",[])
                    return
                
            in_wf = False
            in_mac = False
            for wf in wifi_position: 
                if ip_network == wf.get("wifi_address") or wifi_mac == wf.get("wifi_address"):
                    in_wf = True
                    break
            for mc in mac_position: 
                if ip_network == mc.get("mac_address") or wifi_mac == mc.get("mac_address"):
                    in_mac = True
                    break
            if not in_mac and not in_wf :
                gen_response(500, "loi mang",[])
                return
    
            
            shift_now = get_shift_type_now(name) 
            if shift_now.get("shift_type_now"):   
                new_check = frappe.new_doc("Employee Checkin")
                data["device_id"] = json.dumps({"longitude": data.get(
                    "longitude"), "latitude": data.get("latitude")})
                for field, value in dict(data).items():
                    setattr(new_check, field, value)
                log_type = "IN" if shift_now.get('shift_status') == False or shift_now.get('shift_status') == "OUT" else "OUT"
                setattr(new_check,'log_type',log_type)
                setattr(new_check,"image_attach",data.get("image"))
                new_check.insert()
                message = translations.get("create_success").get(get_language())
                gen_response(200,message,new_check)
                return
            gen_response(500, "Bạn không có ca",None)
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
        exception_handel(e)


@frappe.whitelist(methods="GET",allow_guest= True)
def get_shift_now():
    try:
        import socket
        client_ip = frappe.local.request.remote_addr
        import netifaces
        import requests
        import psutil

        # Lấy địa chỉ IP mạng của giao diện mạng (ví dụ: eth0)
        network_interfaces = psutil.net_if_addrs().keys() 
        # return network_interfaces
        network_interface = "enp2s0"
        network_ip = netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']
        print(f"Địa chỉ IP mạng của giao diện {network_interface}: {network_ip}")        
        return network_ip
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
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        ShiftType = frappe.qb.DocType('Shift Type')
        Employee = frappe.qb.DocType('Employee')
        ShiftRequest = frappe.qb.DocType('Shift Request')
        query_code = (ShiftRequest.employee == employeID)
        if status:
            query_code = query_code & ShiftRequest.status == status
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
