import frappe
from frappe.utils import (
    sbool,
)
from frappe import _
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

FORMAT_DAY = '%d-%m-%Y'
FORMAT_HOUR = '%H:%m:%s'
DATE_FORMAT = CustomFunction('DATE_FORMAT', ['date', 'format'])
    
@frappe.whitelist()
@frappe.read_only()
def get_report_monthly(filters={},overview=True):
    try:
        report = get_report_doc("MBW Monthly Attendance Sheet vi v2")
        user = frappe.session.user
        filters = json.loads(filters)
        employee = get_employee_id()
        ok = validate_link("Employee",employee,json.dumps(["company"]))
        filters["summarized_view"] = True if sbool(overview) == True else False
        filters["employee"] = employee
        filters['company'] = ok.get('company')
        result = generate_report_result(report, filters, user, False, None)
        print("result",result)
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
        if not result: 
            result = []
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        exception_handel(e)

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
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])

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

def get_work_shift(name_employee, str_date):
    EmployeeCheckin = frappe.qb.DocType('Employee Checkin')
    Attendance = frappe.qb.DocType('Attendance')
    LeaveApplication = frappe.qb.DocType('Leave Application')
    LeaveType = frappe.qb.DocType('Leave Type')
    ShiftType = frappe.qb.DocType('Shift Type')
    AttendanceRequest = frappe.qb.DocType('Attendance Request')
    
    employee_checkin = (frappe.qb.from_(EmployeeCheckin)
                .inner_join(Attendance)
                .on(EmployeeCheckin.attendance == Attendance.name)
                .inner_join(ShiftType)
                .on(EmployeeCheckin.shift == ShiftType.name)
                .where((Attendance.employee == name_employee) & (Attendance.attendance_date == str_date))
                .select(EmployeeCheckin.name.as_("name_checkin"), DATE_FORMAT(ShiftType.start_time, FORMAT_HOUR).as_("start_time"), DATE_FORMAT(ShiftType.end_time, FORMAT_HOUR).as_("end_time"), ShiftType.name.as_("name_shift_type"),ShiftType.exchange_to_working_day, DATE_FORMAT(Attendance.in_time, FORMAT_HOUR).as_("in_time"), DATE_FORMAT(Attendance.out_time, FORMAT_HOUR).as_("out_time"), Attendance.working_hours, ShiftType.total_shift_time, EmployeeCheckin.log_type, EmployeeCheckin.attendance)
                .run(as_dict=True))

    dict_checkin = {}
    for checkin in employee_checkin:
        attendance_name = checkin.get('attendance')
        name_checkin = checkin.get('name_checkin')
        log_type = str(checkin.get('log_type'))
        data_check = dict_checkin.get(attendance_name)
        if not data_check:
            work_hour = str(checkin.get('start_time')) + ' - ' + str(checkin.get('end_time'))
            reality_hour = str(checkin.get('in_time')) + ' - ' + str(checkin.get('out_time'))
            reality_attendance_work = 0
            working_hours = checkin.get('working_hours')
            total_shift_time = checkin.get('total_shift_time')
            if working_hours > total_shift_time:
                working_hours = total_shift_time
            if total_shift_time != 0:
                reality_attendance_work = round(working_hours / total_shift_time * checkin.get('exchange_to_working_day'), 2)
            
            dict_checkin[attendance_name] = {
                "attendance": attendance_name,
                "shift_name": checkin.get('name_shift_type'),
                "work_hour": work_hour,
                "attendance_work": checkin.get('exchange_to_working_day'),
                "reality_hour": reality_hour,
                "reality_attendance_work": reality_attendance_work,
                "checkin": [
                    {
                        "label": f"{log_type}: {name_checkin}",
                        "link": f"/app/employee-checkin/{name_checkin}"
                    }
                ]
            }
        else:
            data_check['checkin'].append({
                        "label": f"{log_type}: {name_checkin}",
                        "link": f"/app/employee-checkin/{name_checkin}"
                    })
            dict_checkin[attendance_name] = data_check

    return dict_checkin.values()

def get_leaves(name_employee, str_date):
    Attendance = frappe.qb.DocType('Attendance')
    LeaveApplication = frappe.qb.DocType('Leave Application')
    LeaveType = frappe.qb.DocType('Leave Type')
    ShiftType = frappe.qb.DocType('Shift Type')
    AttendanceRequest = frappe.qb.DocType('Attendance Request')
    data_leave = []
    leave_application = (frappe.qb.from_(LeaveApplication)
                .inner_join(LeaveType)
                .on(LeaveApplication.leave_type == LeaveType.name)
                .inner_join(Attendance)
                .on(LeaveApplication.name == Attendance.leave_application)
                .inner_join(ShiftType)
                .on(Attendance.shift == ShiftType.name)
                .where((LeaveApplication.employee == name_employee) & (LeaveApplication.from_date <= str_date) & (LeaveApplication.to_date >= str_date))
                .select(LeaveApplication.name,DATE_FORMAT(LeaveApplication.creation, FORMAT_DAY).as_("creation"), LeaveApplication.leave_type, Attendance.shift,LeaveType.is_lwp,LeaveApplication.status, LeaveApplication.half_day_date, ShiftType.exchange_to_working_day)
                .run(as_dict=True))

    for leave in leave_application:
        if leave.get("status") == "Open":
            status_leave = _("Chờ duyệt")
        elif leave.get("status") == "Approved":
            status_leave = _("Đã duyệt")
        elif leave.get("status") == "Rejected":
            status_leave = _("Từ chối")
        else:
            status_leave = _("Đã hủy")
        
        name = leave.get("name")
        data_leave.append({
            "name": name,
            "leave_type": leave.get("leave_type"),
            "creation": leave.get("creation"),
            "shift": leave.get("shift") if leave.get("shift") else "",
            "attendance_change": leave.exchange_to_working_day,
            "status": status_leave,
            "receive_salary": _("Có") if leave.get("is_lwp") == 0 else _("Không"),
            "link": f"/app/leave-application/{name}"
        })
    
    attendance_request = (frappe.qb.from_(AttendanceRequest)
                .inner_join(Attendance)
                .on(AttendanceRequest.name == Attendance.attendance_request)
                .inner_join(ShiftType)
                .on(Attendance.shift == ShiftType.name)
                .where((AttendanceRequest.employee == name_employee) & (AttendanceRequest.from_date <= str_date) & (AttendanceRequest.to_date >= str_date))
                .select(AttendanceRequest.name,DATE_FORMAT(AttendanceRequest.creation, FORMAT_DAY).as_("creation"), AttendanceRequest.custom_shift,AttendanceRequest.half_day_date,AttendanceRequest.docstatus, Attendance.shift,ShiftType.exchange_to_working_day)
                .run(as_dict=True))

    for leave in attendance_request:
        if leave.get("docstatus") == 0:
            status_leave = _("Chờ duyệt")
        elif leave.get("docstatus") == 1:
            status_leave = _("Đã duyệt")
        elif leave.get("docstatus") == 2:
            status_leave = _("Đã hủy")
        
        name = leave.get("name")
        data_leave.append({
            "leave_type": _("Giải trình chấm công"),
            "creation": leave.get("creation"),
            "shift": leave.get("shift") if leave.get("shift") else "",
            "attendance_change": leave.exchange_to_working_day,
            "status": status_leave,
            "name": name,
            "receive_salary": _("Có"),
            "link": f"/app/attendance-request/{name}"
        })
    return data_leave

def get_holiday(name_employee, str_date, employee):
    holidays = []
    new_holidays = []
    ShiftAssignment = frappe.qb.DocType('Shift Assignment')
    ShiftType = frappe.qb.DocType('Shift Type')
    Company = frappe.qb.DocType('Company')
    Holiday = frappe.qb.DocType('Holiday')
    
    shift_assignment = []
    # end_date has data
    shift_assignment_1 = (frappe.qb.from_(ShiftAssignment)
            .inner_join(ShiftType)
            .on(ShiftAssignment.shift_type == ShiftType.name)
            .where((ShiftAssignment.employee == name_employee) & (ShiftAssignment.start_date <= str_date) & (ShiftAssignment.end_date >= str_date))
            .select(ShiftType.name.as_('shift_type'), ShiftType.holiday_list)
            .run(as_dict=True))
    shift_assignment.extend(shift_assignment_1)
    # end_date has data
    shift_assignment_2 = (frappe.qb.from_(ShiftAssignment)
            .inner_join(ShiftType)
            .on(ShiftAssignment.shift_type == ShiftType.name)
            .where((ShiftAssignment.employee == name_employee) & (ShiftAssignment.start_date <= str_date) & (ShiftAssignment.end_date.isnull() | ShiftAssignment.end_date == ""))
            .select(ShiftType.name.as_('shift_type'), ShiftType.holiday_list)
            .run(as_dict=True))

    shift_assignment.extend(shift_assignment_2)

    for shift in shift_assignment:
        holiday_list = shift.get('holiday_list')
        if not holiday_list:
            holiday_list = employee.get('holiday_list')
            if not holiday_list:
                company = employee.get('company')
                if company:
                    holiday_list = frappe.db.get_value("Company",{"name": company},['default_holiday_list'])
        holiday = (frappe.qb.from_(Holiday)
                .where((Holiday.holiday_date == str_date) & (Holiday.parent == holiday_list))
                .select(DATE_FORMAT(Holiday.holiday_date, FORMAT_DAY).as_('holiday_date'), Holiday.description, Holiday.weekly_off)
                .run(as_dict=True))
        holidays.extend(holiday)
    
    stt = 0
    for hld in holidays:
        hld_check = list(filter(lambda item: item['holiday_date'] == hld.get('holiday_date'), new_holidays))
        if not hld_check:
            stt+=1
            new_holidays.append({
                "stt": stt,
                "holiday_date": hld.get('holiday_date'),
                "description": hld.get('description'),
                "receive_salary": _("Có") if hld.get("weekly_off") == 0 else _("Không"),
            })
    return new_holidays

@frappe.whitelist(methods="GET")
def get_report_attendance_sheet(**data):
    try:
        name_employee = data.get('employee')
        str_date = data.get('year') + "-" + data.get('month') + "-" + data.get('day')
        employee = get_employee_by_name(name_employee, ["name", "employee_name", "company", "department", "designation", "holiday_list"])
        EmployeeCheckin = frappe.qb.DocType('Employee Checkin')
        Attendance = frappe.qb.DocType('Attendance')
        LeaveApplication = frappe.qb.DocType('Leave Application')
        LeaveType = frappe.qb.DocType('Leave Type')
        ShiftType = frappe.qb.DocType('Shift Type')
        AttendanceRequest = frappe.qb.DocType('Attendance Request')
        
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
            working_hours = att.get('working_hours')
            total_shift_time = att.get('total_shift_time')
            if working_hours > total_shift_time:
                working_hours = total_shift_time
            if total_shift_time != 0:
                cong_lam_viec_trong_ngay += round(working_hours / total_shift_time * att.get('exchange_to_working_day'), 2)

            thoi_gian_lam_viec_trong_ngay += working_hours
            so_phut_di_muon_trong_ngay += att.get('late_check_in')
            so_phut_ve_som_trong_ngay += att.get('early_check_out')

        # get work shift
        work_shift = get_work_shift(name_employee, str_date)

        thong_tin_cham_cong = {
            "head_table": [_("Tên ca"), _("Giờ làm việc"), _("Công"), _("Giờ làm thực tế"), _("Công thực"), _("Dữ liệu chấm công")],
            "data": work_shift,
            "message_empty": _("Không có dữ liệu!")
        }
        
        info_synthesis = {
            "thong_tin_nhan_su": {
                "label": _("Thông tin nhân sự"),
                "value": {
                    "nhan_su": {
                        "label": _("Nhân sự"),
                        "value": valid_value(employee.get("name"))
                    },
                    "ten_nhan_su": {
                        "label": _("Tên nhân sự"),
                        "value": valid_value(employee.get("employee_name"))
                    },
                    "cong_ty": {
                        "label": _("Công ty"),
                        "value": valid_value(employee.get("company"))
                    },
                    "bo_phan": {
                        "label": _("Bộ phận"),
                        "value": valid_value(employee.get("department"))
                    },
                    "chuc_vu": {
                        "label": _("Chức vụ"),
                        "value": valid_value(employee.get("designation"))
                    }
                }
            },
            "cong_lam_viec_trong_ngay": {
                "label": _("Công làm việc trong ngày"),
                "value": cong_lam_viec_trong_ngay
                },
            "thoi_gian_lam_viec_trong_ngay": {
                "label": _("Thời gian làm việc trong ngày"),
                "value": thoi_gian_lam_viec_trong_ngay
                },
            "so_phut_di_muon_trong_ngay": {
                "label": _("Số phút đi muộn trong ngày"),
                "value": so_phut_di_muon_trong_ngay
                },
            "so_phut_ve_som_trong_ngay": {
                "label": _("Số phút về sớm trong ngày"),
                "value": so_phut_ve_som_trong_ngay
                },
            "so_cong_tang_ca_trong_ngay": {
                "label": _("Số công tăng ca trong ngày"),
                "value": so_cong_tang_ca_trong_ngay
                },
            "so_gio_tang_ca_trong_ngay": {
                "label": _("Số giờ tăng ca trong ngày"),
                "value": so_gio_tang_ca_trong_ngay
                },
            "thong_tin_cham_cong": {
                "label": _("Thông tin chấm công"),
                "value": thong_tin_cham_cong
                },
        }
        
        # get leaves
        leaves = {
            "head_table": [_("Loại đơn"), _("Ngày tạo"), _("Ca áp dụng"), _("Công thay đổi"), _("Trạng thái"), _("Chi tiết đơn"), _("Hưởng lương")],
            "data": get_leaves(name_employee, str_date),
            "message_empty": _("Không có dữ liệu!")
        }
        
        # get holiday
        holidays = {
            "head_table": [_("STT"), _("Ngày nghỉ"),_("Loại nghỉ"), _("Tính lương")],
            "data": get_holiday(name_employee, str_date, employee),
            "message_empty": _("Không có dữ liệu!")
        }
        
        result = {"info_synthesis": info_synthesis, "leaves": leaves, "holidays": holidays}
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])