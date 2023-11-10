import json
import frappe
from frappe import _
from frappe.auth import LoginManager

from datetime import datetime
from mbw_service_v2.api.common import (
    gen_response,
    generate_key,
    get_employee_by_user,
    get_language,
    get_shift_type_now,
    exception_handel
)
from mbw_service_v2.config_translate import i18n
# Đăng nhập


def add_device_notification(user_id, device_name=None, device_id=None):
    try:
        if user_id and device_name and device_id:
            name_doc = frappe.db.get_value(
                'User Device', {"device_id": device_id}, ['name'])
            if not name_doc:
                name_doc = frappe.db.get_value(
                    'User Device', {"user": user_id, "device_name": device_name}, ['name'])

            if name_doc:
                update_doc = frappe.get_doc('User Device', name_doc)
                update_doc.user = user_id
                update_doc.device_name = device_name
                update_doc.device_id = device_id
                update_doc.save(ignore_permissions=True)
            else:
                new_doc = frappe.new_doc('User Device')
                new_doc.user = user_id
                new_doc.device_name = device_name
                new_doc.device_id = device_id
                new_doc.insert(ignore_permissions=True)
        return False
    except Exception as e:
        print('===login', e)
        return False


def remove_device_notification(user_id, device_id):
    try:
        if user_id and device_id:
            frappe.db.delete("User Device", {
                "user": user_id,
                "device_id": device_id
            })
            frappe.db.commit()
        return True
    except Exception as e:
        print('===login', e)
        return False


@frappe.whitelist(allow_guest=True, methods='POST')
def login(**kwargs):
    try:
        usr = kwargs.get('usr')
        pwd = kwargs.get('pwd')
        device_name = kwargs.get('device_name')
        device_id = kwargs.get('device_id')

        login_manager = LoginManager()
        login_manager.authenticate(usr, pwd)
        validate_employee(login_manager.user)
        login_manager.post_login()

        if frappe.response["message"] == "Logged In":
            emp_data = get_employee_by_user(login_manager.user, fields=[
                                            "name", "employee_name"])
            # print("emp_data", emp_data)
            frappe.response['message'] = ""
            del frappe.local.response["full_name"]
            del frappe.local.response["home_page"]

        # them thiet bi nhan thong bao
        add_device = add_device_notification(
            login_manager.user, device_name, device_id)

        gen_response(200, i18n.t('translate.login_success', locale=get_language()), {
            "key_details": generate_key(login_manager.user),
        })

    except frappe.AuthenticationError:
        gen_response(401, i18n.t('translate.login_error', locale=get_language()), [])
        return None
    except Exception as e:
        exception_handel(e)


def validate_employee(user):
    if not frappe.db.exists("Employee", dict(user_id=user)):
        frappe.response["message"] = "Please link Employee with this user"
        raise frappe.AuthenticationError(frappe.response["message"])


# Đăng xuất
@frappe.whitelist(allow_guest=True)
def logout(device_id=None):
    try:
        auth_manager = LoginManager()
        remove_device_notification(auth_manager.user, device_id)
        auth_manager.logout()
        frappe.response["message"] = "Logged Out"
        gen_response(200, i18n.t('translate.logout_success', locale=get_language()))
    except frappe.AuthenticationError:
        gen_response(204, i18n.t('translate.logout_error', locale=get_language()), [])
        return None
    except Exception as e:
        gen_response(500, e, [])

# Khôi phục mật khẩu


@frappe.whitelist(allow_guest=True)
def reset_password(user):
    if user == "Administrator":
        gen_response(500, i18n.t('translate.not_allow', locale=get_language()), [])

    try:
        user = frappe.get_doc("User", user)
        if not user.enabled:
            gen_response(500, i18n.t('translate.email_send_fail', locale=get_language()), [])

        user.validate_reset_password()
        user.reset_password(send_email=True)

        gen_response(200, i18n.t('translate.email_send_success', locale=get_language()))
    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        frappe.clear_messages()
        gen_response(404, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist()
def checkin_shift(**data):
    try:
        fieldIn = ["employee_name", "employee",
                   "time", "skip_auto_attendance", "log_type"]
        # for field, value in dict(data).items():
        #     if field not in fieldIn:
        #         mess = {"message": "không được phép thêm " + field}
        #         frappe.local.response['message'] = json.dumps(mess)
        #         frappe.local.response['http_status_code'] = 400
        #         return None
        last_checkin = frappe.get_last_doc("Employee Checkin", filters={
                                           "employee": data.get("employee")})
        if last_checkin.get("log_type") == data.get("log_type"):
            message = i18n.t('translate.title_1', locale=get_language())
            message1 = i18n.t('translate.check_in', locale=get_language())
            message2 = i18n.t('translate.check_out', locale=get_language())
            return gen_response(500, message + "" + message1 if data.get("log_type") == "OUT" else message2)
        new_check = frappe.new_doc("Employee Checkin")
        for field, value in dict(data).items():
            setattr(new_check, field, value)
        new_check.insert()
        return new_check
    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        frappe.clear_messages()
        gen_response(404, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist()
def get_list_checkin(**data):
    try:
        return "nothing here"
    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        frappe.clear_messages()
        gen_response(404, i18n.t('translate.error', locale=get_language()), [])
