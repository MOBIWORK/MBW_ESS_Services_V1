// Copyright (c) 2023, chuyendev and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Request', {
	setup: function(frm) {
		frm.set_query("ot_approver", function() {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype
				}
			};
		});
		frm.set_query("employee", erpnext.queries.employee);
		frm.set_query("shift", function() {
			return {
				query: "mbw_service_v2.mbw_service_v2.doctype.overtime_request.overtime_request.get_shift_assignment",
				filters: {
					"employee": frm.doc.employee,
					"date": frm.doc.ot_date
				}
			};
		});
	},

	employee: function(frm) {
		frm.trigger("set_ot_approver");
	},


	set_ot_approver: function(frm) {
		if (frm.doc.employee) {
			return frappe.call({
				// method: "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
				method: "mbw_service_v2.mbw_service_v2.doctype.overtime_request.overtime_request.get_ot_approver",
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value("ot_approver", r.message);
					}
				}
			});
		}
	}
});
