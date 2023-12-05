import frappe
from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    get_language,
    validate_image
)

from frappe.desk.search import search_link
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_employee_currency
from hrms.hr.doctype.employee_advance.employee_advance import get_pending_amount
from datetime import datetime
from frappe.client import validate_link
import json
from mbw_service_v2.config_translate import i18n

#create advance
@frappe.whitelist(methods="POST")
def create_employee_advance(**data):
    try:
        employee = get_employee_id()
        posting_date = datetime.now().date()
        ok = validate_link("Employee",employee,json.dumps(["company","employee_name","department", "employee"]))
        currency = get_employee_currency(employee=ok.get("employee"))
        pedding_amount = get_pending_amount(employee=ok.get("employee"),posting_date = posting_date)
        account_advance = validate_link(doctype="Company",docname=ok.get('company'), fields= json.dumps(["default_employee_advance_account"]) )
        if account_advance:
            data['docstatus'] = 0
            data["posting_date"] = posting_date
            data['currency'] = currency
            data['company'] = ok.get('company')
            data['employee'] = ok.get('employee')
            data['exchange_rate'] = 1
            data['advance_account'] = account_advance['default_employee_advance_account']
            data['employee_name'] = ok.get('employee_name')
            data['department'] = ok.get('department')
            data["pending_amount"] =pedding_amount
            new_advance =frappe.new_doc("Employee Advance")

            for field, value in dict(data).items():
                setattr(new_advance, field, value)
            new_advance.insert()

            gen_response(201,i18n.t('translate.create_success', locale=get_language()),new_advance)
            return
        gen_response(500, i18n.t('translate.error', locale=get_language()), False)

    except Exception as e:
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])



@frappe.whitelist(methods="GET")
def get_pedding_amount():
    try: 
        today = datetime.now().date()
        employee = get_employee_id()
        employee_due_amount = frappe.get_all(
		"Employee Advance",
		filters={"employee": employee, "docstatus": 1, "posting_date": ("<=", today)},
		fields=["advance_amount", "paid_amount"],
        )
        total =  sum([(emp.advance_amount - emp.paid_amount) for emp in employee_due_amount])
        gen_response(200, "",{"total":total})
    except Exception as e:
        exception_handel(e)

@frappe.whitelist(methods="GET")
def get_approved_amount():
    try:
        EmployeeD = frappe.qb.DocType("Employee")
        employee_id = get_employee_id()
        employee_detail = frappe.get_doc("Employee",employee_id)
        expense_approver = employee_detail.get('expense_approver')
        if not expense_approver :
            gen_response(404,i18n.t('translate.notfound', locale=get_language()),False)
            return
        info_approve = frappe.db.get_value("Employee",{"user_id": expense_approver},['employee_name',"user_id", "image"],as_dict=1)
        info_approve['image'] = validate_image(info_approve['image'])
        info_approve['full_name'] = info_approve['employee_name']
        info_approve['email'] = info_approve['user_id']
        
        del info_approve['employee_name']
        del info_approve['user_id']
        gen_response(200,"",info_approve) 
    except Exception as e:
        exception_handel(e)