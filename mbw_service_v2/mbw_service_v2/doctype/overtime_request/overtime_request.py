# Copyright (c) 2023, chuyendev and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.desk.search import build_for_autosuggest

class OvertimeRequest(Document):
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

