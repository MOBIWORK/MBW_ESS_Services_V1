import frappe
import json
from mbw_service_v2.api.common import  (get_last_check_today, gen_response,get_employee_id,exception_handel,get_language,get_shift_type_now,
    today_list_shift,
    delta_to_time_now,
    group_fields,
    get_ip_network,
    nextshift,
    inshift,
    enable_check_shift,
    validate_datetime,
    validate_empty,
    validate_image
    )


from datetime import datetime
from pypika import  Order, CustomFunction
from mbw_service_v2.config_translate import i18n
UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])

# Timekeeping service
@frappe.whitelist(methods="POST")
def checkin_shift(**data):
    try:
        ip_network = get_ip_network()
        id_position = (data).get("timesheet_position")
        
        wifi_mac = (data).get("wifi_mac")
        shift = (data).get("shift")
        timesheet_position_detail = frappe.get_doc("TimeSheet Position",id_position)
        name= get_employee_id()
        time_now = datetime.now()
        if not id_position or not shift: 
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()),[])
            return
        
        # Get the record of today's last shift or the most recent cross-day shift
        last_check = get_last_check_today(name)
        print('last_check',last_check)
        # Get the transmitted shift information
        shift_detail = frappe.get_doc("Shift Type",shift)
        log_type = "IN"

        # Check the record status 
        if last_check :
            if last_check.get('shift').lower() == shift.lower(): 
                if  last_check.get("log_type") == "OUT": 
                    gen_response(500, i18n.t('translate.invalid_shift', locale=get_language()),[])
                    return
                else: 
                    log_type = "OUT" 
            else:           
                if last_check.get("log_type") == "IN": 
                    gen_response(500, i18n.t('translate.shift_not_out', locale=get_language()),[])
                    return
        if not enable_check_shift(name, shift,time_now,log_type) : 
            gen_response(406, i18n.t('translate.invalid_shift', locale=get_language()),[])
            return
        # check location
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
                        data['timesheet_position'] = id_position
                        break
                if not is_enable_checkin :
                    gen_response(500, i18n.t('translate.no_location_shift', locale=get_language()),[])
                    return
            if (len(wifi_position) > 0 and len(mac_position) > 0) :
                in_wf = False
                in_mac = False
                for wf in wifi_position: 
                    if ip_network == wf.get("wifi_address") or wifi_mac == wf.get("wifi_address"):
                        data['wifi'] = wf.get("wifi_name")
                        in_wf = True
                        break
                for mc in mac_position: 
                    if ip_network == mc.get("mac_address") or wifi_mac == mc.get("mac_address"):
                        data['wifi'] = wf.get("mac_name")
                        in_mac = True
                        break
                if not in_mac and not in_wf :
                    gen_response(500, i18n.t('translate.error_network', locale=get_language()),[])
                    return
            new_check = frappe.new_doc("Employee Checkin")
            data["device_id"] = json.dumps({"longitude": data.get(
                "longitude"), "latitude": data.get("latitude")})
            data['on_map'] = json.dumps({"type":"Feature","properties":{},"geometry":{"type":"Point","coordinates":[data.get(
                "longitude"),data.get("latitude")]}})
            for field, value in data.items():
                setattr(new_check, field, value)
            setattr(new_check,'log_type',log_type)
            setattr(new_check,'employee',name)
            setattr(new_check,"image_attach",data.get("image"))
            new_check.insert()
            gen_response(200,i18n.t('translate.successfully', locale=get_language()),new_check)
            return
    except frappe.DoesNotExistError:
        gen_response(404, i18n.t('translate.error', locale=get_language()), []) 
    except Exception as e: 
        exception_handel(e)


# employee attendance list
@frappe.whitelist(methods='GET')
def get_list_cham_cong(**kwargs):
    try:
        kwargs = frappe._dict(kwargs)
        employee = get_employee_id()
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
                      .where((EmployeeCheckin.time >= start_time) & (EmployeeCheckin.time <= end_time) & (Attendance.attendance_date == date.date()) & (EmployeeCheckin.employee == employee))
                      .select(EmployeeCheckin.shift, EmployeeCheckin.log_type, EmployeeCheckin.time, EmployeeCheckin.device_id, ShiftType.start_time, ShiftType.end_time)
                      .run(as_dict=True)
                      )
        new_shift = group_fields(shift_type, "shift")
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), new_shift)
    except Exception as e:
        exception_handel(e)

#Shift now
@frappe.whitelist(methods="GET",allow_guest= True)
def get_shift_now():
    try:
        name= get_employee_id()
        time_now = datetime.now()
        shift_now = {
            "shift_type_now" : False,
            "shift_status" : False
                }
        # take the last shift
        last_check = get_last_check_today(name)
        # return last_check
        if last_check  :  
            if last_check.get("log_type") == "OUT" : 
                shift_suggest = False
                in_shift = inshift(name, time_now)
                if in_shift and in_shift.get("name") != last_check.get("shift"):
                    shift_suggest = in_shift
                else :
                    shift_suggest =  nextshift(name, time_now)

                shift_now = {
                "shift_type_now" :shift_suggest,
                "shift_status" : False
                }
            else :
                shift_now = {
                    "shift_type_now" : {
                        "name": last_check.get("shift"),
                        "start_time": last_check.get("start_time"),
                        "end_time": last_check.get("end_time"),
                        "allow_check_out_after_shift_end_time": last_check.get("allow_check_out_after_shift_end_time"),
                        "begin_check_in_before_shift_start_time": last_check.get("begin_check_in_before_shift_start_time"),
                        "start_time_today": last_check.get("start_time_today"),
                        "end_time_today": last_check.get("end_time_today"),
                        "timesheet_position": last_check.get("timesheet_position"),
                    },
                    "shift_status" : "IN"
                    }
        else: 
            in_shift = inshift(name, time_now)
            shift_now = {
            "shift_type_now" :in_shift if in_shift else False,
            "shift_status" : False
            }
        if shift_now["shift_type_now"]:
            shift_now["shift_type_now"]["start_time_today"] = delta_to_time_now(shift_now["shift_type_now"]["start_time"])
            shift_now["shift_type_now"]["end_time_today"] =delta_to_time_now(shift_now["shift_type_now"]["end_time"])
        gen_response(200,i18n.t('translate.successfully', locale=get_language()),shift_now) 

        return
    except Exception as e:
        exception_handel(e)

#List shift
@frappe.whitelist(methods="GET")
def get_shift_list():
    try:
        name= get_employee_id()
        time_now = datetime.now()
        list_shift = today_list_shift(name,time_now)
        for x in list_shift:
            x["start_time_today"] = delta_to_time_now(x["start_time"])
            x["end_time_today"] = delta_to_time_now(x['end_time'])
        gen_response(200, i18n.t('translate.successfully', locale=get_language()),list_shift) 
    except Exception as e:
        exception_handel(e)

#list shift request
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
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
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
        employee_id = get_employee_id()
        new_shift_request = frappe.new_doc('Shift Request')
        new_shift_request.employee = employee_id
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
        gen_response(201,i18n.t('translate.create_success', locale=get_language()),{
            "shift_request": new_shift_request,
            "approver_info": approver_info[0]
        })
    except Exception as e:
        exception_handel(e)

# all shifts
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


# approver information
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
 
        gen_response(200,i18n.t('translate.successfully', locale=get_language()),approver_info)
    except Exception as e:
        exception_handel(e)


# list reason
@frappe.whitelist(methods='GET')
def get_list_reason():
    try:
        attandance_reason = frappe.db.get_list('Attendance Reason', fields=["name", "reason_name"])
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), attandance_reason)
    except Exception as e:
        return exception_handel(e)

#create attendance request
@frappe.whitelist(methods='POST')
def create_attendance_request(**kwargs):
    try:
        employee = get_employee_id()
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        company = validate_link("Employee",employee,json.dumps(["company"]))
        
        new_doc = frappe.new_doc("Attendance Request")
        if from_date > to_date:
            gen_response(500, i18n.t('translate.title_3', locale=get_language()))
            return None
        
        if from_date == to_date and kwargs.get('half_day') == True:
            new_doc.half_day = True
            new_doc.half_day_date = validate_datetime(from_date)
        elif(from_date < to_date and kwargs.get('half_day') == True):
            if(kwargs.get('half_day_date') >= from_date and kwargs.get('half_day_date') <= to_date):
                new_doc.half_day = True
                new_doc.half_day_date = validate_datetime(kwargs.get('half_day_date'))
            else: 
                return gen_response(500, i18n.t('translate.title_4', locale=get_language()), [])
        new_doc.from_date = validate_datetime(from_date)
        new_doc.to_date = validate_datetime(to_date)
        new_doc.employee = employee
        new_doc.company = company
        new_doc.reason = validate_empty(kwargs.get('reason'))
        new_doc.explanation = kwargs.get('explanation')
        new_doc.custom_shift = kwargs.get("custom_shift")
        new_doc.insert()
        gen_response(201, i18n.t('translate.create_success', locale=get_language()))
    except Exception as e:
       exception_handel(e)

#list attendace rq
@frappe.whitelist()
def get_attendance_request(**kwargs):
    try:
        employee_id = get_employee_id()
        approver = validate_link(doctype='Employee',docname= employee_id,fields=json.dumps(["employee_name","department","custom_attendance_request_approver"]))
        
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        sortDefault = kwargs.get("sort")
        status = kwargs.get("status")
        filters = {
            "employee": employee_id
        }
        if status:
            filters.update({
                "status": status
            })
        if sortDefault == "asc":
            sortDefault = "asc"
        else:
            sortDefault = "desc"

        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        if approver.get('custom_attendance_request_approver'):
            approver_info = (frappe.qb.from_(User)
                            .inner_join(Employee)
                            .on(User.email == Employee.user_id)
                            .where(User.email ==  approver['custom_attendance_request_approver'])
                            .select(Employee.employee_name.as_("full_name"),Employee.image,User.email)
                            .run(as_dict=True)
                            )
            for info in approver_info:
                info['image'] = validate_image(info.get("image"))
        else: 
            return gen_response(404, i18n.t('translate.approve_not_setup', locale=get_language()))
          
        queryShift = frappe.db.get_list("Attendance Request",filters= filters,
        fields= ['name', 'employee',"employee_name","unix_timestamp(creation) as creation",
                 "unix_timestamp(creation) as creation",
                 "unix_timestamp(from_date) as from_date"
                 ,"unix_timestamp(to_date) as to_date"
                 ,"workflow_state"
                 ,"half_day"
                 ,"unix_timestamp(half_day_date) as half_day_date"
                 ,"(custom_shift) as shift_type"
                 ,"reason"
                 ,"shift"
                 ,"explanation"
                ],
        order_by=f"name {sortDefault}",
        start = start,
        page_length=20,
        )

        for att in queryShift:
            if att.get("shift"): 
                shift = frappe.get_doc("Shift Type",att.get("shift"))
                att["start_time"] = shift.start_time
                att["end_time"] = shift.end_time
        queryDraft = frappe.db.count('Attendance Request', {'workflow_state': "Draft", 'employee': employee_id})
        querryApproved = frappe.db.count('Attendance Request', {'workflow_state': "Approved", 'employee': employee_id})
        queryRejected = frappe.db.count('Attendance Request',{'workflow_state': "Rejected", 'employee': employee_id})
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": queryShift,
            "user_approver": approver_info[0],
            "queryDraft": queryDraft,
            "querryApproved": querryApproved,
            "queryRejected": queryRejected
        })
    except Exception as e:
        print(e)
        exception_handel(e)

#detail attendance
@frappe.whitelist()
def get_detail_attendance(name):
    try:
        employee_id = get_employee_id()
        approver = validate_link(doctype='Employee',docname= employee_id,fields=json.dumps(["employee_name","department","custom_attendance_request_approver"]))
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        ShiftType = frappe.qb.DocType('Shift Type')
        AttendanceRequest = frappe.qb.DocType('Attendance Request')
        query_code = (AttendanceRequest.employee == employee_id)
        queryShift = (frappe.qb.from_(AttendanceRequest)
                      .inner_join(ShiftType)
                      .on(AttendanceRequest.custom_shift == ShiftType.name)
                      .where(query_code & (AttendanceRequest.name == name))
                      .orderby(AttendanceRequest.creation, order=Order.desc)
                      .select(AttendanceRequest.name,AttendanceRequest.employee_name ,UNIX_TIMESTAMP(AttendanceRequest.creation).as_("creation"),UNIX_TIMESTAMP(AttendanceRequest.from_date).as_("from_date"), UNIX_TIMESTAMP(AttendanceRequest.to_date).as_("to_date"),AttendanceRequest.workflow_state,AttendanceRequest.half_day,UNIX_TIMESTAMP(AttendanceRequest.half_day_date).as_("half_day_date") ,AttendanceRequest.custom_shift.as_("shift_type"), AttendanceRequest.explanation, ShiftType.start_time, ShiftType.end_time).run(as_dict=True)
                      )        

        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        approver_info = (frappe.qb.from_(User)
                         .inner_join(Employee)
                         .on(User.email == Employee.user_id)
                         .where(User.email ==  approver['custom_attendance_request_approver'])
                         .select(Employee.employee_name.as_("full_name"),Employee.image,User.email)
                         .run(as_dict=True)
                         )
        for info in approver_info:
            info['image'] = validate_image(info.get("image"))
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": queryShift,
            "user_approver": approver_info[0]
        })
    except Exception as e:
       exception_handel(e)

# approver attendance information
@frappe.whitelist(methods='GET')
def get_approved_attendance():
    try:
        employee = get_employee_id()
        approver = validate_link(doctype='Employee',docname= employee,fields=json.dumps(["employee_name","department","custom_attendance_request_approver"]))
        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        approver_info = (frappe.qb.from_(User)
                         .inner_join(Employee)
                         .on(User.email == Employee.user_id)
                         .where(User.email ==  approver['custom_attendance_request_approver'])
                         .select(Employee.employee_name.as_("full_name"),Employee.image,User.email)
                         .run(as_dict=True)
                         )
        for info in approver_info:
            info['image'] = validate_image(info.get("image"))
        gen_response(200,i18n.t('translate.successfully', locale=get_language()),approver_info)
    except Exception as e:
        exception_handel(e)

#delete shift rq
@frappe.whitelist(methods="DELETE")
def delete_shift_rq(name):
    try:

        frappe.delete_doc('Shift Request',name)
        gen_response(200, i18n.t('translate.delete_success', locale=get_language()),[])
    except Exception as e:
        exception_handel(e)

#update shift rq
@frappe.whitelist(methods="PUT")
def update_shift_rq(**data):
    try:
        date_format = '%Y/%m/%d'
        fieldAccess = ["name", "shift_type", "to_date", "from_date"]
        del data['cmd']

        for field, value in dict(data).items():
            if field not in fieldAccess:
                mess = i18n.t('translate.invalid_value', locale=get_language()) + "" + field
                frappe.local.response['message'] = mess
                frappe.local.response['http_status_code'] = 404
                frappe.response["result"] = []
                return None
            
        if not data.get('name'):
            gen_response(500,i18n.t('translate.name_require', locale=get_language()),[])
            return
        if data['from_date'] : 
            data['from_date'] = datetime.fromtimestamp(int(data.get('from_date'))).strftime(date_format)
        if data['to_date'] : 
            data['to_date'] = datetime.fromtimestamp(int(data.get('to_date'))).strftime(date_format)

        shift_name = data.get('name')
        doc = frappe.get_doc('Shift Request', shift_name)
        if not doc:
            gen_response(500,i18n.t('translate.doc_not_found', locale=get_language()),[])
            return
        for field, value in dict(data).items():
            setattr(doc, field, value)
        doc.save()
        if doc.get("from_date") :
            setattr(doc,"from_date",datetime.strptime(doc.get("from_date"), date_format).timestamp()) 
        if doc.get("to_date") :
            setattr(doc,"to_date",datetime.strptime(doc.get("to_date"), date_format).timestamp())   
        

        gen_response(200, i18n.t('translate.update_success', locale=get_language()))

    except Exception as e:
       exception_handel(e)


#delete attendance rq
@frappe.whitelist(methods="DELETE")
def delete_attendance_rq(name):
    try:

        frappe.delete_doc('Attendance Request',name)
        gen_response(200, i18n.t('translate.delete_success', locale=get_language()),[])
    except Exception as e:
        exception_handel(e)
    
#update attendance rq
@frappe.whitelist(methods="PUT")
def update_attendance_rq(**data):
    try:
        date_format = '%Y/%m/%d'
        fieldAccess = ["name", "custom_shift", "to_date", "from_date", "explanation", "reason", "half_day","half_day_date"]
        del data['cmd']

        for field, value in dict(data).items():
            if field not in fieldAccess:
                mess = i18n.t('translate.invalid_value', locale=get_language()) + "" + field
                frappe.local.response['message'] = mess
                frappe.local.response['http_status_code'] = 404
                frappe.response["result"] = []
                return None
            
        if not data.get('name'):
            gen_response(500,i18n.t('translate.name_require', locale=get_language()),[])
            return
        if data['from_date'] : 
            data['from_date'] = datetime.fromtimestamp(int(data.get('from_date'))).strftime(date_format)
        if data['to_date'] : 
            data['to_date'] = datetime.fromtimestamp(int(data.get('to_date'))).strftime(date_format)
        if data.get("half_day") == 1 and data.get("half_day_date") == "":
            gen_response(500,i18n.t('translate.must_has_hafl_date', locale=get_language()),[])
            return
        if data['half_day_date'] : 
            data['half_day_date'] = datetime.fromtimestamp(int(data.get('half_day_date'))).strftime(date_format)
        shift_name = data.get('name')
        doc = frappe.get_doc('Attendance Request', shift_name)
        if not doc:
            gen_response(500,i18n.t('translate.doc_not_found', locale=get_language()),[])
            return
        for field, value in dict(data).items():
            setattr(doc, field, value)
        doc.save()
        if doc.get("from_date") :
            setattr(doc,"from_date",datetime.strptime(doc.get("from_date"), date_format).timestamp()) 
        if doc.get("to_date") :
            setattr(doc,"to_date",datetime.strptime(doc.get("to_date"), date_format).timestamp())   
        if doc.get("half_day_date") :
            setattr(doc,"half_day_date",datetime.strptime(doc.get("half_day_date"), date_format).timestamp() )

        gen_response(200, i18n.t('translate.update_success', locale=get_language()))

    except Exception as e:
       exception_handel(e)
