import frappe

from mbw_service_v2.api.common import (gen_response,exception_handel, get_language, get_employee_id, validate_datetime, validate_empty,get_user_id, get_employee_by_user)
from pypika import Order, CustomFunction, Tuple
from datetime import datetime

from mbw_service_v2.config_translate import i18n
from frappe.utils import ( cint, flt )
from hrms.hr.doctype.leave_application.leave_application import (get_leave_allocation_records, get_leave_balance_on, get_leaves_for_period, get_leaves_pending_approval_for_period, get_leave_approver)

@frappe.whitelist(methods='GET')
def get_detail_leave(name):
    employee_id = get_employee_id()
    Employee = frappe.qb.DocType('Employee')
    UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
    LeaveApplication = frappe.qb.DocType('Leave Application')  
    leave_allocation = (frappe.qb.from_(LeaveApplication)
                              .inner_join(Employee)
                              .on(LeaveApplication.leave_approver == Employee.user_id)
                              .where((LeaveApplication.employee == employee_id) & (LeaveApplication.name == name))
                              .orderby(LeaveApplication.creation, order=Order.desc)
                              .select(LeaveApplication.name,LeaveApplication.employee_name,LeaveApplication.employee, UNIX_TIMESTAMP(LeaveApplication.creation).as_("creation"),UNIX_TIMESTAMP(LeaveApplication.from_date).as_("from_date"),UNIX_TIMESTAMP(LeaveApplication.to_date).as_("to_date"),LeaveApplication.half_day, UNIX_TIMESTAMP(LeaveApplication.half_day_date).as_("half_day_date"), LeaveApplication.total_leave_days ,LeaveApplication.leave_type, LeaveApplication.status,LeaveApplication.leave_approver,LeaveApplication.description ,Employee.image.as_("avatar_approver")).run(as_dict=True))
    
    employee = (frappe.qb.from_(Employee)
                .where(Employee.name == employee_id)
                .select(Employee.image.as_("avatar_employee")).run(as_dict=True))

    gen_response(200, i18n.t('translate.error', locale=get_language()), {
        "leave_allowcation" : leave_allocation[0],
        "avata_employee": employee[0]
    })

@frappe.whitelist()
def get_list_leave(**kwargs):
    try:
        employee_id = get_employee_id()
        kwargs = frappe._dict(kwargs)
        my_filter = {}
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        leave_type = kwargs.get('leave_type')
        status = kwargs.get('status')
        employee = kwargs.get('employee')
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
        query_code = (LeaveApplication.employee == employee_id)
        if leave_type:
            query_code = query_code & (LeaveApplication.leave_type == leave_type)
        if status:
            query_code = query_code & LeaveApplication.status == status
        if employee:
            query_code = query_code  & LeaveApplication.employee == employee
        if (start_time) and (end_time):
            query_code = query_code & (LeaveApplication.creation.between(start_time, end_time))
        leave_allocation = (frappe.qb.from_(LeaveApplication)
                              .inner_join(Employee)
                              .on(LeaveApplication.leave_approver == Employee.user_id)
                              .offset(start)
                              .limit(page_size)
                              .where(query_code)
                              .orderby(LeaveApplication.creation, order=Order.desc)
                              .select(LeaveApplication.name,LeaveApplication.employee_name,LeaveApplication.employee, UNIX_TIMESTAMP(LeaveApplication.creation).as_("creation"), LeaveApplication.leave_type, LeaveApplication.status,LeaveApplication.leave_approver,LeaveApplication.half_day,UNIX_TIMESTAMP(LeaveApplication.half_day_date).as_("half_day_date") ,Employee.image).run(as_dict=True)
                              )
        queryOpen = frappe.db.count('Leave Application', {'status': 'Open', 'employee': employee_id})
        queryApprover = frappe.db.count('Leave Application', {'status': 'Approved', 'employee': employee_id})
        queryReject = frappe.db.count('Leave Application', {'status': 'Rejected', 'employee': employee_id})
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "leave_allocation": leave_allocation,
            "queryOpen": queryOpen,
            "queryApprover": queryApprover,
            "queryReject": queryReject
        })
    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])

@frappe.whitelist(methods="POST")
def create_leave(**kwargs):
    try:
        employee_id = get_employee_id()
        employee = frappe.get_doc('Employee', employee_id)
        leave_approver = employee.get('leave_approver')
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        # half_day = kwargs.get('half_day')
        new_doc = frappe.new_doc("Leave Application")
        new_doc.employee = employee_id
        new_doc.leave_type = validate_empty(kwargs.get("leave_type"))
        new_doc.posting_date = datetime.now().date()
        if from_date > to_date:
            gen_response(500, i18n.t('translate.title_3', locale=get_language()))
            return None
        
        if from_date == to_date and kwargs.get('half_day') == True:
            new_doc.half_day = True
            new_doc.half_day_date = validate_datetime(from_date)
        elif(from_date < to_date and kwargs.get('half_day') == True):
            if(kwargs.get('half_day_date') >= from_date and kwargs.get('half_day_date') <= to_date):
                print("====", kwargs.get('half_day_date') >= from_date and kwargs.get('half_day_date') <= to_date)
                new_doc.half_day = True
                new_doc.half_day_date = validate_datetime(kwargs.get('half_day_date'))
            else: 
                return gen_response(500, i18n.t('translate.title_4', locale=get_language()), [])
        
        new_doc.from_date = validate_datetime(from_date)
        new_doc.to_date = validate_datetime(to_date)
        new_doc.leave_approver = leave_approver
        new_doc.description = kwargs.get('description')
        new_doc.insert()
        gen_response(201, i18n.t('translate.create_success', locale=get_language()))
    
    except Exception as e:
        if hasattr(e, "http_status_code") and e.http_status_code == 417:
            gen_response(417, f"{i18n.t('translate.employee', locale=get_language())} {employee_id} {i18n.t('translate.title_2', locale=get_language())} {new_doc.leave_type} {i18n.t('translate.from_date', locale=get_language())} {(new_doc.from_date).strftime('%d-%m-%Y')} {i18n.t('translate.to_date', locale=get_language())} {(new_doc.to_date).strftime('%d-%m-%Y')}")
        else:   exception_handel(e)

@frappe.whitelist(methods="GET")
def get_list_leave_type(**kwargs):
    try:
        leave_type = frappe.db.get_list('Leave Type', fields=["name", "leave_type_name"])
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), leave_type)
    except Exception as e:
        return exception_handel(e)

@frappe.whitelist()
def get_leave_details():
    employee = get_employee_id()
    leave_approver = get_employee_by_user(get_user_id(), ["*"]).get("leave_approver")
    date = datetime.now().date()
    allocation_records = get_leave_allocation_records(employee, date)
    leave_allocation = {}
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))

    for d in allocation_records:
        allocation = allocation_records.get(d, frappe._dict())
        remaining_leaves = get_leave_balance_on(
            employee, d, date, to_date=allocation.to_date, consider_all_leaves_in_the_allocation_period=True
        )

        end_date = allocation.to_date
        leaves_taken = get_leaves_for_period(employee, d, allocation.from_date, end_date) * -1
        leaves_pending = get_leaves_pending_approval_for_period(
            employee, d, allocation.from_date, end_date
        )
        expired_leaves = allocation.total_leaves_allocated - (remaining_leaves + leaves_taken)

        leave_allocation[d] = {
            "total_leaves": flt(allocation.total_leaves_allocated, precision),
            "expired_leaves": flt(expired_leaves, precision) if expired_leaves > 0 else 0,
            "leaves_taken": flt(leaves_taken, precision),
            "leaves_pending_approval": flt(leaves_pending, precision),
            "remaining_leaves": flt(remaining_leaves, precision),
        }
    
    Employee = frappe.qb.DocType('Employee')
    query_code = (Employee.user_id == leave_approver)
    query_approver = (frappe.qb.from_(Employee)
                            .where(query_code)
                            .select(Employee.user_id.as_("leave_approver") ,Employee.image).run(as_dict=True)
                            )

    # is used in set query
    lwp = frappe.get_list("Leave Type", filters={"is_lwp": 1}, pluck="name")
    
    gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
        "leave_allocation": leave_allocation,
        "leave_approver": query_approver[0],
        "lwps": lwp,
    })