import frappe
from frappe.utils import (
    sbool,
)
from frappe.monitor import add_data_to_monitor
from pypika import Order, CustomFunction, Tuple
from frappe.desk.query_report import (get_prepared_report_result)
import json
from mbw_service_v2.api.common import (
    gen_response,
    generate_report_result,
    get_report_doc,
    get_employee_id,
    last_day_of_month,
    exception_handel,
    get_language,
    get_employee_by_name
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
def get_report_monthly(filters={},overview=True):
    report = get_report_doc("MBW Monthly Attendance Sheet vi v2")
    user = frappe.session.user
    filters = json.loads(filters)
    employee = get_employee_id()
    ok = validate_link("Employee",employee,json.dumps(["company"]))
    filters["summarized_view"] = True if sbool(overview) == True else False
    filters["employee"] = employee
    filters['company'] = ok.get('company')
    result = generate_report_result(report, filters, user, False, None)
    # print("result",result)
    const_fiel = ["employee","employee_name","total_present","total_hours","total_leaves","total_absent","total_holidays","unmarked_days","total_late_entries","time_late_entries","total_early_exits","time_early_exits","shift"]
    if result :
        result = result[0] 
        vacation = []
        key_del = []
        for key,value in result.items():
            if key not in const_fiel :
                if filters["summarized_view"]: 
                    leave_type =  frappe.db.get_value("Leave Type", key.replace("_"," "),['*'],as_dict=1)
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

        from_day = datetime(year=year, month=1, day=1)
        end_day = datetime(year=year, month=12, day=31)
        filters = {"from_date": from_day, "to_date": end_day,
                   "docstatus": "Submitted", "currency": currency}
        filters["summarized_view"] = True
        filters["docname"] = username
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

            leave_allocation = {
                "name": d,
                "leave_type_name": leave_type.get('leave_type_name'),
                "total_allocated_leaves": flt(allocation.total_leaves_allocated, precision),
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
        report = get_report_doc("Employee Advance Summary MBW")
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
            'total_advance_amount': 0,
            'total_paid_amount': 0,
            'total_claimed_amount': 0,
            'total_pending_amount': 0,
            'total_return_amount': 0,
        }
        if report_info:
            total_advance_amount = report_info[-1][4] if report_info[-1][4] else 0
            total_paid_amount = report_info[-1][5] if report_info[-1][5] else 0 
            total_claimed_amount = report_info[-1][6] if report_info[-1][6] else 0
            total_pending_amount = report_info[-1][7] if report_info[-1][7] else 0
            total_return_amount = report_info[-1][8] if report_info[-1][8] else 0
            result = {
                'total_advance_amount': total_advance_amount,
                'total_paid_amount': total_paid_amount,
                'total_claimed_amount': total_claimed_amount,
                'total_pending_amount': total_pending_amount,
                'total_return_amount': total_return_amount,
            }

            
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        exception_handel(e)


def valid_value(value):
    return value if value else ""

@frappe.whitelist(methods="GET")
def get_report_attendance_sheet(**data):
    try:
        print(data)
        name_employee = data.get('employee')
        str_date = data.get('year') + "-" + data.get('month') + "-" + data.get('day')
        
        employee = get_employee_by_name(name_employee, ["name", "employee_name", "company", "department", "designation"])
        Attendance = frappe.qb.DocType('Attendance')
        ShiftAssignment = frappe.qb.DocType('Shift Assignment')
        LeaveApplication = frappe.qb.DocType('Leave Application')
        LeaveType = frappe.qb.DocType('Leave Type')
        ShiftType = frappe.qb.DocType('Shift Type')
        AttendanceRequest = frappe.qb.DocType('Attendance Request')
        format_day = '%d-%m-%Y'
        DATE_FORMAT = CustomFunction('DATE_FORMAT', ['date', 'format_day'])
        
        # get Information synthesis
        attendances = (frappe.qb.from_(Attendance)
                    .inner_join(ShiftType)
                    .on(Attendance.shift == ShiftType.name)
                    .where((Attendance.employee == name_employee) & (Attendance.attendance_date == str_date))
                    .select(Attendance.name, Attendance.working_hours,Attendance.late_check_in,Attendance.early_check_out, ShiftType.total_shift_time, ShiftType.exchange_to_working_day)
                    .run(as_dict=True))
        
        cong_lam_viec_trong_ngay = 0
        thoi_gian_lam_viec_trong_ngay = 0
        so_phut_di_muon_trong_ngay = 0
        so_phut_ve_som_trong_ngay = 0
        so_cong_tang_ca_trong_ngay = 0
        so_gio_tang_ca_trong_ngay = 0
        for att in attendances:
            cong_lam_viec_trong_ngay += round(att.get('working_hours') / att.get('total_shift_time') * att.get('exchange_to_working_day'), 2)
            thoi_gian_lam_viec_trong_ngay += att.get('working_hours')
            so_phut_di_muon_trong_ngay += att.get('late_check_in')
            so_phut_ve_som_trong_ngay += att.get('early_check_out')
        
        info_employee = {
            "Thông tin nhân sự": {
                "Nhân sự": valid_value(employee.get("name")),
                "Tên nhân sự": valid_value(employee.get("employee_name")),
                "Công ty": valid_value(employee.get("company")),
                "Bộ phận": valid_value(employee.get("department")),
                "Chức vụ": valid_value(employee.get("designation")),
            },
            "Công làm việc trong ngày": cong_lam_viec_trong_ngay,
            "Thời gian làm việc trong ngày": thoi_gian_lam_viec_trong_ngay,
            "Số phút đi muộn trong ngày": so_phut_di_muon_trong_ngay,
            "Số phút về sớm trong ngày": so_phut_ve_som_trong_ngay,
            "Số công tăng ca trong ngày": so_cong_tang_ca_trong_ngay,
            "Số giờ tăng ca trong ngày": so_gio_tang_ca_trong_ngay
        }
        
        # get Work shift information
        shift_information = []
        
        # get leaves
        data_leave = []
        leave_application = (frappe.qb.from_(LeaveApplication)
                    .inner_join(LeaveType)
                    .on(LeaveApplication.leave_type == LeaveType.name)
                    .where((LeaveApplication.employee == name_employee) & (LeaveApplication.from_date >= str_date) & (LeaveApplication.to_date <= str_date))
                    .select(LeaveApplication.name,DATE_FORMAT(LeaveApplication.creation, format_day).as_("creation"), LeaveApplication.leave_type, LeaveApplication.custom_shift_type,LeaveType.is_lwp,LeaveApplication.status)
                    .run(as_dict=True))

        for leave in leave_application:
            shift_type = leave.get('custom_shift_type') if leave.get('custom_shift_type') else "Cả ngày"
            attendance_change = 1
            data_leave.append({
                "leave_type": leave.get("leave_type"),
                "creation": leave.get("creation"),
                "shift_type": shift_type,
                "attendance_change": attendance_change,
                "status": leave.get("status"),
                "name": leave.get("name"),
                "receive_salary": leave.get("is_lwp"),
            })
        
        attendance_request = (frappe.qb.from_(AttendanceRequest)
                    .where((AttendanceRequest.employee == name_employee) & (AttendanceRequest.from_date >= str_date) & (AttendanceRequest.to_date <= str_date))
                    .select(AttendanceRequest.name,DATE_FORMAT(AttendanceRequest.creation, format_day).as_("creation"), AttendanceRequest.custom_shift,AttendanceRequest.docstatus)
                    .run(as_dict=True))
        for leave in attendance_request:
            shift_type = leave.get('custom_shift') if leave.get('custom_shift') else "Cả ngày"
            attendance_change = 1
            receive_salary = 1
            data_leave.append({
                "leave_type": "Giải trình chấm công",
                "creation": leave.get("creation"),
                "shift_type": shift_type,
                "attendance_change": attendance_change,
                "status": leave.get("docstatus"),
                "name": leave.get("name"),
                "receive_salary": receive_salary,
            })

        leaves = {
            "head_table": ["Loại đơn", "Ngày tạo", "Ca áp dụng", "Công thay đổi", "Trạng thái", "Chi tiết đơn", "Hưởng lương"],
            "data_leave": data_leave,
        }
        
        print(leaves)
        
        result = {"info_employee": info_employee, "shift_information": shift_information, "leaves": leaves}
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])