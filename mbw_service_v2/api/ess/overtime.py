import frappe
import json
from mbw_service_v2.api.common import  (get_last_check, gen_response,get_employee_id,exception_handel,get_language,get_shift_type_now,
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


# created ot request
@frappe.whitelist(methods="POST")
def create_ot_request(**data):
    try:
        data = dict(data)
        new_ot_rq = frappe.new_doc("Overtime Request")
        employee = get_employee_id()
        ot_date = datetime.fromtimestamp(int(data.get('ot_date'))).date()  if data.get('ot_date') else False
        shift = data.get('shift') if data.get('shift') else False
        ot_start_time = datetime.strptime(data.get('ot_start_time'), "%H:%M").time()  if data.get('ot_start_time') else False
        ot_end_time = datetime.strptime(data.get('ot_end_time'), "%H:%M").time() if data.get('ot_end_time') else False
        ot_approver = data.get('ot_approver') if data.get('ot_approver') else False
        if not ( ot_date or shift or ot_start_time or ot_end_time or ot_approver ) :
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), []) 
            return
        del data['cmd']
        data['employee'] = employee
        data['ot_date'] = ot_date
        data['posting_date'] = datetime.now().date()
        data['suggested_time'] = (ot_end_time.hour*60 + ot_end_time.minute  - (ot_start_time.hour*60 + ot_start_time.minute))/60
        field_in = ["ot_date", "shift", "ot_start_time", "ot_end_time", "ot_approver", "posting_date","employee","suggested_time"]
        for field, value in data.items() :
            if field not in field_in: 
                gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), []) 
                return
            setattr(new_ot_rq, field, value)
        new_ot_rq.insert()
        gen_response(201, "", new_ot_rq)
    except frappe.DoesNotExistError:
        gen_response(404, i18n.t('translate.error', locale=get_language()), []) 

# update ot request
@frappe.whitelist(methods="PATCH")
def update_ot_request(**data):
    try:
        data = dict(data)
        ot_name = data.get("name")
        ot_rq = frappe.get_doc("Overtime Request",ot_name)
        ot_date = datetime.fromtimestamp(int(data.get('ot_date'))).date()  if data.get('ot_date') else False
        shift = data.get('shift') if data.get('shift') else False
        ot_start_time = datetime.strptime(data.get('ot_start_time'), "%H:%M").time()  if data.get('ot_start_time') else False
        ot_end_time = datetime.strptime(data.get('ot_end_time'), "%H:%M").time() if data.get('ot_end_time') else False
        ot_approver = data.get('ot_approver') if data.get('ot_approver') else False
        if not ( ot_date or shift or ot_start_time or ot_end_time or ot_approver ) :
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), []) 
            return
        del data['cmd']
        data['ot_date'] = ot_date
        data['suggested_time'] = (ot_end_time.hour*60 + ot_end_time.minute  - (ot_start_time.hour*60 + ot_start_time.minute))/60
        # field_in = ["ot_date", "shift", "ot_start_time", "ot_end_time", "ot_approver", "posting_date","suggested_time"]
        for field, value in data.items() :
            setattr(ot_rq, field, value)
        ot_rq.save()
        gen_response(201, "", ot_rq)
    except frappe.DoesNotExistError:
        gen_response(404, i18n.t('translate.error', locale=get_language()), []) 


# ot list
@frappe.whitelist(methods='GET')
def get_list_ot_request():
    try:
        employee_id = get_employee_id()
        list_ot = frappe.db.get_list("Overtime Request",["name","ot_date", "shift", "ot_start_time", "ot_end_time", "ot_approver", "posting_date","employee","suggested_time","status"])
        queryDraft = frappe.db.count('Overtime Request', {'workflow_state': "Draft", 'employee': employee_id})
        queryApproved = frappe.db.count('Overtime Request', {'workflow_state': "Approved", 'employee': employee_id})
        queryRejected = frappe.db.count('Overtime Request', {'workflow_state': "Rejected", 'employee': employee_id})

        gen_response(200,"",{
            "list_ot": list_ot,
            "Draft": queryDraft,
            "Approved": queryApproved,
            "Rejected": queryRejected,
        } ) 
    except Exception as e:
        exception_handel(e)


# delete a ot request
@frappe.whitelist(methods="DELETE")
def delete_ot_request(name):
    try:

        frappe.delete_doc('Overtime Request',name)
        gen_response(200, i18n.t('translate.delete_success', locale=get_language()),[])
    except Exception as e:
        exception_handel(e)


#get ot approver
@frappe.whitelist(methods="GET")
def get_ot_approver():
    try:
        from frappe.client import validate_link
        employee = get_employee_id()
        approver = validate_link(doctype='Employee',docname= employee,fields=json.dumps(["employee_name","department","ot_approver"]))
        Employee = frappe.qb.DocType("Employee")
        User = frappe.qb.DocType("User")
        approver_info = (frappe.qb.from_(User)
                         .inner_join(Employee)
                         .on(User.email == Employee.user_id)
                         .where(User.email ==  approver['ot_approver'])
                         .select(Employee.employee_name.as_("full_name"),Employee.image,User.email)
                         .run(as_dict=True)
                         )
        for info in approver_info:
            info['image'] = validate_image(info.get("image"))
        gen_response(200,i18n.t('translate.successfully', locale=get_language()),approver_info)
    except Exception as e :
        exception_handel(e )
