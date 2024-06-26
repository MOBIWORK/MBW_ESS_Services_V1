import frappe

def after_install(name,**arg) :
    create_work_state()
    create_role()
    create_work_flow()
    pass


def create_work_state() :
    list_state=[
        {
            "workflow_state_name":"Draft"
        },
        {
            "workflow_state_name":"Approval Pending by Manager"
        },
        {
            "workflow_state_name":"Approval Pending by HR Manager"
        },
    ]

    for state in list_state:
        if not frappe.db.exists("Workflow State",state.get("workflow_state_name")):
            new_state = frappe.new_doc("Workflow State")
            for key, value in state.items():
                new_state.set(key,value)
            new_state.insert()
            try:
                new_state.insert()
            except Exception as e:
                name=state.get("workflow_state_name")
                print(f"lỗi tạo workflow state: {name} - {e}")
        frappe.db.commit()

    
def create_role() :
    roles=[
        {
            "role_name":"Approve Overtime Request"
        },
        {
            "role_name":"Approve Attendance Request"
        }
    ]

    for role in roles:
        if not frappe.db.exists("Role",role.get("role_name")):
            new_state = frappe.new_doc("Role")
            for key, value in role.items():
                new_state.set(key,value)
            new_state.insert()
            try:
                new_state.insert()
            except Exception as e:
                name= role.get("role_name")
                print(f"lỗi tạo role: {name} - {e}")
        frappe.db.commit()
        
       
def create_work_flow():
    workflows = [
        {
        "workflow_name":"Quy trình giải trình chấm công",
        "workflow_state_field":"workflow_state",
        "is_active":1,
        "document_type": "Attendance Request",
        "states": [
                {
                    "state": "Draft",
                    "doc_status": "0",
                    "is_optional_state": 0,
                    "allow_edit": "Employee",
                },
                {
                    "state": "Approved",
                    "doc_status": "1",
                    "is_optional_state": 0,
                    "allow_edit": "Approve Attendance Request",
                },
                {
                    "state": "Rejected",
                    "doc_status": "1",
                    "is_optional_state": 0,
                    "allow_edit": "Approve Attendance Request",
                }
            ],
        "transitions": [
                {
                    "state": "Draft",
                    "action": "Approve",
                    "next_state": "Approved",
                    "allowed": "Approve Attendance Request",
                    "allow_self_approval": 1,
                },
                {
                    "state": "Draft",
                    "action": "Reject",
                    "next_state": "Rejected",
                    "allowed": "Approve Attendance Request",
                    "allow_self_approval": 1,
                }
            ]
        },
        {
            "workflow_name": "Quy trình yêu cầu làm thêm",
            "document_type": "ESS Overtime Request",
            "is_active": 1,
            "override_status": 0,
            "send_email_alert": 0,
            "workflow_state_field": "workflow_state",
            "doctype": "Workflow",
            "states": [
                {
                    "state": "Draft",
                    "doc_status": "0",
                    "is_optional_state": 0,
                    "allow_edit": "Employee",
                },
                {
                    
                    "state": "Approved",
                    "doc_status": "1",
                    "is_optional_state": 0,
                    "allow_edit": "Approve Overtime Request"
                },
                {
                  
                    "state": "Rejected",
                    "doc_status": "1",
                    "is_optional_state": 0,
                    "allow_edit": "Approve Overtime Request",
                }
            ],
            "transitions": [
                {
                    "state": "Draft",
                    "action": "Approve",
                    "next_state": "Approved",
                    "allowed": "Approve Overtime Request",
                    "allow_self_approval": 1,
                },
                {
                    "state": "Draft",
                    "action": "Reject",
                    "next_state": "Rejected",
                    "allowed": "Approve Overtime Request",
                    "allow_self_approval": 1
                }
            ]
        }

    ]

    for workflow in workflows:
        if not frappe.db.exists("Workflow",workflow.get("workflow_name")):
            new_workflow = frappe.new_doc("Workflow")
            for key,value in workflow.items():
                new_workflow.set(key,value)
            try:
                new_workflow.insert()
            except Exception as e:
                name= workflow.get("workflow_name")
                print(f"lỗi tạo workflow: {name} - {e}")
    frappe.db.commit()
