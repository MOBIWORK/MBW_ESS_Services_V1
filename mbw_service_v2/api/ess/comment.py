import frappe
from mbw_service_v2.api.common import (
    gen_response,
    exception_handel,
    validate_image,
    BASE_URL,
    get_user_id,
    get_employee_by_user,
    get_language
)
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from datetime import datetime
from pypika import Order, CustomFunction
import json
from mbw_service_v2.config_translate import i18n


@frappe.whitelist(methods='GET')
def get_list_comment_leave(**kwargs):
    try:
        name = kwargs.get('name')
        type_comment = kwargs.get('type_comment')

        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))
        page = 1 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page'))
        start = (page - 1) * page_size

        Employee = frappe.qb.DocType('Employee')
        Comment = frappe.qb.DocType('Comment')
        UNIX_TIMESTAMP = CustomFunction('UNIX_TIMESTAMP', ['day'])
        count_all = Count('*').as_("count")

        total_doc = (
            frappe.qb.from_(Comment)
            .inner_join(Employee)
            .on(Comment.owner == Employee.user_id)
            .select(count_all)
            .where((Comment.reference_doctype == type_comment) & (Comment.reference_name == name))
            .where((Comment.comment_type == 'Comment'))
        ).run(as_dict=True)[0].get('count')

        list_employee = (
            frappe.qb.from_(Comment)
            .inner_join(Employee)
            .on(Comment.owner == Employee.user_id)
            .select(Comment.comment_by, Employee.image, Comment.content, UNIX_TIMESTAMP(Comment.creation).as_('creation'))
            .where((Comment.reference_doctype == type_comment) & (Comment.reference_name == name))
            .where((Comment.comment_type == 'Comment'))
            .offset(start)
            .limit(page_size)
            .orderby(Comment.creation, order=Order.desc)
        ).run(as_dict=True)

        for doc in list_employee:
            user_image = doc.get('image')
            doc['user_image'] = validate_image(user_image)
            del doc['image']

        result = {
            "data": list_employee,
            "total_doc": total_doc
        }
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), result)
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])


@frappe.whitelist(methods='POST')
def post_comment_leave(**kwargs):
    try:
        name_doc = kwargs.get('name')
        content = kwargs.get('content')
        type_comment = kwargs.get('type_comment')
        info_employee = get_employee_by_user(get_user_id(), ["*"])

        if not info_employee:
            gen_response(404, i18n.t('translate.user_not_found', locale=get_language()), [])
            return None

        if not type_comment or not frappe.db.get_value('DocType', type_comment):
            gen_response(404, i18n.t('translate.cmt_correct', locale=get_language()), [])
            return None

        if not frappe.db.exists(type_comment, name_doc, cache=True):
            gen_response(404, i18n.t('translate.leave_not_found', locale=get_language()), [])
            return None

        # them moi comment
        doc_comment = frappe.new_doc('Comment')
        doc_comment.reference_doctype = type_comment
        doc_comment.reference_name = name_doc
        doc_comment.comment_type = 'Comment'
        doc_comment.content = content
        doc_comment.comment_by = info_employee.get('employee_name')
        doc_comment.comment_email = info_employee.get('user_id')
        doc_comment.insert(ignore_permissions=True)

        gen_response(200, i18n.t('translate.create_success', locale=get_language()), doc_comment.as_dict(True))
    except Exception as e:
        print(e)
        gen_response(500, i18n.t('translate.error', locale=get_language()), [])
