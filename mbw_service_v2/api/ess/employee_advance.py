import frappe
from datetime import datetime, timedelta
from calendar import monthrange

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    get_language
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

        my_filter = {
            'creation': ['>=', from_day],
            'creation': ['<=', end_day],
            'employee': employee_id
        }

        if status:
            my_filter['status'] = status

        total_doc = frappe.db.count('Employee Advance', my_filter)
        lst_employee_advance = frappe.db.get_list(
            'Employee Advance',
            filters=my_filter,
            fields=['name', 'purpose', 'advance_amount',
                    'UNIX_TIMESTAMP(creation) as creation', 'status'],
            order_by='creation desc',
            start=start,
            page_length=page_size
        )

        result = {
            "data": lst_employee_advance,
            "total_doc": total_doc
        }

        return gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        message = e
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
