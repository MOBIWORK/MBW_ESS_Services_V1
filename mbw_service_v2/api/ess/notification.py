import frappe
from mbw_service_v2.api.common import (
    gen_response,
    exception_handel,
    get_employee_id,
    get_user_id,
    get_employee_by_name,
    validate_image,
    BASE_URL,
    get_language
)
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from datetime import datetime
from pypika import Order, CustomFunction
import json
from mbw_service_v2.config_translate import i18n

@frappe.whitelist(methods="GET")
def get_list_notification(**kwargs):
    try:
        employee_id = get_employee_id()
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")

        page_size = 20 if not kwargs.get('page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size

        NoticeBoard = DocType("Notice Board")
        EmployeeJoin = frappe.qb.DocType('Notice Board Employee')
        Employee = frappe.qb.DocType('Employee')
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        
        query_code = (EmployeeJoin.employee == employee_id) | (NoticeBoard.apply_for == "All Employee")
        if start_time and end_time:
            start_day = datetime.fromtimestamp(int(start_time))
            end_day = datetime.fromtimestamp(int(end_time))
            query_code = query_code & (NoticeBoard.creation <= end_day) & (NoticeBoard.creation >= start_day)

        # count_all = Count('*').as_("count")
        # total_doc = (
        #     frappe.qb.from_(NoticeBoard)
        #     .left_join(EmployeeJoin)
        #     .on(NoticeBoard.name == EmployeeJoin.parent)
        #     .inner_join(Employee)
        #     .on(NoticeBoard.owner == Employee.user_id)
        #     .select(count_all)
        #     .where((NoticeBoard.from_date <= end_day))
        #     .where((NoticeBoard.to_date >= start_day))
        #     .where((EmployeeJoin.employee == employee_id) | (NoticeBoard.apply_for == "All Employee"))
        # ).run(as_dict=True)[0].get('count')

        list_doc = (
            frappe.qb.from_(NoticeBoard)
            .left_join(EmployeeJoin)
            .on(NoticeBoard.name == EmployeeJoin.parent)
            .inner_join(Employee)
            .on(NoticeBoard.owner == Employee.user_id)
            .select(NoticeBoard.name, Employee.employee_name, Employee.image, NoticeBoard.notice_title, NoticeBoard.message, NoticeBoard.description, UNIX_TIMESTAMP(NoticeBoard.from_date).as_("from_date"), UNIX_TIMESTAMP(NoticeBoard.to_date).as_("to_date"), UNIX_TIMESTAMP(NoticeBoard.creation).as_('creation'), NoticeBoard.priority_level, NoticeBoard.employee_watched)
            .offset(start)
            .limit(page_size)
            .where(query_code)
            .orderby(NoticeBoard.creation, order=Order.desc)
        ).run(as_dict=True)

        for doc in list_doc:
            user_image = doc.get('image')
            doc['user_image'] = validate_image(user_image)

            employee_watched_json = doc.get('employee_watched')
            if employee_watched_json:
                employee_watched = json.loads(employee_watched_json)
                if not any(d['name'] == employee_id for d in employee_watched):
                    doc['is_watched'] = False
                else:
                    doc['is_watched'] = True
            else:
                doc['is_watched'] = False

            del doc['employee_watched']
            del doc['image']

        result = {
            "data": list_doc,
            # "total_doc": total_doc
        }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist(methods="GET")
def get_info_notification(**kwargs):
    try:
        employee_id = get_employee_id()
        name_doc = kwargs.get("name")

        NoticeBoard = DocType("Notice Board")
        FileDoc = DocType("File")
        Employee = frappe.qb.DocType('Employee')
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        Concat = CustomFunction('CONCAT', ['str_root', 'str_concat'])

        # lay thong bao
        list_doc = (
            frappe.qb.from_(NoticeBoard)
            .inner_join(Employee)
            .on(NoticeBoard.owner == Employee.user_id)
            .select(NoticeBoard.name, NoticeBoard.notice_title, Employee.employee_name, Employee.image, NoticeBoard.message, NoticeBoard.description, UNIX_TIMESTAMP(NoticeBoard.from_date).as_("from_date"), UNIX_TIMESTAMP(NoticeBoard.to_date).as_("to_date"), NoticeBoard.priority_level, UNIX_TIMESTAMP(NoticeBoard.creation).as_('creation'), NoticeBoard.employee_watched)
            .where(NoticeBoard.name == name_doc)
            .limit(1)
        ).run(as_dict=True)

        # kiem thong bao tra co ton tai khong
        if len(list_doc):
            info = list_doc[0]
            # xu ly add nhan vien da xem
            employee_watched_json = info.get('employee_watched')
            employee_watched = []
            if employee_watched_json:
                employee_watched = json.loads(employee_watched_json)

            #  kiem tra nhan vien da xem chua
            if not any(d['name'] == employee_id for d in employee_watched):
                employee_info = get_employee_by_name(
                    employee_id, ["name", "image", "employee_name"])

                employee_image = validate_image(employee_info.get('image'))

                employee_add = {
                    "name": employee_id,
                    "image": employee_image,
                    "employee_name": employee_info.get('employee_name')
                }
                employee_watched.append(employee_add)
                employee_watched_json = json.dumps(employee_watched)

                # cap nhat nhan vien da xem cho thong bao
                doc = frappe.get_doc('Notice Board', name_doc)
                doc.employee_watched = employee_watched_json
                doc.save(ignore_permissions=True)
                frappe.db.commit()

            info["employee_watched"] = employee_watched
            # xu ly tra ve file dinh kem
            info['files'] = (frappe.qb.from_(FileDoc)
                             .select(Concat(BASE_URL, FileDoc.file_url).as_("file_url"), FileDoc.name)
                             .where(FileDoc.attached_to_name == name_doc)
                             ).run(as_dict=True)

            user_image = info.get('image')
            info['user_image'] = validate_image(user_image)
            del info['image']

            gen_response(200, i18n.t('translate.successfully', locale=get_language()), info)
        else:
            message = "Không tồn tại tài liệu"
            gen_response(404, i18n.t('translate.error', locale=get_language()), list_doc)
            return None
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist(methods="GET")
def get_list_notification_system(**kwargs):
    try:
        user_id = get_user_id()
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")

        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size

        NotificationLog = DocType("Notification Log")
        Employee = frappe.qb.DocType('Employee')
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        
        query_code = (NotificationLog.for_user == user_id)
        if start_time and end_time:
            start_day = datetime.fromtimestamp(int(start_time))
            end_day = datetime.fromtimestamp(int(end_time))
            query_code = query_code & (NotificationLog.creation <= end_day) & (NotificationLog.creation >= start_day)

        # count_all = Count('*').as_("count")
        # total_doc = (
        #     frappe.qb.from_(NotificationLog)
        #     .inner_join(Employee)
        #     .on(NotificationLog.owner == Employee.user_id)
        #     .select(count_all)
        #     .where((NotificationLog.for_user == user_id))
        # ).run(as_dict=True)[0].get('count')

        list_doc = (
            frappe.qb.from_(NotificationLog)
            .inner_join(Employee)
            .on(NotificationLog.owner == Employee.user_id)
            .select(NotificationLog.subject, NotificationLog.document_type, NotificationLog.document_name, Employee.employee_name, Employee.image, UNIX_TIMESTAMP(NotificationLog.creation).as_('creation'), NotificationLog._seen)
            .offset(start)
            .limit(page_size)
            .where(query_code)
            .orderby(NotificationLog.creation, order=Order.desc)
        ).run(as_dict=True)
        for doc in list_doc:
            user_image = doc.get('image')
            doc['user_image'] = validate_image(user_image)

            employee_watched_json = doc.get('_seen')
            if employee_watched_json:
                employee_watched = json.loads(employee_watched_json)
                if user_id in employee_watched:
                    doc['is_watched'] = True
                else:
                    doc['is_watched'] = False
            else:
                doc['is_watched'] = False

            del doc['_seen']
            del doc['image']

        result = {
            "data": list_doc,
            # "total_doc": total_doc
        }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
