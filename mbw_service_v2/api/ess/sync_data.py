import frappe
from mbw_service_v2.api.common import (basic_auth,gen_response,exception_handel, inshift,get_language)
import requests
import json
from datetime import datetime
from mbw_service_v2.translations.language import translations

@frappe.whitelist(methods="POST")
def checkin_data(**data):
    try:

        from_date = data.get('from_date') if data.get('from_date') else False
        to_date = data.get('to_date') if data.get('to_date') else False
        id_dms = data.get('id_dms') if data.get('id_dms') else False
        token_key = data.get('token_key') if data.get('token_key') else False
        ma_nv = data.get('emplyee_code') if data.get('emplyee_code') else False
        if not from_date or not to_date or not id_dms or not token_key:
            gen_response(500, 'Invalid value',[])
        params = {
            "tu_ngay": from_date,
            "den_ngay": to_date,
            }
        if ma_nv :
            params['ma_nv'] = ma_nv
        url = f"https://dev.mobiwork.vn:4036/OpenAPI/V1/TimesheetData"
        # url = f"https://openapi.mobiwork.vn/OpenAPI/V1/TimesheetData"
        dataTimeSheet = requests.get(url=url,params=params,
            headers={
                "Authorization": basic_auth(id_dms,token_key),
            })
        
        dataTimeSheet = json.loads(dataTimeSheet.text)
        if not dataTimeSheet.get('status'):
            gen_response(500, dataTimeSheet.get('message'),[])
            return 
        data_checkin = dataTimeSheet.get('data')
        if len(data_checkin) > 0 : 
            field_not_loop = ['stt','ma_nhan_vien','ten_nhan_vien']
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
                    for field, value in employee.items():
                        if(field not in field_not_loop):
                            dataCheckShift = value.get('data_cc')
                            for data_check in dataCheckShift :
                                total +=1

                    new_log = frappe.new_doc("Dms Log")
                    data_log = {
                        "ma_nv": emp_data,
                        "checkin_start": from_date,
                        "checkin_end": to_date,
                        "total_records": total,
                        "total_import" : 0,
                        "status": "Đang tiến hành"
                    }
                    for fiel, value in data_log.items():
                        setattr(new_log,fiel,value)
                    
                    new_log.insert()
                    # employee_log = frappe.get_doc()
                    for field, value in employee.items():
                        if(field not in field_not_loop):
                            dataCheckShift = value.get('data_cc')
                            for docShift in dataCheckShift: 
                                if bool(docShift.get('thoi_gian')): 
                                    hour = docShift.get('thoi_gian').split(':')[0]
                                    minute = docShift.get('thoi_gian').split(':')[1]
                                    ime_check_server = datetime.strptime(value.get('ngay'),"%Y-%m-%dT%H:%M:%S.%fZ").replace(hour=int(hour),minute=int(minute))
                                    data = {
                                        "time" : ime_check_server,
                                        "device_id": json.dumps({"longitude": docShift.get("long"), "latitude": docShift.get("lat")}),
                                        "log_type": "IN" if docShift.get("loai") == "Vào" else "OUT",
                                        "image" : docShift.get('hinh_anh'),
                                        "employee": emp_data,                                
                                    }
                                    new_check = frappe.new_doc("Employee Checkin")
                                    for field, value in data.items():
                                        setattr(new_check, field, value)
                                    setattr(new_check,"image_attach",data.get("image"))
                                    new_check.insert()
                                    total_has +=1
                    new_log.total_import = total_has
                    new_log.status = "Thành công"
                    new_log.save()       
                    
        return
    except Exception as e:
        setattr(new_log,'status',"Thất bại")
        new_log.save()
        exception_handel(e)