import frappe
from mbw_service_v2.api.common import  (gen_response,get_employee_id,exception_handel,get_language,   
    get_employee_by_user,
    get_user_id,
    validate_image,
    get_approver_detail
    )
from mbw_service_v2.config_translate import i18n
from mbw_service_v2.api.ess.comment import post_comment_leave
from pypika import  Order, CustomFunction
from frappe.client import validate_link
import json
from datetime import datetime

@frappe.whitelist(methods="PATCH")
def approve_leave(**data):
    try: 
        doc_type = data.get("doc_type")
        name = data.get("name")
        reason = data.get("reason")
        status = data.get("status")
        if not (doc_type and name and reason and status): 
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), [])
            return 
        leave = frappe.get_doc(doc_type , name)
        if not leave :
            gen_response(500, i18n.t('translate.not_found', locale=get_language()), [])
            return 
        for key_att, value in data.items():
            if(key_att != "reason"):
                setattr(leave,key_att,value)
        setattr(leave,"docstatus",1)
        leave.save()
        info_employee = get_employee_by_user(get_user_id(), ["*"])
        doc_comment = frappe.new_doc('Comment')
        doc_comment.reference_doctype = doc_type
        doc_comment.reference_name = name
        doc_comment.comment_type = 'Comment'
        doc_comment.content = reason
        doc_comment.comment_by = info_employee.get('employee_name')
        doc_comment.comment_email = info_employee.get('user_id')
        doc_comment.insert(ignore_permissions=True)
        gen_response(200,"",{"leave":leave,"reason":reason})
        return
    except Exception as e:
        frappe.clear_messages()
        if frappe.response.get('exc_type'):
            del frappe.response["exc_type"]
        exception_handel(e)


@frappe.whitelist(methods="GET")
def get_leave_approve(**data):
    try:
        employee_id = get_employee_id()
        employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
        workflow_state = data.get('status')
        name = data.get('name')
        employee = data.get('employee')
        doctype = data.get("doctype")
        sortDefault = data.get("sort")
        if sortDefault == "asc":
            sortDefault = Order.asc
        else:
            sortDefault = Order.desc
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        page_size = 20 if not data.get(
            'page_size') else int(data.get('page_size'))

        page = 1 if not data.get('page') or int(
            data.get('page')) <= 0 else int(data.get('page'))
        start = (page - 1) * page_size
        Employee = frappe.qb.DocType("Employee")
        ShiftType = frappe.qb.DocType('Shift Type')

        Doc = frappe.qb.DocType(doctype)

        #attendance_request_for_approver
        if doctype == 'Attendance Request':
            typeLeave ='shift'
            query_code = (Employee.custom_attendance_request_approver == employee_info.get("user_id"))
            on1 = Doc.custom_shift
            selectReturn = (
                            Doc.workflow_state,
                            Doc.half_day,
                            UNIX_TIMESTAMP(Doc.half_day_date).as_("half_day_date") ,
                            Doc.custom_shift.as_("shift_type"),
                            Doc.reason ,
                            Doc.explanation,
                            UNIX_TIMESTAMP(Doc.from_date).as_("from_date"), 
                                UNIX_TIMESTAMP(Doc.to_date).as_("to_date"),
                            )
            if workflow_state:
                query_code = query_code & Doc.workflow_state == workflow_state
            
        #list_leave_for_approver
        elif doctype == "Leave Application" :
            typeLeave ='shift'
            query_code = (Employee.leave_approver == employee_info.get("user_id"))
            on1 = Doc.custom_shift_type
            selectReturn = ( Doc.leave_type, Doc.status,Doc.leave_approver,
                            Doc.half_day,UNIX_TIMESTAMP(Doc.half_day_date).as_("half_day_date"),
                            Doc.total_leave_days,Doc.description,
                            Doc.custom_shift_type,UNIX_TIMESTAMP(Doc.from_date).as_("from_date"), 
                                UNIX_TIMESTAMP(Doc.to_date).as_("to_date"),)
            if workflow_state:
                query_code = (query_code & Doc.status == workflow_state)

        #list_shift_rq_for_approver
        elif doctype == "Overtime Request" :
            typeLeave ='shift'
            query_code = (Employee.ot_approver == employee_info.get("user_id"))
            on1 = Doc.shift
            if workflow_state:
                query_code = query_code & Doc.workflow_state == workflow_state
            selectReturn = (
                    UNIX_TIMESTAMP(Doc.ot_date).as_("ot_date"),
                    Doc.shift,Doc.ot_start_time,Doc.ot_end_time,
                    Doc.ot_approver,UNIX_TIMESTAMP(Doc.posting_date).as_("posting_date"),
                    Doc.suggested_time,Doc.reason, Doc.status)
        #get_list_ot_request_approver
        elif doctype == "Shift Request":
            typeLeave ='shift'
            query_code = (Employee.shift_request_approver == employee_info.get("user_id"))
            on1 = Doc.shift_type
            if workflow_state:
                query_code = query_code & Doc.status == workflow_state
            selectReturn = (
                                UNIX_TIMESTAMP(Doc.from_date).as_("from_date"), 
                              UNIX_TIMESTAMP(Doc.to_date).as_("to_date"), 
                              Doc.shift_type,Doc.status
            )
        #get_list_Employee Advance
        elif doctype == 'Employee Advance':
            typeLeave ='advance'
            selectReturn = (Doc.purpose,Doc.advance_amount,Doc.status)
            query_code = (Employee.advance_approver == employee_info.get("user_id"))
            if workflow_state:
                query_code = query_code & Doc.status == workflow_state

        #handle common
        if name:
                query_code = query_code & Doc.name == name
        if employee:
            if type(employee) == str :
                 query_code = query_code & Doc.employee == employee
            else:
                query_code = query_code & (Doc.employee.isin(employee))
        print("query_code",query_code,page_size,start)
        # handle type leave 
        if typeLeave == "shift" :
            leave = (frappe.qb.from_(Doc)
                                .inner_join(ShiftType)
                                .on(on1 == ShiftType.name)
                                .inner_join(Employee)
                                .on(Doc.employee == Employee.name)
                                .offset(start)
                                .limit(page_size)
                                .where(query_code)
                                .orderby(Doc.creation, order=sortDefault)
                                .select(Doc.name, 
                                    Doc.employee,
                                    Doc.employee_name ,
                                    UNIX_TIMESTAMP(Doc.creation).as_("creation"),                                    
                                    *selectReturn,
                                    ShiftType.start_time, ShiftType.end_time,Employee.image, Employee.department).run(as_dict=True)
                                )
        else:
            leave = (frappe.qb.from_(Doc)
                     .inner_join(Employee)
                    .on(Doc.employee == Employee.name)
                    .where(query_code)
                    .offset(start)
                    .limit(page_size)
                    .where(query_code)
                    .orderby(Doc.creation, order=sortDefault)
                    .select(
                        Doc.name, 
                        Doc.employee,
                        Doc.employee_name ,
                        UNIX_TIMESTAMP(Doc.creation).as_("creation"),                        
                        *selectReturn,
                        Employee.image, Employee.department).run(as_dict=True)
                    )
                     
        if len(leave) > 0 :
            for rq in leave :
                rq['image'] = validate_image(rq.get("image"))
                info_approvers = frappe.db.get_value("Employee",employee_id, ['image', "user_id", "employee_name"],as_dict=True)
                rq["approver"] = {
                    "image": validate_image(info_approvers.get('image')),
                    "full_name": info_approvers.get('employee_name'),
                    "email": info_approvers.get('user_id')
                }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), leave)
    except Exception as e:
        exception_handel(e)


@frappe.whitelist(methods="GET")
def count_application(**data):
    employee_id = get_employee_id()
    employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
    Employee = frappe.qb.DocType('Employee')
    AttendanceRequest = frappe.qb.DocType('Attendance Request')
    LeaveApplication = frappe.qb.DocType('Leave Application')
    ShiftRequest = frappe.qb.DocType('Shift Request')
    OtRequest = frappe.qb.DocType("Overtime Request")
    
    queryOpenAttendanceRQ = len( (frappe.qb.from_(AttendanceRequest)
                      .inner_join(Employee)
                      .on(Employee.name == AttendanceRequest.employee)
                      .where(((Employee.custom_attendance_request_approver == employee_info.get("user_id")))& ("Draft" == AttendanceRequest.workflow_state))
                      .select("*").run(as_dict=True)
                      ))
    
    queryOpenLeaveApplication = len( 
        (frappe.qb.from_(LeaveApplication)
                        .inner_join(Employee)
                        .on(LeaveApplication.employee == Employee.name)
                        .where(((Employee.leave_approver == employee_info.get("user_id"))) & ("Open" == LeaveApplication.status)  & (LeaveApplication.custom_shift_type != ""))
                        .select("*").run(as_dict=True)
                    ))
    
    
    queryOpenShiftRQ = len( (frappe.qb.from_(ShiftRequest)
                      .inner_join(Employee)
                      .on(Employee.name == ShiftRequest.employee)
                      .where(((Employee.shift_request_approver == employee_info.get("user_id")))& ("Draft" == ShiftRequest.status))
                      .select("*").run(as_dict=True)
                      ))
    
    queryOpenOTRequest = len(frappe.qb.from_(OtRequest)
            .where(((OtRequest.ot_approver == employee_info.get("user_id"))) & ("Draft" == OtRequest.workflow_state))
            .select("*")
            .run(as_dict=True) )
    
    return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "explantion": queryOpenAttendanceRQ,
            "leave": queryOpenLeaveApplication,
            "shift": queryOpenShiftRQ,
            "overtime": queryOpenOTRequest
    })


#list attendance request for approver
@frappe.whitelist()
def attendance_request_for_approver(**kwargs):
    try:
        employee_id = get_employee_id()
        employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
        workflow_state = kwargs.get('status')
        name = kwargs.get('name')
        employee = kwargs.get('employee')
        sortDefault = kwargs.get("sort")
        if sortDefault == "asc":
            sortDefault = Order.asc
        else:
            sortDefault = Order.desc
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        Employee = frappe.qb.DocType("Employee")
        ShiftType = frappe.qb.DocType('Shift Type')
        AttendanceRequest = frappe.qb.DocType('Attendance Request')
        query_code = (Employee.custom_attendance_request_approver == employee_info.get("user_id"))
        if workflow_state:
            query_code = query_code & AttendanceRequest.workflow_state == workflow_state
        if name:
            query_code = query_code & AttendanceRequest.name == name
        if employee:
            if type(employee) == str :
                 query_code = query_code & AttendanceRequest.employee == employee
            else:
                query_code = query_code & (AttendanceRequest.employee.isin(employee))
        queryShift = (frappe.qb.from_(AttendanceRequest)
                      .inner_join(ShiftType)
                      .on(AttendanceRequest.custom_shift == ShiftType.name)
                      .inner_join(Employee)
                      .on(Employee.name == AttendanceRequest.employee)
                      .where(query_code)
                      .offset(start)
                      .limit(page_size)
                      .orderby(AttendanceRequest.creation, order=sortDefault)
                      .select(AttendanceRequest.name, 
                              AttendanceRequest.employee,
                              AttendanceRequest.employee_name ,
                              UNIX_TIMESTAMP(AttendanceRequest.creation).as_("creation"),
                              UNIX_TIMESTAMP(AttendanceRequest.from_date).as_("from_date"), 
                              UNIX_TIMESTAMP(AttendanceRequest.to_date).as_("to_date"),
                              AttendanceRequest.workflow_state,AttendanceRequest.half_day,
                              UNIX_TIMESTAMP(AttendanceRequest.half_day_date).as_("half_day_date") ,
                              AttendanceRequest.custom_shift.as_("shift_type"),
                              AttendanceRequest.reason ,AttendanceRequest.explanation, 
                              ShiftType.start_time, ShiftType.end_time, Employee.image, Employee.department).run(as_dict=True)
                      )
        if len(queryShift) > 0 :
            for rq in queryShift :
                rq['image'] = validate_image(rq.get("image"))
                info_approvers = frappe.db.get_value("Employee",employee_id, ['image', "user_id", "employee_name"],as_dict=True)
                rq["approver"] = {
                    "image": validate_image(info_approvers.get('image')),
                    "name_approver": info_approvers.get('employee_name'),
                    "email": info_approvers.get('user_id')
                }
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": queryShift,
        })
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])

#list of leaves for approver for approver
@frappe.whitelist()
def list_leave_for_approver(**kwargs):
    try:
        from frappe.client import validate_link
        employee_id = get_employee_id()
        employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
        kwargs = frappe._dict(kwargs)
        my_filter = {}
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        leave_type = kwargs.get('leave_type')
        status = kwargs.get('status')
        employee = kwargs.get('employee')
        name = kwargs.get('name')
        sortDefault = kwargs.get("sort")
        if sortDefault == "asc":
            sortDefault = Order.asc
        else:
            sortDefault = Order.desc
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        if start_time:
            start_time = datetime.fromtimestamp(int(start_time))
        if end_time:
            end_time = datetime.fromtimestamp(int(end_time))
        if leave_type:
            my_filter["leave_type"] = ['==', leave_type]
        Employee = frappe.qb.DocType('Employee')
        LeaveApplication = frappe.qb.DocType('Leave Application')
        ShiftType = frappe.qb.DocType('Shift Type')
        query_code = (Employee.leave_approver == employee_info.get("user_id"))
        if leave_type:
            query_code = query_code & (LeaveApplication.leave_type == leave_type)
        if status:
            query_code = query_code & LeaveApplication.status == status
        if employee:
            if type(employee) == str :
                 query_code = query_code & LeaveApplication.employee == employee
            else:
                query_code = query_code & (LeaveApplication.employee.isin(employee))
        if name:
            query_code = query_code & LeaveApplication.name == name
        if (start_time) and (end_time):
            query_code = query_code & (LeaveApplication.creation.between(start_time, end_time))
        leave_application = (frappe.qb.from_(LeaveApplication)
                              .inner_join(ShiftType)
                              .on(LeaveApplication.custom_shift_type == ShiftType.name)
                              .inner_join(Employee)
                              .on(LeaveApplication.employee == Employee.name)
                              .offset(start)
                              .limit(page_size)
                              .where(query_code)
                              .orderby(LeaveApplication.creation, order=sortDefault)
                              .select(LeaveApplication.name,LeaveApplication.employee_name,LeaveApplication.employee, 
                                      UNIX_TIMESTAMP(LeaveApplication.creation).as_("creation"), 
                                      UNIX_TIMESTAMP(LeaveApplication.from_date).as_("from_date"),
                                      UNIX_TIMESTAMP(LeaveApplication.to_date).as_("to_date"), 
                                      LeaveApplication.leave_type, LeaveApplication.status,LeaveApplication.leave_approver,
                                      LeaveApplication.half_day,UNIX_TIMESTAMP(LeaveApplication.half_day_date).as_("half_day_date"),
                                      LeaveApplication.total_leave_days,LeaveApplication.description,
                                      LeaveApplication.custom_shift_type,
                                      ShiftType.start_time, ShiftType.end_time,
                                      Employee.image, Employee.department).run(as_dict=True)
                              )
        if len(leave_application) > 0 :
            for rq in leave_application :
                rq['image'] = validate_image(rq.get("image"))
                info_approvers = frappe.db.get_value("Employee",employee_id, ['image', "user_id", "employee_name"],as_dict=True)
                rq["approver"] = {
                    "image": validate_image(info_approvers.get('image')),
                    "name_approver": info_approvers.get('employee_name'),
                    "email": info_approvers.get('user_id')
                }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": leave_application
        })
    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist(methods="GET")
def list_shift_rq_for_approver(**kwargs):
    try:
        employee_id = get_employee_id()
        employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
        status = kwargs.get('status')
        employee = kwargs.get('employee')
        name = kwargs.get('name')
        sortDefault = kwargs.get("sort")
        if sortDefault == "asc":
            sortDefault = Order.asc
        else:
            sortDefault = Order.desc
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        ShiftType = frappe.qb.DocType('Shift Type')
        Employee = frappe.qb.DocType('Employee')
        ShiftRequest = frappe.qb.DocType('Shift Request')
        query_code = (Employee.shift_request_approver == employee_info.get("user_id"))
        if status:
            query_code = query_code & ShiftRequest.status == status
        if name:
            query_code = query_code & ShiftRequest.name == name
        if employee:
            if type(employee) == str :
                 query_code = query_code & ShiftRequest.employee == employee
            else:
                query_code = query_code & (ShiftRequest.employee.isin(employee))
        queryShift = (frappe.qb.from_(ShiftRequest)
                      .inner_join(ShiftType)
                      .on(ShiftRequest.shift_type == ShiftType.name)
                      .inner_join(Employee)
                      .on(ShiftRequest.employee == Employee.name)
                      .where(query_code)
                      .offset(start)
                      .limit(page_size)
                      .orderby(ShiftRequest.creation, order=sortDefault)
                      .select(ShiftRequest.name,
                              ShiftRequest.employee, ShiftRequest.employee_name ,UNIX_TIMESTAMP(ShiftRequest.creation).as_("creation"),
                              UNIX_TIMESTAMP(ShiftRequest.from_date).as_("from_date"), 
                              UNIX_TIMESTAMP(ShiftRequest.to_date).as_("to_date"), 
                              ShiftRequest.shift_type,ShiftRequest.status, ShiftType.start_time, ShiftType.end_time,
                              Employee.image, Employee.department).run(as_dict=True)
                      )
        if len(queryShift) > 0 :
            for rq in queryShift :
                rq['image'] = validate_image(rq.get("image"))
                info_approvers = frappe.db.get_value("Employee",employee_id, ['image', "user_id", "employee_name"],as_dict=True)
                rq["approver"] = {
                    "image": validate_image(info_approvers.get('image')),
                    "name_approver": info_approvers.get('employee_name'),
                    "email": info_approvers.get('user_id')
                }
        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "data": queryShift
        })
    except Exception as e:
        exception_handel(e)

#ot approver
@frappe.whitelist(methods='GET')
def get_list_ot_request_approver(**kwargs):
    try:
        employee_id = get_employee_id()
        employee_info = frappe.db.get_value("Employee",employee_id,['*'],as_dict=True)
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        workflow_state = kwargs.get('status')
        name = kwargs.get('name')
        employee = kwargs.get('employee')
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        sortDefault = kwargs.get("sort")
        if sortDefault == "asc":
            sortDefault = Order.asc
        else:
            sortDefault = Order.desc
        OtRequest = frappe.qb.DocType("Overtime Request")
        Employee = frappe.qb.DocType("Employee")
        ShiftType = frappe.qb.DocType('Shift Type')
        query = (OtRequest.ot_approver == employee_info.get("user_id"))
        query_code = (Employee.ot_approver == employee_info.get("user_id"))
        if workflow_state:
            query_code = query_code & OtRequest.workflow_state == workflow_state
        if name:
            query_code = query_code & OtRequest.name == name
        if employee:
            if type(employee) == str :
                 query_code = query_code & OtRequest.employee == employee
            else:
                query_code = query_code & (OtRequest.employee.isin(employee))
        list_ot_rq = (
            frappe.qb.from_(OtRequest)
            .inner_join(Employee)
            .on(OtRequest.employee == Employee.name)
            .inner_join(ShiftType)
            .on(OtRequest.shift == ShiftType.name)
            .where(query)
            .offset(start)
            .limit(page_size)
            .orderby(OtRequest.posting_date, order=sortDefault)
            .select(OtRequest.name,
                    OtRequest.employee,
                    OtRequest.employee_name,
                    UNIX_TIMESTAMP(OtRequest.ot_date).as_("ot_date"),
                    OtRequest.shift,OtRequest.ot_start_time,OtRequest.ot_end_time,
                    OtRequest.ot_approver,UNIX_TIMESTAMP(OtRequest.posting_date).as_("posting_date"),
                    OtRequest.suggested_time,OtRequest.reason, OtRequest.status, ShiftType.start_time, ShiftType.end_time, Employee.image, Employee.department)
            .run(as_dict=True)
        )
        if len(list_ot_rq) > 0 :
            for rq in list_ot_rq :
                rq['image'] = validate_image(rq.get("image"))
                info_approvers = frappe.db.get_value("Employee",employee_id, ['image', "user_id", "employee_name"],as_dict=True)
                rq["approver"] = {
                    "image": validate_image(info_approvers.get('image')),
                    "name_approver": info_approvers.get('employee_name'),
                    "email": info_approvers.get('user_id')
                }
        gen_response(200,"",{
            "data": list_ot_rq
        } ) 
    except Exception as e:
        exception_handel(e)