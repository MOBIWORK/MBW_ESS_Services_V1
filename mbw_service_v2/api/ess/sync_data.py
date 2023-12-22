import frappe
from mbw_service_v2.api.common import (
    basic_auth, gen_response, exception_handel, inshift, get_language,cong_va_xoa_trung)
import requests
import json
from datetime import datetime
from frappe.utils import cstr
from mbw_service_v2.config_translate import i18n
# sync data checkin
@frappe.whitelist(methods="POST")
def checkin_data(**data):
    try:
        from_date = data.get('from_date') if data.get('from_date') else False
        to_date = data.get('to_date') if data.get('to_date') else False
        id_dms = data.get('id_dms') if data.get('id_dms') else False
        token_key = data.get('token_key') if data.get('token_key') else False
        ma_nv = data.get('emplyee_code') if data.get('emplyee_code') else False
        if not from_date or not to_date or not id_dms or not token_key:
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), [])
        params = {
            "tu_ngay": from_date,
            "den_ngay": to_date,
        }
        if ma_nv:
            params['ma_nv'] = ma_nv
        url = f"https://dev.mobiwork.vn:4036/OpenAPI/V1/TimesheetData"
        dataTimeSheet = requests.get(url=url, params=params,
                                     headers={
                                         "Authorization": basic_auth(id_dms, token_key),
                                     })

        dataTimeSheet = json.loads(dataTimeSheet.text)
        if not dataTimeSheet.get('status'):
            gen_response(500, i18n.t('translate.error', locale=get_language()), [])
            return
        data_checkin = dataTimeSheet.get('data')
        
        # return data_checkin
        if len(data_checkin) > 0:
            field_not_loop = ['stt', 'ma_nhan_vien', 'ten_nhan_vien']
            for employee in data_checkin:
                emp_data = frappe.db.get_value(
                    "Employee",
                    {"employee_code_dms": employee.get('ma_nhan_vien')},
                    ["employee"],
                    # as_dict=1,
                )

                if emp_data:
                    total = 0
                    total_has = 0
                    thoi_gian_co = []
                    for field, value in employee.items():
                        if (field not in field_not_loop):
                            dataCheckShift = value.get('data_cc')
                            for data_check in dataCheckShift:
                                total += 1
                    new_log = frappe.new_doc("DMS Log")
                    data_log = {
                        "ma_nv": emp_data,
                        "checkin_start":  datetime.strptime(from_date, "%d/%m/%Y"),
                        "checkin_end":  datetime.strptime(to_date, "%d/%m/%Y"),
                        "total_records": total,
                        "total_import": 0,
                        "status": "Đang tiến hành"
                    }
                    
                    for fiel, value in data_log.items():
                        setattr(new_log, fiel, value)

                    new_log.insert()
                    for field, value in employee.items():
                        if (field not in field_not_loop):
                            dataCheckShift = value.get('data_cc')
                            thoigian = {
                                value.get("date_time") : []
                            }
                            for docShift in dataCheckShift:
                                if bool(docShift.get('thoi_gian')):
                                    thoigian[value.get("date_time")].append(docShift.get('thoi_gian'))
                                    hour = docShift.get(
                                        'thoi_gian').split(':')[0]
                                    minute = docShift.get(
                                        'thoi_gian').split(':')[1]
                                    ime_check_server = datetime.strptime(value.get('date_time'),  '%a, %d %b %Y %H:%M:%S %Z').replace(hour=int(hour), minute=int(minute))
                                    data = {
                                        "time": ime_check_server,
                                        "device_id": json.dumps({"longitude": docShift.get("long"), "latitude": docShift.get("lat")}),
                                        "log_type": "IN" if docShift.get("loai") == "Vào" else "OUT",
                                        "image": docShift.get('hinh_anh'),
                                        "employee": emp_data,
                                    }
                                    ShiftType = frappe.qb.DocType('Shift Type')
                                    ShiftAssignment = frappe.qb.DocType('Shift Assignment')


                                    that_shift_now = (frappe.qb.from_(ShiftType)
                                        .inner_join(ShiftAssignment)
                                        .on(ShiftType.name == ShiftAssignment.shift_type)
                                        .where(
                                            (ShiftAssignment.employee == emp_data) & 
                                            (ime_check_server.time() >= ShiftType.start_time) & 
                                            (ime_check_server.time() <= ShiftType.end_time) & 
                                            (ime_check_server.date() >= ShiftAssignment.start_date) & 
                                            (ime_check_server.date() <= ShiftAssignment.end_date)
                                        )
                                        .select(ShiftType.name, ShiftType.start_time, ShiftType.end_time, ShiftType.allow_check_out_after_shift_end_time, ShiftType.begin_check_in_before_shift_start_time)
                                        .run(as_dict=True)
                                    )
                                    if len(that_shift_now) == 0 :
                                        continue
                                    that_shift_now = that_shift_now[0]

                                    countDelete = frappe.db.delete('Employee Checkin',{
                                        "employee": emp_data,
                                        "shift" : that_shift_now.get('name'),
                                        "log_type" : data['log_type'],
                                        "time" : ['between', [datetime.strptime(value.get('date_time'),  '%a, %d %b %Y %H:%M:%S %Z').replace(hour=0, minute=0),datetime.strptime(value.get('date_time'),  '%a, %d %b %Y %H:%M:%S %Z').replace(hour=23, minute=59)]] 
                                    })
                                    new_check = frappe.new_doc(
                                        "Employee Checkin")
                                    for field, value_data in data.items():
                                        setattr(new_check, field, value_data)
                                    setattr(new_check, "image_attach",
                                            data.get("image"))
                                    
                                    new_check.insert()
                                    total_has += 1
                            thoi_gian_co.append(thoigian)
                    new_log.total_import = total_has
                    new_log.status = "Thành công"
                    new_log.save()

        return thoi_gian_co
    except Exception as e:
        new_log.status = "Thất bại"
        new_log.message = cstr(e)
        new_log.save()
        exception_handel(e)

# sync data kpi
## handle support
def bonus_sell(rate, actually) :

	if rate >= 1.2:
		return actually*0.15
	
	elif rate >=1.1 :
		return actually*0.12
	elif rate >=1 :
		return actually*0.1	
	elif rate >= 0.9 :
		return actually*0.08	
	elif rate >=0.8 :
		return actually*0.05
	else: return 0


def bonus_kpi(rate):
	if rate >=1:
		return 600000
	elif rate >= 0.9:
		return 500000
	elif rate >=0.8:
		return 400000	
	else: return 0
##### Cac ham xu ly ho tro dong bo kpi
     
# xu ly phan cap tu data 1 cap => data 4 cap
def handle_array_to_key(data_array,i=0):
    key_field = ['rsm','asm','ss']
    arr_tree = {}
    if i < len(key_field): 
        for kpi_data in  data_array :
            if kpi_data.get(key_field[i]) != '':
                arr_tree.setdefault(kpi_data.get(key_field[i]),[])
                if kpi_data.get(key_field[i]) in arr_tree.keys():
                    arr_tree[kpi_data.get(key_field[i])].append(kpi_data)
            else:
                if i>0:
                    arr_tree.setdefault(f"none_{key_field[i]}",[])
                    if kpi_data.get(key_field[i]) == '':
                        arr_tree[f"none_{key_field[i]}"].append(kpi_data)  

        for key, data_ in arr_tree.items():
            arr_tree[key]=handle_array_to_key(data_,i+1)
    else:
        arr_tree = data_array
    return arr_tree    



# xu ly dong bo theo tung khu vuc
def handle_sync_data(data_lv,manage_info = None,kv=None,filters={}):
    month = filters['month']
    year = filters['year']
    data_kpi_sr_total = {
            "spending_sell_out": 0,
            "actually_achieved_sell_out": 0,
            "spending_kpi1": 0,
            "actually_achieved_kpi1": 0,
            "month": month,
            "year": year
        }
    if type(data_lv) == dict:
        for key,value in data_lv.items():
            # lay thong tin nhan vien cap cao theo key
            emp_info = frappe.db.get_value(
            "Employee",
            {"employee_code_dms": key},
            ["employee","employee_code_dms"],
             as_dict=1,
        )
            #tinh toan du lieu kpi cua ca thang con
            data_sync_manage = handle_sync_data(value,emp_info,kv,filters)
            if emp_info:
                data_sync_manage.update({
                    "employee" : emp_info.get('employee'),
                    "employee_dms" : emp_info.get('employee_code_dms')
                })
                data_mn = hande_sync_single_employee(key, emp_info,data_sync_manage,filters,manage_info,kv)
                if data_mn:
                    data_kpi_sr_total['spending_sell_out'] += data_mn['spending_sell_out']
                    data_kpi_sr_total['actually_achieved_sell_out'] += data_mn['spending_sell_out']
                    data_kpi_sr_total['actually_achieved_sell_out'] += data_mn['spending_sell_out']
                    data_kpi_sr_total['spending_kpi1'] += data_mn['spending_kpi1']    
    else:       
        for data_sync in data_lv:
            emp_data = frappe.db.get_value(
                "Employee",
                {"employee_code_dms": data_sync.get('ma_nv')},
                ["employee","employee_code_dms"],
                 as_dict=1,
                )
            data_employee_kpi = {
                "spending_sell_out": data_sync.get("doanh_so").get('kh'),
                "actually_achieved_sell_out": data_sync.get("doanh_so").get('th'),
                "rate_sell_out": data_sync.get("doanh_so").get('tl'),
                "bonus_sales": bonus_sell(float( data_sync.get("doanh_so").get('tl')/100), data_sync.get("doanh_so").get('th')),
                "spending_kpi1": data_sync.get("sp_trong_tam").get('kh'),
                "actually_achieved_kpi1": data_sync.get("sp_trong_tam").get('th'),
                "rate_kpi1": data_sync.get("sp_trong_tam").get('tl'),
                "bonus_kpi1": bonus_kpi(float(data_sync.get("sp_trong_tam").get('tl')/100)),
                "month": month,
                "year": year
            }
            data_sr= hande_sync_single_employee(data_sync.get('ma_nv'),emp_data, data_employee_kpi,filters,manage_info,kv)
            if data_sr:
                data_kpi_sr_total['spending_sell_out'] += data_sr['spending_sell_out']
                data_kpi_sr_total['actually_achieved_sell_out'] += data_sr['actually_achieved_sell_out']
                data_kpi_sr_total['actually_achieved_kpi1'] += data_sr['actually_achieved_kpi1']
                data_kpi_sr_total['spending_kpi1'] += data_sr['spending_kpi1']   
    # rate + bonus total:
    if data_kpi_sr_total['spending_sell_out'] != 0  :
        data_kpi_sr_total['rate_sell_out'] =  float( data_kpi_sr_total['actually_achieved_sell_out']/data_kpi_sr_total['spending_sell_out']) *100
        data_kpi_sr_total['bonus_sales']  = bonus_sell(float( data_kpi_sr_total['rate_sell_out']/100), data_kpi_sr_total['actually_achieved_sell_out'])
    else:
        data_kpi_sr_total['rate_sell_out'] = 100 if data_kpi_sr_total['actually_achieved_sell_out'] > 0 else 0
        data_kpi_sr_total['bonus_sales']  = bonus_sell(float( data_kpi_sr_total['rate_sell_out']/100), data_kpi_sr_total['actually_achieved_sell_out'])
    if  data_kpi_sr_total['spending_kpi1'] !=0:
        data_kpi_sr_total['rate_kpi1'] =  float( data_kpi_sr_total['actually_achieved_kpi1']/data_kpi_sr_total['spending_kpi1']) *100
        data_kpi_sr_total['bonus_kpi1']  = bonus_kpi(float(data_kpi_sr_total['rate_kpi1']/100)) 
    else: 
        data_kpi_sr_total['rate_kpi1'] =  100 if data_kpi_sr_total['actually_achieved_kpi1'] > 0 else 0
        data_kpi_sr_total['bonus_kpi1']  = bonus_kpi(float(data_kpi_sr_total['rate_kpi1']/100)) 
     
    return data_kpi_sr_total 
 # xu ly dong bo tung nhan vien      
def hande_sync_single_employee(ma_nv,emp_data,data_employee_kpi,filters,manage_info,kv):
    month = filters['month']
    year = filters['year']
    # them mot log khi dong bo du lieu nhan vien
    new_log  =frappe.new_doc("DMS Kpi Log")
    reason = ""
    data_log = {
                "employee_dms":ma_nv,
                "month":  month,
                "year":  year,
                "status": "Đang tiến hành"
            }
    for fiel, value in data_log.items():
        setattr(new_log, fiel, value) 
    new_log.insert() 
    if emp_data:       
        update_employee = frappe.get_doc("Employee",emp_data.get('employee'))   
        if kv.get(emp_data.get('employee_code_dms')):
            setattr(update_employee,'manager_area',kv.get(emp_data.get('employee_code_dms')))
        if manage_info:
            setattr(update_employee,'reports_to',manage_info.get("employee"))

        update_employee.save()       
        # dang tien hanh dong bo (them vao log)
        # xu ly dong bo kpi
        new_kpi = frappe.new_doc('DMS KPI')
        data_employee_kpi.update({"employee": emp_data.get('employee'),
                "employee_dms": emp_data.get('employee_code_dms')}) 
        
        # xu ly dong bo nhan vien
        try:
            frappe.db.delete('DMS KPI', {
                "employee" : emp_data.get("employee"),
                "month": month,
                "year": year          
            })
            for field, value in data_employee_kpi.items() :
                setattr(new_kpi,field,value)
            new_kpi.insert()
            new_log.status = "Thành Công" 
            new_log.employee = emp_data.get("employee")  
            new_log.save()     
            return {
                "spending_sell_out": data_employee_kpi.get('spending_sell_out'),
                "actually_achieved_sell_out": data_employee_kpi.get('actually_achieved_sell_out'),
                "spending_kpi1": data_employee_kpi.get('spending_kpi1'),
                "actually_achieved_kpi1": data_employee_kpi.get('actually_achieved_kpi1'),
                
            }                  
        except Exception as e:
            new_log.reason = cstr(e) 
            new_log.status = "Thất Bại"
            new_log.save()
            return False
    else:
        # thong bao that bai neu nhan vien khong co tai frappe
        new_log.reason = f"Employee not found by {ma_nv}" 
        new_log.status = "Thất Bại"
        new_log.save()  
        return False
        # ket thuc xu ly dong bo 1 nhan vien
def handle_khu_vuc(arr_gs) :
    employee_kv = {}
    for gs in arr_gs:
        employee_kv[gs.get('ma_nv')] = gs.get('kv_quan_ly')
    return employee_kv
##handle
@frappe.whitelist(methods="POST")
def kpi_data(**data): 
    try:
        month = data.get('month') if data.get('month') else False
        year = data.get('year') if data.get('year') else False
        id_dms = data.get('id_dms') if data.get('id_dms') else False
        token_key = data.get('token_key') if data.get('token_key') else False
        ma_nv = data.get('employee_code') if data.get('employee_code') else False
        params = {
             "thang": month,
             "nam": year,
        }
        if ma_nv:
            params['nhan_vien'] = ma_nv
        url = f"https://openapi.mobiwork.vn/OpenAPI/V1/KPI"
        # url = f"https://dev.mobiwork.vn:4036/OpenAPI/V1/KPI"
        dataTimeSheet = requests.get(url=url, params=params,verify=False,
                                     headers={
                                         "Authorization": basic_auth(id_dms, token_key),
                                     })
        dataTimeSheet = json.loads(dataTimeSheet.text)
        if dataTimeSheet.get('message') != "":
            gen_response(500, i18n.t('translate.error', locale=get_language()), [])
            return
        data_kpi = dataTimeSheet.get('result')
        data_gs = dataTimeSheet.get('ds_giam_sat')
        # sap xep kpi nhan vien theo quan ly
        if len(data_kpi) > 0:       
            data_level = handle_array_to_key(data_kpi)
            data_gs_kv = handle_khu_vuc(data_gs)
            # return data_level, data_gs_kv
            handle_sync_data(data_level,None,data_gs_kv,data)                           
            gen_response(200,"Thành công!",[])
            return 
        else: 
             gen_response(404,"không có bản ghi nào! ",[])
             return 
    except Exception as e:
        exception_handel(e)
