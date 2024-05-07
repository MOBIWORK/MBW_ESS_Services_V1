# Copyright (c) 2023, chuyendev and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.desk.search import build_for_autosuggest
from frappe import _

class ESSOvertimeRequest(Document):
	pass


@frappe.whitelist()
def get_ot_approver(employee):
	ot_approver, department = frappe.db.get_value(
		"Employee", employee, ["ot_approver", "department"]
	)

	if not ot_approver and department:
		ot_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return ot_approver
@frappe.whitelist()
def get_shift_list(doctype, txt, searchfield, start, page_len, filters):
	get_shift_assignment(doctype, txt, searchfield, start, page_len, filters)
	frappe.response["results"] = build_for_autosuggest(frappe.response["values"], doctype=doctype)
	del frappe.response["values"]

@frappe.whitelist(allow_guest=True)
def get_shift_assignment(doctype, txt, searchfield, start, page_len, filters):

	if not filters.get("employee"):
		frappe.throw(_("Please select Employee first."))
	date = filters.get('date') if  filters.get('date') else False
	employee  = filters.get('employee')
	ShiftType = frappe.qb.DocType("Shift Type")
	ShiftAssignment = frappe.qb.DocType("Shift Assignment")
	query =   ShiftAssignment.employee == employee
	if date : 
		query = ((ShiftAssignment.employee == employee ) & (ShiftAssignment.start_date <= date and ShiftAssignment.end_date >= date))
	list_shift = (frappe.qb.from_(ShiftAssignment)
			   .inner_join(ShiftType)
			   .on(ShiftAssignment.shift_type == ShiftType.name)
			   .where(
				  query
				   )
			   .select(ShiftType.name)
			   .run(as_dict=True)
				 )
	return set(tuple((shift.get("name", ""),"")) for shift in list_shift)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_approvers(doctype, txt, searchfield, start, page_len, filters):

	if not filters.get("employee"):
		frappe.throw(_("Please select Employee first."))

	approvers = []
	department_details = {}
	department_list = []
	employee = frappe.get_value(
		"Employee",
		filters.get("employee"),
		["employee_name", "department", "leave_approver", "expense_approver", "shift_request_approver","ot_approver"],
		as_dict=True,
	)

	employee_department = filters.get("department") or employee.department
	if employee_department:
		department_details = frappe.db.get_value(
			"Department", {"name": employee_department}, ["lft", "rgt"], as_dict=True
		)
	if department_details:
		department_list = frappe.db.sql(
			"""select name from `tabDepartment` where lft <= %s
			and rgt >= %s
			and disabled=0
			order by lft desc""",
			(department_details.lft, department_details.rgt),
			as_list=True,
		)

	if filters.get("doctype") == "Leave Application" and employee.leave_approver:
		approvers.append(
			frappe.db.get_value("User", employee.leave_approver, ["name", "first_name", "last_name"])
		)

	if filters.get("doctype") == "Expense Claim" and employee.expense_approver:
		approvers.append(
			frappe.db.get_value("User", employee.expense_approver, ["name", "first_name", "last_name"])
		)

	if filters.get("doctype") == "Shift Request" and employee.shift_request_approver:
		approvers.append(
			frappe.db.get_value(
				"User", employee.shift_request_approver, ["name", "first_name", "last_name"]
			)
		)

	if filters.get("doctype") == "ESS Overtime Request" and employee.ot_approver:
			approvers.append(
				frappe.db.get_value(
					"User", employee.ot_approver, ["name", "first_name", "last_name"]
				)
			)

	if filters.get("doctype") == "Leave Application":
		parentfield = "leave_approvers"
		field_name = "Leave Approver"
	elif filters.get("doctype") == "Expense Claim":
		parentfield = "expense_approvers"
		field_name = "Expense Approver"
	elif filters.get("doctype") == "Shift Request":
		parentfield = "shift_request_approver"
		field_name = "Shift Request Approver"
	elif filters.get("doctype") == "ESS Overtime Request":
		parentfield = "ot_approver"
		field_name = "Overtime Approver"
	if department_list:
		for d in department_list:
			approvers += frappe.db.sql(
				"""select user.name, user.first_name, user.last_name from
				tabUser user, `tabDepartment Approver` approver where
				approver.parent = %s
				and user.name like %s
				and approver.parentfield = %s
				and approver.approver=user.name""",
				(d, "%" + txt + "%", parentfield),
				as_list=True,
			)

	if len(approvers) == 0:
		error_msg = _("Please set {0} for the Employee: {1}").format(
			_(field_name), frappe.bold(employee.employee_name)
		)
		if department_list:
			error_msg += " " + _("or for Department: {0}").format(frappe.bold(employee_department))
		frappe.throw(error_msg, title=_("{0} Missing").format(_(field_name)))

	return set(tuple(approver) for approver in approvers)
