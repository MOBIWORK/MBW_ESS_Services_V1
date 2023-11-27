import frappe
from mbw_service_v2.api.common import  (gen_response,get_employee_id,exception_handel,get_language,   
    get_employee_by_user,
    get_user_id
    )
from mbw_service_v2.config_translate import i18n
from mbw_service_v2.api.ess.comment import post_comment_leave

@frappe.whitelist(methods="PATCH")
def approve_leave(**data):
    try: 
        doc_type = data.get("doc_type")
        name = data.get("name")
        reason = data.get("reason")
        status = data.get("status")
        if not (doc_type and name and reason and status): 
            gen_response(500, i18n.t('translate.invalid_value', locale=get_language()), [])
            return 
        leave = frappe.get_doc(doc_type , name)
        if not leave :
            gen_response(500, i18n.t('translate.not_found', locale=get_language()), [])
            return 
        for key_att, value in data.items():
            if(key_att != "reason"):
                setattr(leave,key_att,value)
        setattr(leave,"docstatus",1)
        leave.save()
        info_employee = get_employee_by_user(get_user_id(), ["*"])
        doc_comment = frappe.new_doc('Comment')
        doc_comment.reference_doctype = doc_type
        doc_comment.reference_name = name
        doc_comment.comment_type = 'Comment'
        doc_comment.content = reason
        doc_comment.comment_by = get_employee_id()
        doc_comment.comment_email = info_employee.get('user_id')
        doc_comment.insert(ignore_permissions=True)
        leave["reason"] = reason
        gen_response(200,"",leave)
        return
    except frappe.UpdateAfterSubmitError : 
        frappe.clear_messages()
        del frappe.response["exc_type"]
        print("exc",frappe.response.get('_server_messages'))
        return
    except Exception as e:
        exception_handel(e)