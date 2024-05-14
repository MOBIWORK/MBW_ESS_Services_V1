import frappe
from frappe import _
from mbw_service_v2.api.common import (gen_response,exception_handel,get_info_employee,get_employee_id,get_language, post_image, validate_image,get_user_id)
from datetime import datetime
import base64
from mbw_service_v2.config_translate import i18n
BASE_URL = frappe.utils.get_request_site_address()
# cập nhật tài khoản
@frappe.whitelist(methods="PUT")
def update_profile(**kwargs):
    try:
        employee_id = get_employee_id()
        date_format = '%Y/%m/%d'
        fieldAccess = ["full_name", "image", "gender", "date_of_birth", "cell_number", 'current_address']
        del kwargs['cmd']
        
        for field, value in dict(kwargs).items():
            if field not in fieldAccess:
                mess = i18n.t('translate.invalid_value', locale=get_language()) + "" + field
                frappe.local.response['message'] = mess
                frappe.local.response['http_status_code'] = 404
                frappe.response["result"] = []
                return None
            elif field == 'date_of_birth':
                dob = int(kwargs.get('date_of_birth'))
                date_of_birth = int(kwargs.get('date_of_birth'))
                date_of_birth = datetime.fromtimestamp(date_of_birth).strftime(date_format)
                kwargs['date_of_birth'] = date_of_birth
                
            elif field == 'full_name':
                if kwargs.get("full_name"):
                    full_name = kwargs.get("full_name")
                    list_name = full_name.split(" ")
                    if len(list_name) == 1:
                        kwargs['first_name'] = list_name[0]
                    elif len(list_name) == 2:
                        kwargs['first_name'] = list_name[0]
                        kwargs['last_name'] = list_name[1]
                    else:
                        kwargs['first_name'] = list_name[0]
                        kwargs['middle_name'] = ' '.join(list_name[1:-1])
                        kwargs['last_name'] = list_name[-1]
                    
                    del kwargs['full_name']
            elif field == "image":
                face_image = kwargs.get("image")
                name_image = "avarta_"+employee_id
                kwargs['image'] = post_image(name_image, face_image, "Employee", employee_id)
                
       
        if frappe.db.exists("Employee", employee_id, cache=True):
            doc = frappe.get_doc('Employee', employee_id)
            for field, value in dict(kwargs).items():
                setattr(doc, field, value)
                if field == "date_of_birth":
                    kwargs['date_of_birth'] = dob
            doc.save()
        
        gen_response(200, i18n.t('translate.update_success', locale=get_language()),kwargs)

    except Exception as e:
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
        return exception_handel(e)


# lấy thông tin nhân viên
@frappe.whitelist(methods="GET")
def get_employee_info() :
    try:
        employee_id = get_employee_id()
        if not employee_id:
            return gen_response(404 ,i18n.t('translate.user_not_found', locale=get_language()),[])
        
        user_info = get_info_employee(name=employee_id, fields=["employee", "employee_name", "company", "gender", "date_of_birth", "date_of_joining" ,"salutation", "image","user_id","department", "designation","cell_number", "current_address"])
        user_info['date_of_birth'] = user_info['date_of_birth']
        if user_info['image']:
            user_info['image'] = validate_image(user_info['image'])

        gen_response(200,i18n.t('translate.successfully', locale=get_language()),user_info)
    except Exception as e:
        exception_handel(e)


# lấy thông tin nhân viên
@frappe.whitelist(methods="GET")
def get_user_info() :
    try:
        user_id = get_user_id()
        if not user_id:
            return gen_response(404 ,i18n.t('translate.user_not_found', locale=get_language()),[])
        
        user_info = frappe.db.get_value("User",user_id,["full_name","email","user_image","name"],as_dict=1)
        employee_info = ""
        try:
            employee = frappe.db.get_value("Employee",{"user_id":user_id},["department"],as_dict=1)
            if employee and employee.department:
                employee_info = employee.department
            else: 
                raise ValueError("Không tìm thấy nhân viên")
        except Exception as e:
            employee_info= "unknown"
        user_info["department"] = employee_info
        if user_info.get("user_image"):
            user_info["user_image"] = BASE_URL+user_info["user_image"]
        gen_response(200,_(""),user_info)
    except Exception as e:
        exception_handel(e)