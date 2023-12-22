# Copyright (c) 2023, chuyendev and contributors
# For license information, please see license.txt


from calendar import monthrange
from itertools import groupby
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from datetime import datetime, date, timedelta
Filters = frappe._dict
# ham xu ly hop nhat ngay thang
def delta_to_time_now(date,time):
    return int((datetime.combine(date, datetime.min.time())+time).timestamp())

#ham main tra ve du lieu hien thi
def execute(filters: Optional[Filters] = None)-> Tuple:
    filters = frappe._dict(filters or {})
     
    if not (filters.month and filters.year):
        frappe.throw(_("Please select month and year."))
            
    salary_slip = get_salary_slip_map(filters)
    if not salary_slip:
        frappe.msgprint(_("No salary records found."), alert=True, indicator="orange")
        return [], [], None, None  
            
    columns = get_columns(filters)
    data = get_data(filters,salary_slip)
    # handle_box(data,filters)
    return columns, data,""
#tra ve rows data
def get_data(filters: Filters, salary_slip: Dict) -> List[Dict]:
    employee_details, group_by_param_values = get_employee_related_details(filters,salary_slip)
    kpi_map = get_kpi_map(filters)
    holiday_map = get_holiday_map(filters)
    data = get_rows(employee_details, filters,holiday_map, kpi_map, salary_slip)
    return data

# handle box
def handle_box(data,filters) :
    type_attendance = ['attendance']
    type_not_click = ['positions',"area_manager"]
    type_salary = ['salary_basic','salary_received','total_not_bonuses']
    type_sell_in = ['rate_sell_in']
    type_sell_out  = ['rate_sell_out']
    type_bonus_sell_out = ['bonus_sales']
    type_kpi = ['rate_kpi1']
    type_bonus_kpi = ['bonus_kpi1']
    type_deduction = ['salary_tax','salary_advance','salary_bhxh','total_deductions']
    for row in data: 
        data_detail = {
                "employee":row.get('employee'),
                "month": filters.month,
                "year": filters.year
                }
        type_detail = ''
        for key, value in row.items() :
            if key in type_attendance: 
                type_detail = 'attendance'
            elif key in type_salary:
                type_detail = 'salary'
            elif key in type_sell_in:
                type_detail = 'sell_in'
            elif key in type_sell_out:
                type_detail ='sell_out'
            elif key in type_bonus_sell_out:
                type_detail = 'bonus_sell_out'
            elif key in type_kpi:
                type_detail = "kpi"
            elif key in type_bonus_kpi:
                type_detail = 'bonus_kpi'
            elif key in type_deduction:
                type_detail = "deduction"
            data_detail["type"] = type_detail
            row[key] = f'<p style="width: 100%;height:100%;" onclick="frappe.open_dialog({data_detail})">{value if value else ""}</p>'                
    if filters.view_mode == "em" :
        for row in data:
            if row.get("positions") == "" :
                for key, value in row.items() :
                    row[key] = f'<p style="background-color: #ccc;display:block;width: 100%;height:100%;">{value if value else ""}</p>'
            if row.get("positions") == "SS" :
                for key, value in row.items() :
                    row[key] = f'<p style="background-color: #d4b07f;display:block;width: 100%;height:100%;">{value if value else ""}</p>'
            if row.get("positions") == "ASM" :
                for key, value in row.items() :
                    row[key] = f'<p style="background-color: #60b846;display:block;width: 100%;height:100%;">{value if value else ""}</p>'


# xu ly tra ve row
def get_rows(
    employee_details: Dict, filters: Filters,holiday_map:Dict, kpi_map:Dict, salary_slip: Dict
) -> List[Dict]:
    print("employee_details",employee_details,holiday_map)
    total_holiday = 0
    for holiday ,value in holiday_map.items():
        total_holiday += value
    records = {}
    for employee, details in employee_details.items():
        if details.reports_to :
            manager = details.reports_to
        else: 
            manager = "None_Manager"
        records.setdefault(manager,[])
        row = get_employee_summary(details)
        row.update({
            "total_holiday":total_holiday
        })
        handle_row(row,salary_slip.get(employee),kpi_map.get(employee),filters)
        records[manager].append(row)
    final_records = []
    for manager, employees in records.items(): 
        if manager == "None_Manager" :
            info_manager=get_employee_summary(frappe._dict({"employee_name" : "None Manager"}))
            handle_row(info_manager,{},{},filters)
            final_records.append(info_manager)
            final_records = final_records + employees
        else:
            append_manage(final_records,manager)
            final_records = final_records + employees
    return final_records

# handle summary
## handle row 
def handle_row(row,salary_slip,kpi_map,filters):
    att_summary = get_attendance_summary_and_holiday(row.get('employee'),filters)
    salary_summary = get_salary_summary(salary_slip)
    deduction_summary = get_deduction_summary(salary_slip)
    row.update(att_summary)
    row.update(salary_summary)
    row.update(kpi_map)
    row.update(deduction_summary)
    received = get_received(row)
    row.update(received)
    return row
## handle manager
def append_manage(records,employee):
    return records
## employee
def get_employee_summary(details):
    return { "employee": details.get("name") ,"employee_name": details.get("employee_name") or "","positions":details.get("grade") or "" ,"area_manager": details.get("manager_area") or "", "wage": "", "dependent_person":""}

## salary
def get_salary_summary(salary_slip):
    fiel_base_salary = "DMS_Lương cơ bản chuẩn"
    fiel_base_salary_received = "DMS_Lương trách nhiệm"
    fiel_allowance = ['DMS_Phụ cấp đi lại','DMS_Phụ cấp điện thoại + thiết bị']
    fiel_tax = "Income Tax"
    fiel_advance= "Tạm ứng"
    fiel_bhxh = "Bảo hiểm xã hội"
    salary_basic = 0
    salary_received = 0
    salary_tax = 0
    salary_advance = 0
    salary_bhxh=0
    salary_allowance = 0
    total = 0
    if salary_slip and salary_slip.get("earning") and salary_slip.get("deduction") :
        for s in salary_slip.get("earning"):
            total += s.get('amount')
            if s.get('salary_component') ==fiel_base_salary :
                salary_basic = s.get('amount')
            elif s.get('salary_component') ==fiel_base_salary_received: 
                salary_received = s.get('amount')
            elif s.get('salary_component') in fiel_allowance:
                salary_allowance += s.get('amount')

        for s in salary_slip.get("deduction"):    
            if s.get('salary_component') ==fiel_tax: 
                salary_tax = s.get('amount')
            elif s.get('salary_component') ==fiel_advance: 
                salary_advance = s.get('amount')
            elif s.get('salary_component') ==fiel_bhxh: 
                salary_bhxh = s.get('amount')

    return {
        "salary_basic":salary_basic,
        "salary_received": salary_received,
        "salary_tax": salary_tax,
        "salary_advance": salary_advance,
        "salary_bhxh": salary_bhxh,
        "gross_pay": salary_slip.get("gross_pay") if salary_slip.get("gross_pay") else 0,
        "salary_allowance":salary_allowance,
        "total_not_bonuses":total,
        "total_deduction":salary_slip.get("total_deduction") if salary_slip.get("total_deduction") else 0
    }
## kpi
def get_kpi_summary(kpi_map):
    rate_sell_in = 0
    rate_sell_out = 0
    bonus_sales = 0
    rate_kpi1 = 0
    bonus_kpi1 = 0
    other_bonuses = 0
    if kpi_map and len(kpi_map.keys()) >0:
        for key, value in kpi_map.items() :
            if key == "rate_sell_in":
                rate_sell_in = kpi_map.get('rate_sell_in')
            elif key == "rate_sell_out": 
                rate_sell_out = kpi_map.get('rate_sell_out')
            elif key == "bonus_sales" : 
                bonus_sales = kpi_map.get('bonus_sales')
            elif key == "rate_kpi1":
                rate_kpi1 = kpi_map.get('rate_kpi1')
            elif key == "bonus_kpi1":
                bonus_kpi1 = kpi_map.get('bonus_kpi1')
    return {
        "rate_sell_in":rate_sell_in,
        "rate_sell_out":rate_sell_out,
        "bonus_sales":bonus_sales,
        "rate_kpi1":rate_kpi1,
        "bonus_kpi1": bonus_kpi1,
        "other_bonuses": other_bonuses,
    }
## deduction
def get_deduction_summary(salary_slip):
    total_deductions = 0
    if salary_slip: 
        total_deductions = salary_slip.get("total_deduction")
    return {
        "total_deductions" :total_deductions 
    }

## actually received
def get_received(row) :
    print("row",row)
    return {
        "real_total": row.get('gross_pay') - row.get('salary_tax') - row.get('salary_advance')
    }
#ham tra ve column
def get_columns(filters: Filters) -> List[Dict]:
    columns = [
        # thong tin nhan su
		{"fieldname": "employee_name", "label": "Employee name", "fieldtype": "Data", "width": 120},
		{"fieldname": "positions", "label": "Positions", "fieldtype": "Data", "width": 120},
		{"fieldname": "area_manager", "label": "Area manager", "fieldtype": "Data", "width": 120},
		{"fieldname": "wage", "label": "Wage", "fieldtype": "Data", "width": 120},
		{"fieldname": "dependent_person", "label": "Dependent person", "fieldtype": "Data", "width": 120},
        # ngay cong
		{"fieldname": "total_present", "label": "Attendances", "fieldtype": "Float", "width": 120},
        # luong va phu cap
		{"fieldname": "salary_basic", "label": "Salary Basic", "fieldtype": "Float", "width": 120},
		{"fieldname": "salary_received", "label": "Salary Received", "fieldtype": "Float", "width": 120},
		#tong thu nhap chua thuong
		{"fieldname": "total_not_bonuses", "label": "Total not bonuses", "fieldtype": "Float", "width": 120},
		#sell in
		{"fieldname": "rate_sell_in", "label": "Rate sell in", "fieldtype": "Float", "width": 120},
        # sell out
		{"fieldname": "rate_sell_out", "label": "Rate sell out", "fieldtype": "Float", "width": 120},
        # thuong sell out
		{"fieldname": "bonus_sales", "label": "Bonus sales", "fieldtype": "Float", "width": 120},
        #kpi1

		{"fieldname": "rate_kpi1", "label": "Rate KPI1", "fieldtype": "Float", "width": 120},
		{"fieldname": "bonus_kpi1", "label": "Bonus KPI1", "fieldtype": "Float", "width": 120},
        #kpi2
        #thuong khac
		{"fieldname": "other_bonuses", "label": "Other bonuses", "fieldtype": "Float", "width": 120},
        # tong thu nhap
		{"fieldname": "gross_pay", "label": "Gross pay", "fieldtype": "Float", "width": 120},
        #thue
        {"fieldname": "salary_tax", "label": "Tax", "fieldtype": "Float", "width": 120},
        {"fieldname": "salary_advance",  "label": "Employee Advance", "fieldtype": "Float", "width": 120},
        {"fieldname": "salary_bhxh", "label":"BHXH","type" : "Float", "width": 120},
		{"fieldname": "total_deductions", "label": "Total deductions", "fieldtype": "Float", "width": 120},
		{"fieldname": "real_total", "label": "Real total", "fieldtype": "Float", "width": 120},
	]
    return columns
# chuyen ban ghi tho ve ban ghi dung form

## xu ly tra ve thong tin bang luong
def get_salary_slip_map(filters) -> Dict:
    salary_list = get_salary_records(filters)
    salary_map = { }
    for d in salary_list:
        salary_map.setdefault(d.employee,{})
        for key_s, value_s in d.items():
            salary_map[d.employee][key_s] = value_s
    return salary_map

## xu ly thong tin bang kpi
def get_kpi_map(filters) :
    kpi_list = get_kpi_records(filters)
    kpi_map = {}
    for k in kpi_list:
        kpi_map.setdefault(k.employee,{})
        for key_k, value_k in k.items():
            kpi_map[k.employee][key_k] = value_k
        kpi_map[k.employee].update({
            "sell_out_80": kpi_map[k.employee]['bonus_sales'] if float(kpi_map[k.employee]['rate_sell_out']) >= 80 and float(kpi_map[k.employee]['rate_sell_out']) < 90 else 0,
            "sell_out_90": kpi_map[k.employee]['bonus_sales'] if float(kpi_map[k.employee]['rate_sell_out']) >= 90  and float(kpi_map[k.employee]['rate_sell_out']) < 100 else 0,
            "sell_out_100": kpi_map[k.employee]['bonus_sales'] if float(kpi_map[k.employee]['rate_sell_out']) >= 100  and float(kpi_map[k.employee]['rate_sell_out']) < 110 else 0,
            "sell_out_110": kpi_map[k.employee]['bonus_sales'] if float(kpi_map[k.employee]['rate_sell_out']) >= 110  and float(kpi_map[k.employee]['rate_sell_out']) < 120 else 0,
            "sell_out_120": kpi_map[k.employee]['bonus_sales'] if float(kpi_map[k.employee]['rate_sell_out']) >= 120 else 0,
            "kpi_80": kpi_map[k.employee]['bonus_kpi1'] if float(kpi_map[k.employee]['rate_kpi1']) >= 80 and float(kpi_map[k.employee]['rate_kpi1']) < 90 else 0,
            "kpi_90": kpi_map[k.employee]['bonus_kpi1'] if float(kpi_map[k.employee]['rate_kpi1']) >= 90 and float(kpi_map[k.employee]['rate_kpi1']) < 100 else 0,
            "kpi_100": kpi_map[k.employee]['bonus_kpi1'] if float(kpi_map[k.employee]['rate_kpi1']) >= 100 else 0,
        })
    
    return kpi_map
# lay ban ghi tho
## holiday list
def get_holiday_map(filters: Filters) -> Dict[str, List[Dict]]:
    """
    Returns a dict of holidays falling in the filter month and year
    with list name as key and list of holidays as values like
    {
            'Holiday List 1': 0,
            'Holiday List 2': 2
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
            .select(Extract("day", Holiday.holiday_date).as_("day_of_month"), Holiday.description)
            .where(
                (Holiday.parent == d)
                & (Holiday.weekly_off == 0)
                & (Extract("month", Holiday.holiday_date) == filters.month)
                & (Extract("year", Holiday.holiday_date) == filters.year)
            )
        ).run(as_dict=True)
        holiday_map.setdefault(d,len(holidays))
    return holiday_map

## lay bang luong trong thang cua nhan vien
def get_salary_records(filters) -> Dict:
    SalarySlip = frappe.qb.DocType("Salary Slip")
    Employee = frappe.qb.DocType("Employee")
    query = (
		frappe.qb.from_(SalarySlip)
        .inner_join(Employee)
        .on(SalarySlip.employee == Employee.name)
		.select(
            SalarySlip.name,
			SalarySlip.employee,
			SalarySlip.total_working_days,
            SalarySlip.gross_pay,
            SalarySlip.total_deduction,
		)
		.where(
			(SalarySlip.docstatus == 1)
			& (Extract("month", SalarySlip.start_date) == filters.month)
			& (Extract("year", SalarySlip.start_date) == filters.year)
            & (Extract("month", SalarySlip.end_date) == filters.month)
			& (Extract("year", SalarySlip.end_date) == filters.year)
		)
	)

    if filters.employee:
        query = query.where(SalarySlip.employee == filters.employee)
    if filters.view_mode :
        if filters.view_mode == "em":
            query = query.where(Employee.grade == "SR")
        elif filters.view_mode == "ss":
            query =  query.where(Employee.grade == "SS")          
        else: 
            query =  query.where(Employee.grade == "ARM")
    query = query.orderby(SalarySlip.employee, SalarySlip.posting_date)
    data_salary =  query.run(as_dict=1)
    salary_map = frappe._dict()
    SalaryDetail = frappe.qb.DocType("Salary Detail")
    SalaryComponent = frappe.qb.DocType("Salary Component")
    for s in data_salary:
        if not s:
            continue
        earning = (
            frappe.qb.from_(SalaryDetail)
            .inner_join(SalaryComponent)
            .on(SalaryComponent.name == SalaryDetail.salary_component)
            .select(SalaryDetail.amount, SalaryDetail.salary_component)
            .where(
                (SalaryDetail.parent == s.name)
                & (SalaryComponent.type == "Earning")
                )
            .run(as_dict = True)
        )

        deduction = (
            frappe.qb.from_(SalaryDetail)
            .inner_join(SalaryComponent)
            .on(SalaryComponent.name == SalaryDetail.salary_component)
            .select(SalaryDetail.amount, SalaryDetail.salary_component)
            .where(
                (SalaryDetail.parent == s.name)
                & (SalaryComponent.type == "Deduction")
                )
            .run(as_dict = True)
        )
        s["earning"] = earning
        s['deduction'] = deduction

    return data_salary
## lay bang kpi nhan vien
def get_kpi_records(filters) -> Dict:
    KpiDms = frappe.qb.DocType("DMS KPI")
    query = (
        frappe.qb.from_(KpiDms)
        .select(
            '*'
        )
        .where(
            (KpiDms.month == filters.month)
            & (KpiDms.year == filters.year)
        )
    ).run(as_dict=1)
    return query

## lay thong tin Dependent person

#tinh tong ca/ thoi gian
def get_attendance_summary_and_holiday(employee,filters: Filters) -> Tuple[Dict, List]:

    attendance_sumary = get_attendance_summary(employee,filters)
    if employee:
        return {
            "total_working": attendance_sumary.sum_absent_shift + attendance_sumary.sum_leave_shift + attendance_sumary.total_present + attendance_sumary.total_half_days,
            "total_present": attendance_sumary.total_present + attendance_sumary.total_half_days,
        }
    else: 
        return {
            "total_working":0,
            "total_present": 0,
        }

# format data summarized view
def get_attendance_summary(employee: str, filters: Filters) -> Tuple[Dict, List]:
    Attendance = frappe.qb.DocType("Attendance")
    ShiftType = frappe.qb.DocType("Shift Type")

    present_case = (
        frappe.qb.terms.Case()
        .when(((Attendance.status == "Present") | (Attendance.status == "Work From Home")),  ShiftType.exchange_to_working_day)
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
    if employee:
        for key,value in summary[0].items()  :
            summary[0][key] = value if value else 0
        return summary[0]
    else :
        return None
# holiday
def get_holiday_summary(filters: Filters) -> Dict[str, List[Dict]]:
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
            .select("*")
            .where(
                (Holiday.parent == d)
                & (Extract("month", Holiday.holiday_date) == filters.month)
                & (Extract("year", Holiday.holiday_date) == filters.year)
            )
        ).run(as_dict=True)

        holiday_map.setdefault(d, holidays)
    return holiday_map

#list employee 
def get_employee_related_details(filters: Filters,salary_slip) -> Tuple[Dict, List]:
    """Returns
    1. nested dict for employee details
    2. list of values for the group by filter
    """
    employees = []
    for emp,s in salary_slip.items() :
        employees.append(emp)
    Employee = frappe.qb.DocType("Employee")
    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.employee_name,
            Employee.grade,
            Employee.branch,
            Employee.reports_to,
            Employee.designation,
            Employee.department,
            Employee.company,
            Employee.holiday_list,
        )
        .where(Employee.name.isin(employees))
    )
    if filters.employee:
        query = query.where(Employee.name == filters.employee)
    employee_details = query.run(as_dict=True)

    group_by_param_values = []
    emp_map = {} 
    for emp in employee_details:
        emp_map[emp.name] = emp

    return emp_map, group_by_param_values

# nam co ban ghi tinh luong
@frappe.whitelist()
def get_payroll_years() -> str:
    """Returns all the years for which attendance records exist"""
    SalarySlip = frappe.qb.DocType("Salary Slip")
    year_list = (
        frappe.qb.from_(SalarySlip)
        .select(Extract("year", SalarySlip.posting_date).as_("year"))
        .distinct()
    ).run(as_dict=True)

    if year_list:
        year_list.sort(key=lambda d: d.year, reverse=True)
    else:
        year_list = [frappe._dict({"year": getdate().year})]

    return "\n".join(cstr(entry.year) for entry in year_list)



