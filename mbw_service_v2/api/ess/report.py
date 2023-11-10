import frappe
from frappe.utils import (
    sbool,
)
from frappe.monitor import add_data_to_monitor
from frappe.desk.query_report import (get_prepared_report_result)
import json
from mbw_service_v2.api.common import (
    gen_response,
    generate_report_result,
    get_report_doc,
    get_employee_id,
    last_day_of_month,
    exception_handel,
    get_language

)
from frappe.desk.query_report import generate_report_result as reportDefault
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import (cint, flt)
from hrms.hr.doctype.leave_application.leave_application import (
    get_leave_allocation_records, get_leave_balance_on, get_leaves_for_period, get_leaves_pending_approval_for_period, get_leave_approver)
from frappe.utils import (
    sbool,
)

from frappe.client import validate_link
from mbw_service_v2.config_translate import i18n

@frappe.whitelist()
@frappe.read_only()
def get_report_monthly(
        filters={},
        overview=True
):
    
    # rs = frappe.getdoc("Report","Monthly Attendance Sheet")
    # return rs
    report = get_report_doc("MBW Monthly Attendance Sheet vi v2")
    user = frappe.session.user
    filters = json.loads(filters)
    employee = get_employee_id()
    ok = validate_link("Employee",employee,json.dumps(["company"]))
    filters["summarized_view"] = True if sbool(overview) == True else False
    filters["employee"] = employee
    filters['company'] = ok.get('company')
    result = generate_report_result(report, filters, user, False, None)
    const_fiel = ["employee","employee_name","total_present","total_hours","total_leaves","total_absent","total_holidays","unmarked_days","total_late_entries","time_late_entries","total_early_exits","time_early_exits","shift"]
    if result :
        result = result[0] 
        vacation = []
        key_del = []
        for key,value in result.items():
            if key not in const_fiel :
                if filters["summarized_view"]: 
                    leave_type =  frappe.db.get_value("Leave Type", key.replace("_"," "),['*'],as_dict=1)
                    print("value",leave_type)
                    if leave_type: 
                        vacation.append({leave_type.get("leave_type_name"):value})
                else :    vacation.append({key:value})

                key_del.append(key)
        for key_d in key_del : 
            del result[key_d]
        result["vacation"] = vacation

        
    add_data_to_monitor(report=report.reference_report or report.name)
    gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)


@frappe.whitelist()
@frappe.read_only()
def get_report_salary(**data):
    try:
        report = get_report_doc("Salary Register")
        user = frappe.session.user
        username = get_employee_id()
        this_time = datetime.now()
        this_month = this_time.month
        this_year = this_time.year

        year = this_year if not data.get('year') else int(data.get('year'))
        currency = "VND" if not data.get("currency") else data.get("currency")
        # end_day = last_day_of_month(this_time).date()
        # from_day = (end_day - relativedelta(months = this_month-7)).replace(day=1)
        from_day = datetime(year=year, month=1, day=1)
        end_day = datetime(year=year, month=12, day=31)
        filters = {"from_date": from_day, "to_date": end_day,
                   "docstatus": "Submitted", "currency": currency}
        filters["summarized_view"] = True
        filters["docname"] = username
        # print(filters)
        result = generate_report_result(report, filters, user, False, None)
        if result:
            result = result[0]
        add_data_to_monitor(report=report.reference_report or report.name)
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        exception_handel(e)


@frappe.whitelist()
def get_statistic_vacation_fund():
    try:
        employee_id = get_employee_id()
        date = datetime.now().date()
        allocation_records = get_leave_allocation_records(employee_id, date)
        precision = cint(frappe.db.get_single_value(
            "System Settings", "float_precision", cache=True))

        result = []

        leave_types = frappe.db.get_list(
            'Leave Type',
            filters={'name': ['in', [d for d in allocation_records]]},
            fields=['name', 'leave_type_name']
        )

        for d in allocation_records:
            leave_type = next(
                item for item in leave_types if item["name"] == d)
            if not leave_type:
                leave_type = {}

            allocation = allocation_records.get(d, frappe._dict())
            remaining_leaves = get_leave_balance_on(
                employee_id, d, date, to_date=allocation.to_date, consider_all_leaves_in_the_allocation_period=True
            )

            end_date = allocation.to_date
            # leaves_taken = get_leaves_for_period(
            #     employee_id, d, allocation.from_date, end_date) * -1
            # leaves_pending = get_leaves_pending_approval_for_period(
            #     employee_id, d, allocation.from_date, end_date
            # )
            # expired_leaves = allocation.total_leaves_allocated - \
            #     (remaining_leaves + leaves_taken)

            leave_allocation = {
                "name": d,
                "leave_type_name": leave_type.get('leave_type_name'),
                "total_allocated_leaves": flt(allocation.total_leaves_allocated, precision),
                # "expired_leaves": flt(expired_leaves, precision) if expired_leaves > 0 else 0,
                # "used_leaves": flt(leaves_taken, precision),
                # "pending_leaves": flt(leaves_pending, precision),
                "available_leaves": flt(remaining_leaves, precision),
            }
            result.append(leave_allocation)

        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        message = str(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])

@frappe.whitelist()
def get_report_advance(**data):
    try:
        report = get_report_doc("Employee Advance Summary")
        user = frappe.session.user
        username = get_employee_id()
        this_time = datetime.now()
        this_month = this_time.month
        this_year = this_time.year
        status = data.get("status")

        year = this_year if not data.get('year') else int(data.get('year'))
        from_day = datetime(year=year, month=1, day=1)
        end_day = datetime(year=year, month=12, day=31)
        filters = {"from_date": from_day, "to_date": end_day,
                   "status": status, "employee": username}
        report_info = reportDefault(report, filters, user, False, None).get('result')
        
        result = {
            # 'data': [],
            'total_advance_amount': 0,
            'total_paid_amount': 0,
            'total_claimed_amount': 0,
        }
        if report_info:
            total_advance_amount = report_info[-1][4] if report_info[-1][4] else 0
            total_paid_amount = report_info[-1][5] if report_info[-1][5] else 0 
            total_claimed_amount = report_info[-1][6] if report_info[-1][6] else 0
            result = {
                # 'data': report_info[0:-1],
                'total_advance_amount': total_advance_amount,
                'total_paid_amount': total_paid_amount,
                'total_claimed_amount': total_claimed_amount,
            }

            
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        exception_handel(e)