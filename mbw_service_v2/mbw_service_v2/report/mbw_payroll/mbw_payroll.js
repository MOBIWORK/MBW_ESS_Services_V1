// Copyright (c) 2023, chuyendev and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["MBW Payroll"] = {
	"filters": [
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
	],
};
