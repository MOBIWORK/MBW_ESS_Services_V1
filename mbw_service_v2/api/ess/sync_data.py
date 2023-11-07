import frappe
from mbw_service_v2.api.common import (
    basic_auth, gen_response, exception_handel, inshift, get_language)
import requests
import json
from datetime import datetime
from mbw_service_v2.translations.language import translations
from frappe.utils import cstr

@frappe.whitelist(methods="POST")
def checkin_data(**data):
    try:

        from_date = data.get('from_date') if data.get('from_date') else False
        to_date = data.get('to_date') if data.get('to_date') else False
        id_dms = data.get('id_dms') if data.get('id_dms') else False
        token_key = data.get('token_key') if data.get('token_key') else False
        ma_nv = data.get('emplyee_code') if data.get('emplyee_code') else False
        if not from_date or not to_date or not id_dms or not token_key:
            gen_response(500, 'Invalid value', [])
        params = {
            "tu_ngay": from_date,
            "den_ngay": to_date,
        }
        if ma_nv:
            params['ma_nv'] = ma_nv
        url = f"https://dev.mobiwork.vn:4036/OpenAPI/V1/TimesheetData"
        # url = f"https://openapi.mobiwork.vn/OpenAPI/V1/TimesheetData"
        dataTimeSheet = requests.get(url=url, params=params,
                                     headers={
                                         "Authorization": basic_auth(id_dms, token_key),
                                     })

        dataTimeSheet = json.loads(dataTimeSheet.text)
        if not dataTimeSheet.get('status'):
            gen_response(500, dataTimeSheet.get('message'), [])
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
                    # employee_log = frappe.get_doc()
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
                                    # print("data in",data,'\n')
                                    # print("data del",that_shift_now.get('name'),data['log_type'],'\n')
                                    # print("end=================="'\n')

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
        print(e)
        exception_handel(e)
