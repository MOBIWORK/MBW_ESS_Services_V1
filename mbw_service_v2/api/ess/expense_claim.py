import frappe
from mbw_service_v2.api.common import (
    gen_response,
    generate_report_result,
    get_report_doc,
    get_employee_id,
    last_day_of_month,
    exception_handel,
    get_language
)

from frappe.desk.search import search_link
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_employee_currency
from hrms.hr.doctype.employee_advance.employee_advance import get_pending_amount
from datetime import datetime
from frappe.client import validate_link
import json
from mbw_service_v2.config_translate import i18n

@frappe.whitelist(methods="POST")
def create_employee_advance(**data):
    try:
        employee = get_employee_id()
        posting_date = datetime.now().date()
        ok = validate_link("Employee",employee,json.dumps(["company","employee_name","department", "employee"]))
        currency = get_employee_currency(employee=ok.get("employee"))
        pedding_amount = get_pending_amount(employee=ok.get("employee"),posting_date = posting_date)
        account_advance = validate_link(doctype="Company",docname=ok.get('company'), fields= json.dumps(["default_employee_advance_account"]) )

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

    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])