import frappe
from datetime import datetime, timedelta
from calendar import monthrange

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    get_language,
    validate_image,
    get_report_doc
)
from mbw_service_v2.config_translate import i18n
from frappe.desk.query_report import generate_report_result as reportDefault

@frappe.whitelist(methods='GET')
def get_list_employee_advance(**kwargs):
    try:
        employee_id = get_employee_id()
        status = kwargs.get('status')

        this_time = datetime.now()
        this_month = this_time.month
        this_year = this_time.year
        day_in_mon = monthrange(this_year, this_month)

        # in month
        from_day = datetime(year=this_year, month=this_month, day=1)
        str_end_day = datetime(
            year=this_year, month=this_month, day=day_in_mon[1])
        end_day = datetime.fromtimestamp(datetime.strptime(
            str(str_end_day), "%Y-%m-%d %H:%M:%S").timestamp() + 24*60*60)

        # in year
        from_day_year = datetime(year=this_year, month=1, day=1)
        end_day_year = datetime(year=this_year+1, month=1, day=1)

        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        
        # get report
        report = get_report_doc("Employee Advance Summary")
        user = frappe.session.user
        filters = {"from_date": from_day_year, "to_date": end_day_year,
                   "status": status, "employee": employee_id}
        report_info = reportDefault(report, filters, user, False, None).get('result')
        if report_info:
            total_advance_amount = report_info[-1][4] if report_info[-1][4] else 0
            total_paid_amount = report_info[-1][5] if report_info[-1][5] else 0 
            total_claimed_amount = report_info[-1][6] if report_info[-1][6] else 0
        else:
            total_advance_amount = 0
            total_paid_amount = 0
            total_claimed_amount = 0
            
        # get approver
        employee_detail = frappe.get_doc("Employee",employee_id)
        expense_approver = employee_detail.get('expense_approver')
        
        info_approve = frappe.db.get_value("Employee",{"user_id": expense_approver},['employee_name',"user_id", "image"],as_dict=1)
        if info_approve:
            info_approve['image'] = validate_image(info_approve['image'])
            info_approve['full_name'] = info_approve['employee_name']
            info_approve['email'] = info_approve['user_id']
            
            del info_approve['employee_name']
            del info_approve['user_id']
        else:
            info_approve = {}

        my_filter = {
            'creation': ['>=', from_day],
            'creation': ['<=', end_day],
            'employee': employee_id
        }

        if status:
            my_filter['status'] = status
        
        # get list employee advances
        employee_advances = frappe.db.get_list(
            'Employee Advance',
            filters=my_filter,
            fields=['name', 'UNIX_TIMESTAMP(creation) as creation', 'advance_amount', 'paid_amount', 'pending_amount', 'claimed_amount','return_amount', 'status','company', 'purpose','repay_unclaimed_amount_from_salary','currency'],
            order_by='creation desc',
            start=start,
            page_length=page_size
        )
        
        for advance in employee_advances:
            advance['approver'] = info_approve

        result = {
            "data": employee_advances,
            "total_advance_amount": total_advance_amount,
            "total_paid_amount":  total_paid_amount,
            "total_claimed_amount":  total_claimed_amount,
        }

        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
