# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from calendar import monthrange
from itertools import groupby
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from datetime import datetime, date, timedelta
Filters = frappe._dict

status_off = {
    "Work From Home": "WFH",
    "On Leave": "L",
    "Holiday": "H",
    "Weekly Off": "WO",
    "Half Day": "HD",

}

leave_without_pay = {
    "Nghỉ không lương": "KL"
}

leave_with_pay = {
    "Work From Home": "WFH",
    "On Leave": "L",
    "Holiday": "H",
    "Half Day": "HD",

}

ot_type = {
    "Over Time": "OT"
}

status_map = {
    "Absent": "A",
    "Half Day": "HD",
    "Work From Home": "WFH",
    "On Leave": "L",
    "Holiday": "H",
    "Weekly Off": "WO",
}


day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

#ham tra ve data
def execute(filters: Optional[Filters] = None) -> Tuple:
    filters = frappe._dict(filters or {})

    if not (filters.month and filters.year):
        frappe.throw(_("Please select month and year."))

    attendance_map = get_attendance_map(filters)
    if not attendance_map:
        frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
        return [], [], None, None

    columns = get_columns(filters)
    data = get_data(filters, attendance_map)
    data_service_mobile = []

    if not data:
        frappe.msgprint(
            _("No attendance records found for this criteria."), alert=True, indicator="orange"
        )
        return columns, [], None, None
    for row in data:
        data_service_mobile.append(row.copy())
        for field, value_att in row.items() :
            if field not in ["employee", "shift"] and not bool(filters.summarized_view):
                if type(value_att) == dict:
                    w= value_att['w']
                    l= value_att['l']
                    day = field if len(field) == 2 else "0" + field
                    month = filters.get("month") if len(filters.get("month")) == 2 else "0" + filters.get("month")
                    detail_check = {
                        "employee_name": row['employee_name'],
                        "employee": row['employee'],
                        "day": day,
                        "month": month,
                        "year": filters.get('year')
                    }
                    string_show = ''
                    if l == "A" or l=="KL" or l == "A/A":
                        string_show = f'<p  onclick="frappe.open_dialog({detail_check})">{l if l == "KL" else "A"}</p>'
                    elif l != "WO" and l != False and l !='':
                        string_show = f'<p  onclick="frappe.open_dialog({detail_check})">{w} {f"<sup>{l}</sup>" if l else ""} </p>'
                    elif w == 0 and l != "WO": 
                        string_show = f'<p  onclick="frappe.open_dialog({detail_check})">x</p>'
                    else:
                        string_show = f'<p  onclick="frappe.open_dialog({detail_check})">{w if l != "WO" else "WO" }</p>'
                    row[field] = string_show  
    # chart = get_chart_data(attendance_map, filters)
    message = get_message() if not filters.summarized_view else ""
    return columns, data, message, data_service_mobile



def get_message() -> str:
    message = ""
    colors = ["green", "red", "orange", "green", "#318AD8", "", ""]

    count = 0
    for status, abbr in status_map.items():
        message += f"""
            <span style='border-left: 2px solid {colors[count]}; padding-right: 12px; padding-left: 5px; margin-right: 3px;'>
                {status} - {abbr}
            </span>
        """
        count += 1

    return message

#ham tra ve column
def get_columns(filters: Filters) -> List[Dict]:
    columns = []

    if filters.group_by:
        columns.append(
            {
                "label": _(filters.group_by),
                "fieldname": frappe.scrub(filters.group_by),
                "fieldtype": "Link",
                "options": "Branch",
                "width": 120,
            }
        )

    columns.extend(
        [
            {
                "label": _("Employee"),
                "fieldname": "employee",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 135,

            },
            {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 120},
        ]
    )

    if filters.summarized_view:
        # cau hinh column tong quan
        columns.extend(
            [
                {"label": _("Total Hour"), "fieldname": "total_hours", "fieldtype": "Float", "width": 110},
                {
                    "label": _("Total Present"),
                    "fieldname": "total_present",
                    "fieldtype": "Float",
                    "width": 110,
                },
                {
                    "label": _("Total Late Entries"),
                    "fieldname": "total_late_entries",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {
                    "label": _("Time Late Entries (minute)"),
                    "fieldname": "time_late_entries",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {
                    "label": _("Time Late Entries to work"),
                    "fieldname": "time_late_entries_work",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {
                    "label": _("Total Early Exits "),
                    "fieldname": "total_early_exits",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {
                    "label": _("Time Early Exits (minute)"),
                    "fieldname": "time_early_exits",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {
                    "label": _("Time Early Exits to work"),
                    "fieldname": "time_early_exits_work",
                    "fieldtype": "Float",
                    "width": 140,
                },
                {"label": _("Total Leaves "), "fieldname": "total_leaves", "fieldtype": "Float", "width": 110},
                {"label": _("Total Leaves to work"), "fieldname": "total_leaves_work", "fieldtype": "Float", "width": 110},

                {"label": _("Total Absent"), "fieldname": "total_absent", "fieldtype": "Float", "width": 110},
                {"label": _("Total Absent to work"), "fieldname": "total_absent_to_work", "fieldtype": "Float", "width": 110},
                
                {"label": _("Shift OT"), "fieldname": "shift_ot", "fieldtype": "Float", "width": 110},
                {"label": _("Shift OT time(Hour)"), "fieldname": "shift_ot_time", "fieldtype": "Float", "width": 110},

                {"label": _("OT time (Hour)"), "fieldname": "total_ot", "fieldtype": "Float", "width": 110},
            ]
        )

        # columns.extend(get_columns_for_leave_types())
    else:
        # columns.append({"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 120})
        columns.extend(get_columns_for_days(filters))

    return columns

#ham tra
def get_columns_for_leave_types() -> List[Dict]:
    leave_types = frappe.db.get_all("Leave Type", pluck="name")
    types = []
    for entry in leave_types:
        types.append(
            {"label": _(entry), "fieldname": frappe.scrub(entry), "fieldtype": "Float", "width": 120}
        )

    return types


def get_columns_for_days(filters: Filters) -> List[Dict]:
    total_days = get_total_days_in_month(filters)
    days = []

    for day in range(1, total_days + 1):
        # forms the dates from selected year and month from filters
        date = "{}-{}-{}".format(cstr(filters.year), cstr(filters.month), cstr(day))
        # gets abbr from weekday number
        weekday = day_abbr[getdate(date).weekday()]
        # sets days as 1 Mon, 2 Tue, 3 Wed
        label = "{} {}".format(cstr(day), weekday)
        days.append({"label": label, "fieldtype": "Data", "fieldname": day, "width": 65})

    return days


def get_total_days_in_month(filters: Filters) -> int:
    return monthrange(cint(filters.year), cint(filters.month))[1]


def get_data(filters: Filters, attendance_map: Dict) -> List[Dict]:
    employee_details, group_by_param_values = get_employee_related_details(filters)
    holiday_map = get_holiday_map(filters)
    data = []
    # print("getdata",attendance_map)
    if filters.group_by:
        group_by_column = frappe.scrub(filters.group_by)

        for value in group_by_param_values:
            if not value:
                continue

            records = get_rows(employee_details[value], filters, holiday_map, attendance_map)

            if records:
                data.append({group_by_column: frappe.bold(value)})
                data.extend(records)

    else:

        data = get_rows(employee_details, filters, holiday_map, attendance_map)
    return data

# get attedance syntax
def get_attendance_map(filters: Filters) -> Dict:
    """Returns a dictionary of employee wise attendance map as per shifts for all the days of the month like
    {
        'employee1': {
                'Morning Shift': {1: 'Present', 2: 'Absent', ...}
                'Evening Shift': {1: 'Absent', 2: 'Present', ...}
        },
        'employee2': {
                'Afternoon Shift': {1: 'Present', 2: 'Absent', ...}
                'Night Shift': {1: 'Absent', 2: 'Absent', ...}
        },
        'employee3': {
                None: {1: 'On Leave'}
        }
    }
    """
    attendance_list = get_attendance_records(filters)
    attendance_map = {}
    leave_map = {}
    for d in attendance_list:        
        attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
        date_att = date(int(filters.get('year')),int(filters.get('month')),int( d.day_of_month))
        if d.status not in status_map and d.status not in leave_without_pay : 
            if d.total_shift_time == 0 :
                attendance_map[d.employee][d.shift][d.day_of_month] = 0
            else :
                if d.working_hours and d.total_shift_time and  d.exchange_to_working_day:
                    overtime_leave = False
                    if d.working_hours > d.total_shift_time :
                        overtime_leave = frappe.db.get_value("ESS Overtime Request", {"employee": d.employee, "ot_date": date_att,"workflow_state": "Approved"},['*'],as_dict=True)
                        if overtime_leave:
                            #hệ số chuyển đổi (tam thoi fix cung, se co cau hinh rieng)
                            conversion_factor = 0.2
                            #tinh so gio tang ca ra cong
                            working_ot = d.working_hours - d.exchange_to_working_day
                            time_ot_access = overtime_leave.get('ot_end_time') - overtime_leave.get('ot_start_time')
                            # chua thong nhat ......, de tam la cong cua ca truoc no
                            working = d.exchange_to_working_day
                        else :
                            working = d.exchange_to_working_day
                    else:        
                        working = round((d.working_hours/d.total_shift_time)*d.exchange_to_working_day,2) 
                    attendance_map[d.employee][d.shift][d.day_of_month] = working if not overtime_leave and d.working_hours <= d.total_shift_time  else {
                    "status" :"Over Time", 
                    "has_leave": False ,
                    "exchange_to_working_day": working	
                    }

                else :
                    attendance_map[d.employee][d.shift][d.day_of_month] = 0         
        else:
            if d.status == "On Leave":
                leave_map.setdefault(d.employee, []).append(d.day_of_month)
                attendance_map[d.employee][d.shift][d.day_of_month] = {
                    "status" :d.status, 
                    "exchange_to_working_day": d.exchange_to_working_day
                    }
            elif d.status in leave_without_pay:
                attendance_map[d.employee][d.shift][d.day_of_month] = {
                "status" :d.status, 
                "exchange_to_working_day": d.exchange_to_working_day
                }
            else:
                attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
                attendance_map[d.employee][d.shift][d.day_of_month] = {
                    "status" :d.status, 
                    "has_leave": d.has_leave if d.has_leave else False,
                    "exchange_to_working_day": d.exchange_to_working_day	
                    }
                
    # leave is applicable for the entire day so all shifts should show the leave entry
    for employee, leave_days in leave_map.items():
        # no attendance records exist except leaves
        if employee not in attendance_map:
            attendance_map.setdefault(employee, {}).setdefault(None, {})

        for day in leave_days:
            for shift in attendance_map[employee].keys():
                attendance_map[employee][shift][day] = "On Leave"
    return attendance_map

# lay thong tin danh dau com cong/ban ghi tho
def get_attendance_records(filters: Filters) -> List[Dict]:
    Attendance = frappe.qb.DocType("Attendance")

    query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.attendance_date,
			Attendance.status,
			Attendance.shift,
            Attendance.working_hours,
            Attendance.late_check_in,
            Attendance.early_check_out,
            Attendance.attendance_request,
            Attendance.leave_type,
            Attendance.leave_application,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	)

    if filters.employee:
        query = query.where(Attendance.employee == filters.employee)
    query = query.orderby(Attendance.employee, Attendance.attendance_date)

    data_att =  query.run(as_dict=1)
    LeaveApplication = frappe.qb.DocType("Leave Application")
    if not filters.summarized_view:
        for att in data_att:
            if att.status not in status_off: 
                list_leave = (
                frappe.qb.from_(LeaveApplication)
                .select('*')
                .where(
                    (LeaveApplication.employee == att.get('employee')) & 
                    (att.get("attendance_date") >= LeaveApplication.from_date) & 
                    (att.get("attendance_date") <= LeaveApplication.to_date)
                )
                .run(as_dict=1)
                )           
                if len(list_leave) > 0: 
                    att['has_leave'] = True 
                
            if not att.get('shift'):
                if att.get("attendance_request") :
                    att_request = frappe.db.get_value("Attendance Request",att.get("attendance_request"),['custom_shift'],as_dict=1)
                    att['shift'] = att_request.get('custom_shift')
                if att.get('leave_type'):
                    att_leave = frappe.db.get_value("Leave Application",att.get('leave_application'),['custom_shift_type',"leave_type"],as_dict=1)
                    att['shift'] = att_leave.get('custom_shift_type')
            if att.get('shift') :
                shift_detail = frappe.db.get_value('Shift Type',att.get('shift'), ['total_shift_time',"exchange_to_working_day"],as_dict=1)
                att['total_shift_time'] = shift_detail.get('total_shift_time')
                att['exchange_to_working_day'] = shift_detail.get('exchange_to_working_day')
            
            if att.get('leave_type') and att.get('leave_type') in leave_without_pay:
                att["status"] = att.get('leave_type')

    return data_att

def get_employee_related_details(filters: Filters) -> Tuple[Dict, List]:
    """Returns
    1. nested dict for employee details
    2. list of values for the group by filter
    """
    Employee = frappe.qb.DocType("Employee")
    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.employee_name,
            Employee.designation,
            Employee.grade,
            Employee.department,
            Employee.branch,
            Employee.company,
            Employee.holiday_list,
        )
        .where(Employee.company == filters.company)
    )

    if filters.employee:
        query = query.where(Employee.name == filters.employee)

    group_by = filters.group_by
    if group_by:
        group_by = group_by.lower()
        query = query.orderby(group_by)

    employee_details = query.run(as_dict=True)

    group_by_param_values = []
    emp_map = {}

    if group_by:
        for parameter, employees in groupby(employee_details, key=lambda d: d[group_by]):
            group_by_param_values.append(parameter)
            emp_map.setdefault(parameter, frappe._dict())

            for emp in employees:
                emp_map[parameter][emp.name] = emp
    else:
        for emp in employee_details:
            emp_map[emp.name] = emp

    return emp_map, group_by_param_values


def get_holiday_map(filters: Filters) -> Dict[str, List[Dict]]:
    """
    Returns a dict of holidays falling in the filter month and year
    with list name as key and list of holidays as values like
    {
            'Holiday List 1': [
                    {'day_of_month': '0' , 'weekly_off': 1},
                    {'day_of_month': '1', 'weekly_off': 0}
            ],
            'Holiday List 2': [
                    {'day_of_month': '0' , 'weekly_off': 1},
                    {'day_of_month': '1', 'weekly_off': 0}
            ]
    }
    """
    # add default holiday list too
    holiday_lists = frappe.db.get_all("Holiday List", pluck="name")
    default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
    holiday_lists.append(default_holiday_list)

    holiday_map = frappe._dict()
    Holiday = frappe.qb.DocType("Holiday")

    for d in holiday_lists:
        if not d:
            continue

        holidays = (
            frappe.qb.from_(Holiday)
            .select(Extract("day", Holiday.holiday_date).as_("day_of_month"), Holiday.weekly_off)
            .where(
                (Holiday.parent == d)
                & (Extract("month", Holiday.holiday_date) == filters.month)
                & (Extract("year", Holiday.holiday_date) == filters.year)
            )
        ).run(as_dict=True)

        holiday_map.setdefault(d, holidays)

    return holiday_map

# xuat ra row hien thi tren table (bao gom tinh tong cong cua ca)
def get_rows(
    employee_details: Dict, filters: Filters, holiday_map: Dict, attendance_map: Dict
) -> List[Dict]:
    records = []
    default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

    for employee, details in employee_details.items():
        emp_holiday_list = details.holiday_list or default_holiday_list
        holidays = holiday_map.get(emp_holiday_list)

        if filters.summarized_view:
            attendance = get_attendance_status_for_summarized_view(employee, filters, holidays)
            if not attendance:
                continue

            leave_summary = get_leave_summary(employee, filters)
            # Xu ly thoi gian ra vao muon
            entry_exits_summary = get_entry_exits_summary(employee, filters)
            row = {"employee": employee, "employee_name": details.employee_name}
            set_defaults_for_summarized_view(filters, row)
            row.update(attendance)
            row.update(leave_summary)
            row.update(entry_exits_summary)
            # print("row",row)
            records.append(row)
        else:
            employee_attendance = attendance_map.get(employee)
            if not employee_attendance:
                continue
            # lay thong tinh cham cong cua nhan vien
            attendance_for_employee = get_attendance_status_for_detailed_view(
                employee, filters, employee_attendance, holidays
            )
            detail_checkin = {}
            for att in range(0,len(attendance_for_employee)): 

                # attendance_for_employee[att]  = {}
                detail_shift = attendance_map.get(employee).get(attendance_for_employee[att].get("shift"))
                for field_att, value_att in attendance_for_employee[att].items():
                    if field_att != 'shift':
                        detail_shift_day = detail_shift.get(field_att)  
                        prev_w =  detail_checkin.get(str(field_att))['w'] if detail_checkin.get(str(field_att)) and detail_checkin.get(str(field_att))['w'] != None else 0
                        prev_l =  detail_checkin.get(str(field_att))['l'] if detail_checkin.get(str(field_att)) and detail_checkin.get(str(field_att))['l'] != ''  else ""
                        if detail_shift_day: 
                            this_w = 0
                            this_l = ""
                            if type(detail_shift_day) == dict and (detail_shift_day.get('status') in leave_with_pay or  detail_shift_day.get('status') in ot_type): 
                                this_w = detail_shift_day.get('exchange_to_working_day') or 0
                                this_l = value_att + ("!" if detail_shift_day.get("has_leave") else "")
                            elif type(detail_shift_day) == float:
                                this_w  = value_att  or 0
                            else : 
                                this_w = 0
                                this_l = value_att   + ("!" if type(detail_shift_day) == dict and  detail_shift_day.get("has_leave") else "")                
                            l = prev_l
                            print("ooaofno:",field_att,{prev_l,this_l})
                            if prev_l != "" and this_l != "" and prev_l != this_l  :
                                l= prev_l + "/"+ this_l
                            elif prev_l == this_l:
                                l= prev_l
                            else: 
                                l = this_l

                            detail_checkin[str(field_att)] = {
                                "w": prev_w + this_w  ,
                                "l": l
                            }
                            # print("detail_shift_day",attendance_for_employee[att].get("shift"),detail_shift_day)
                        else: 
                            detail_checkin[str(field_att)] = {
                                "w": 0 + prev_w,
                                "l": "" + prev_l
                            }
                           
            detail_checkin.update(
                {"employee": employee, "employee_name": details.employee_name}
            )
            records.extend([detail_checkin])
    # print("records",records)
    return records


def set_defaults_for_summarized_view(filters, row):
    for entry in get_columns(filters):
        if entry.get("fieldtype") == "Float":
            row[entry.get("fieldname")] = 0.0

# format data summarized view
def get_attendance_status_for_summarized_view(
    employee: str, filters: Filters, holidays: List
) -> Dict:
    """Returns dict of attendance status for employee like
    {'total_present': 1.5, 'total_leaves': 0.5, 'total_absent': 13.5, 'total_holidays': 8, 'unmarked_days': 5}
    """
    summary, attendance_days = get_attendance_summary_and_days(employee, filters)
    if not any(summary.values()):
        return {}

    total_days = get_total_days_in_month(filters)
    total_holidays = total_unmarked_days = 0

    for day in range(1, total_days + 1):
        if day in attendance_days:
            continue

        status = get_holiday_status(day, holidays)
        if status in ["Weekly Off", "Holiday"]:
            total_holidays += 1
        elif not status:
            total_unmarked_days += 1

    return {
        "total_present": summary.total_present + summary.total_half_days,
        "total_hours": summary.total_hours,
        "total_leaves": summary.total_leaves + summary.total_half_days,
        "total_leaves_work": summary.sum_leave_shift + (summary.total_half_days_shift if summary.total_half_days_shift else 0),
        "total_absent": summary.total_absent,
        "total_absent_to_work": summary.sum_absent_shift,
        "total_holidays": total_holidays,
        "unmarked_days": total_unmarked_days,
        "total_ot" : summary.total_ot
    }

#tinh tong ca/ thoi gian
def get_attendance_summary_and_days(employee: str, filters: Filters) -> Tuple[Dict, List]:
    Attendance = frappe.qb.DocType("Attendance")
    ShiftType = frappe.qb.DocType("Shift Type")

    present_case = (
        frappe.qb.terms.Case()
        .when(((Attendance.status == "Present") | (Attendance.status == "Work From Home")), 1)
        .else_(0)
    )
    sum_present = Sum(present_case).as_("total_present")

    hours_case = frappe.qb.terms.Case().when(((Attendance.status == "Present") | (Attendance.status == "Work From Home")),Attendance.working_hours).else_(0)
    sum_hours = Sum(hours_case).as_("total_hours")

    absent_case = frappe.qb.terms.Case().when(Attendance.status == "Absent", 1).else_(0)
    sum_absent = Sum(absent_case).as_("total_absent")
    #tong cong vang mat theo ca
    absent_case_shift = frappe.qb.terms.Case().when((Attendance.status == "Absent"), ShiftType.exchange_to_working_day).else_(0)
    sum_absent_shift = Sum(absent_case_shift).as_("sum_absent_shift")

    leave_case = frappe.qb.terms.Case().when(Attendance.status == "On Leave", 1).else_(0)
    sum_leave = Sum(leave_case).as_("total_leaves")
    #tong thoi  cong co phep theo ca
    leave_case_shift = frappe.qb.terms.Case().when(Attendance.status == "On Leave", ShiftType.exchange_to_working_day).else_(0)
    sum_leave_shift = Sum(leave_case_shift).as_("sum_leave_shift")

    half_day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(0)
    sum_half_day = Sum(half_day_case).as_("total_half_days")
    #tong cong theo nua ngay
    half_day_case_shift = frappe.qb.terms.Case().when(Attendance.status == "Half Day", ShiftType.exchange_to_working_day).else_(0)
    sum_half_day_shift = Sum(half_day_case_shift).as_("total_half_days_shift")

    #Tong thoi gian tang ca
    OverTimeRequest = frappe.qb.DocType("ESS Overtime Request")
    EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
    ot_total = (
        frappe.qb.from_(OverTimeRequest)
        .inner_join(ShiftType)
        .on(ShiftType.name == OverTimeRequest.shift)
        .inner_join(EmployeeCheckin)
        .on(EmployeeCheckin.shift == OverTimeRequest.shift)
        .inner_join(Attendance)
        .on(Attendance.shift == OverTimeRequest.shift)
        .select(
            # OverTimeRequest.name,
            OverTimeRequest.employee,
            OverTimeRequest.ot_start_time,
            OverTimeRequest.ot_date,
            OverTimeRequest.ot_end_time,
            EmployeeCheckin.time,
            EmployeeCheckin.name,
        )
        .where(
            (EmployeeCheckin.log_type == "OUT")
            & ((OverTimeRequest.status == "Approved") | (OverTimeRequest.workflow_state == "Approved"))
            & (Attendance.docstatus == 1)
            & (Attendance.employee == employee)
            & (OverTimeRequest.employee == employee)
            & (Attendance.company == filters.company)
            & (Attendance.status == "Present")
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
            & (Extract("month", OverTimeRequest.ot_date) == filters.month)
            & (Extract("year", OverTimeRequest.ot_date) == filters.year)
            & (Extract("day",EmployeeCheckin.time) == Extract("day", OverTimeRequest.ot_date))
            & (Extract("month",EmployeeCheckin.time) == Extract("month", OverTimeRequest.ot_date))
            & (Extract("year",EmployeeCheckin.time) == Extract("year", OverTimeRequest.ot_date))
        )
    ).run(as_dict=True)
    total_ot = 0
    for ot_doc in ot_total : 
        if ot_doc.get('time').timestamp() >=  delta_to_time_now(ot_doc.get("ot_date"),ot_doc.get("ot_end_time")) :
            time_ot_shift = delta_to_time_now(ot_doc.get("ot_date"),ot_doc.get("ot_end_time")) - delta_to_time_now(ot_doc.get("ot_date"),ot_doc.get("ot_start_time"))
        else:
            time_ot_shift = ot_doc.get('time').timestamp() - delta_to_time_now(ot_doc.get("ot_date"),ot_doc.get("ot_start_time"))
        time_to_hour = time_ot_shift/3600
        total_ot += time_to_hour
        

    #tinh tong thoi gian
    summary = (
        frappe.qb.from_(Attendance)
        .inner_join(ShiftType)
        .on(ShiftType.name == Attendance.shift)
        .select(
            sum_present,
            sum_absent,
            sum_absent_shift,
            sum_hours,
            sum_leave,
            sum_leave_shift,
            sum_half_day,
            sum_half_day_shift
        )
        .where(
            (Attendance.docstatus == 1)
            & (Attendance.employee == employee)
            & (Attendance.company == filters.company)
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
        )
    ).run(as_dict=True)
    summary[0]["total_ot"] = total_ot
    days = (
        frappe.qb.from_(Attendance)
        .select(Extract("day", Attendance.attendance_date).as_("day_of_month"))
        .distinct()
        .where(
            (Attendance.docstatus == 1)
            & (Attendance.employee == employee)
            & (Attendance.company == filters.company)
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
        )
    ).run(pluck=True)
    return summary[0], days
# ham xu ly hop nhat ngay thang
def delta_to_time_now(date,time):
    return int((datetime.combine(date, datetime.min.time())+time).timestamp())
# xu ly lay thong tin cham cong 'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
def get_attendance_status_for_detailed_view(
    employee: str, filters: Filters, employee_attendance: Dict, holidays: List
) -> List[Dict]:
    """Returns list of shift-wise attendance status for employee
    [
            {'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
            {'shift': 'Evening Shift', 1: 'P', 2: 'A', 3: 'P'....}
    ]
    """
    total_days = get_total_days_in_month(filters)
    attendance_values = []

    for shift, status_dict in employee_attendance.items():
        row = {"shift": shift}

        for day in range(1, total_days + 1):
            status = status_dict.get(day)
            if type(status) == dict:
                status = status.get('status')
            if status is None and holidays:
                status = get_holiday_status(day, holidays)

            if status in status_map:
                abbr = status_map.get(status, "")
            elif status in leave_without_pay:
                abbr = leave_without_pay.get(status,"")
            elif status in ot_type:
                abbr = ot_type.get(status,"")
            else :
                abbr = 0
                if status :
                    abbr = status
            row[day] = abbr

        attendance_values.append(row)

    return attendance_values


def get_holiday_status(day: int, holidays: List) -> str:
    status = None
    if holidays:
        for holiday in holidays:
            if day == holiday.get("day_of_month"):
                if holiday.get("weekly_off"):
                    status = "Weekly Off"
                else:
                    status = "Holiday"
                break
    return status


def get_leave_summary(employee: str, filters: Filters) -> Dict[str, float]:
    """Returns a dict of leave type and corresponding leaves taken by employee like:
    {'leave_without_pay': 1.0, 'sick_leave': 2.0}
    """
    Attendance = frappe.qb.DocType("Attendance")
    ShiftType = frappe.qb.DocType("Shift Type")
    day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(1)
    sum_leave_days = Sum(day_case).as_("leave_days")

    leave_details = (
        frappe.qb.from_(Attendance)
        .inner_join(ShiftType)
        .on(Attendance.shift == ShiftType.name )
        .select(Attendance.leave_type, sum_leave_days)
        .where(
            (Attendance.employee == employee)
            & (Attendance.docstatus == 1)
            & (Attendance.company == filters.company)
            & ((Attendance.leave_type.isnotnull()) | (Attendance.leave_type != ""))
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
        )
        .groupby(Attendance.leave_type)
    ).run(as_dict=True)

    leaves = {}
    for d in leave_details:
        leave_type = frappe.scrub(d.leave_type)
        leaves[leave_type] = d.leave_days
    # print("leave",leaves)
    return leaves


def get_entry_exits_summary(employee: str, filters: Filters) -> Dict[str, float]:
    """Returns total late entries and total early exits for employee like:
    {'total_late_entries': 5, 'total_early_exits': 2}
    """
    Attendance = frappe.qb.DocType("Attendance")
    ShiftType = frappe.qb.DocType("Shift Type")
    # so lan va thoi gian vao muon
    late_entry_case = frappe.qb.terms.Case().when(Attendance.late_entry == "1", 1)
    count_late_entries = Count(late_entry_case).as_("total_late_entries")

    time_entry_case = frappe.qb.terms.Case().when(Attendance.late_entry == "1", Attendance.late_check_in)
    time_late_entries = Sum(time_entry_case).as_("time_late_entries")
    # so lan va thoi gian ra som
    early_exit_case = frappe.qb.terms.Case().when(Attendance.early_exit == "1", 1)
    count_early_exits = Count(early_exit_case).as_("total_early_exits")

    time_exit_case = frappe.qb.terms.Case().when(Attendance.early_exit == "1", Attendance.early_check_out)
    time_early_exits = Sum(time_exit_case).as_("time_early_exits")
    entry_exits = (
        frappe.qb.from_(Attendance)
        .inner_join(ShiftType)
        .on(Attendance.shift == ShiftType.name)
        .select(count_late_entries,time_late_entries, count_early_exits,time_early_exits,ShiftType.exchange_to_working_day,ShiftType.total_shift_time)
        .where(
            (Attendance.docstatus == 1)
            & (Attendance.employee == employee)
            & (Attendance.company == filters.company)
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
        )
    ).run(as_dict=True)

    entry_exits =  entry_exits[0]
    # print("entry_exits",entry_exits)
    entry_exits['time_early_exits_work'] = 0 if (not entry_exits["time_early_exits"]) or entry_exits['total_shift_time'] == 0 else float(entry_exits["time_early_exits"]/60/entry_exits['total_shift_time']*entry_exits["exchange_to_working_day"] )
    entry_exits['time_late_entries_work'] = 0 if (not entry_exits["time_late_entries"]) or entry_exits['total_shift_time']==0 else float(entry_exits["time_late_entries"]/60/entry_exits['total_shift_time']*entry_exits["exchange_to_working_day"] )

    return entry_exits

@frappe.whitelist()
def get_attendance_years() -> str:
    """Returns all the years for which attendance records exist"""
    Attendance = frappe.qb.DocType("Attendance")
    year_list = (
        frappe.qb.from_(Attendance)
        .select(Extract("year", Attendance.attendance_date).as_("year"))
        .distinct()
    ).run(as_dict=True)

    if year_list:
        year_list.sort(key=lambda d: d.year, reverse=True)
    else:
        year_list = [frappe._dict({"year": getdate().year})]

    return "\n".join(cstr(entry.year) for entry in year_list)


def get_chart_data(attendance_map: Dict, filters: Filters) -> Dict:
    days = get_columns_for_days(filters)
    labels = []
    absent = []
    present = []
    leave = []

    for day in days:
        labels.append(day["label"])
        total_absent_on_day = total_leaves_on_day = total_present_on_day = 0

        for employee, attendance_dict in attendance_map.items():
            for shift, attendance in attendance_dict.items():
                attendance_on_day = attendance.get(day["fieldname"])

                if attendance_on_day == "On Leave":
                    # leave should be counted only once for the entire day
                    total_leaves_on_day += 1
                    break
                elif attendance_on_day == "Absent":
                    total_absent_on_day += 1
                elif attendance_on_day in ["Present", "Work From Home"]:
                    total_present_on_day += 1
                elif attendance_on_day == "Half Day":
                    total_present_on_day += 0.5
                    total_leaves_on_day += 0.5

        absent.append(total_absent_on_day)
        present.append(total_present_on_day)
        leave.append(total_leaves_on_day)

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Absent", "values": absent},
                {"name": "Present", "values": present},
                {"name": "Leave", "values": leave},
            ],
        },
        "type": "line",
        "colors": ["red", "green", "blue"],
    }
