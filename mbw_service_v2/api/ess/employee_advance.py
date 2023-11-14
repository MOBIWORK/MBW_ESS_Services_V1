import frappe
from datetime import datetime, timedelta
from calendar import monthrange

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    get_language,
    validate_image
)
from mbw_service_v2.config_translate import i18n

@frappe.whitelist(methods='GET')
def get_list_employee_advance(**kwargs):
    try:
        employee_id = get_employee_id()
        status = kwargs.get('status')

        this_time = datetime.now()
        this_month = this_time.month
        this_year = this_time.year
        day_in_mon = monthrange(this_year, this_month)

        from_day = datetime(year=this_year, month=this_month, day=1)
        str_end_day = datetime(
            year=this_year, month=this_month, day=day_in_mon[1])
        end_day = datetime.fromtimestamp(datetime.strptime(
            str(str_end_day), "%Y-%m-%d %H:%M:%S").timestamp() + 24*60*60)

        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size
        
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
        }

        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        message = e
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
