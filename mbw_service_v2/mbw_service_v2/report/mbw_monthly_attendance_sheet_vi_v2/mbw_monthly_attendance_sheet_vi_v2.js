// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["MBW Monthly Attendance Sheet vi v2"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1 ,
			"options": [
				{ "value": 1, "label": __("Jan") },
				{ "value": 2, "label": __("Feb") },
				{ "value": 3, "label": __("Mar") },
				{ "value": 4, "label": __("Apr") },
				{ "value": 5, "label": __("May") },
				{ "value": 6, "label": __("June") },
				{ "value": 7, "label": __("July") },
				{ "value": 8, "label": __("Aug") },
				{ "value": 9, "label": __("Sep") },
				{ "value": 10, "label": __("Oct") },
				{ "value": 11, "label": __("Nov") },
				{ "value": 12, "label": __("Dec") },
			],
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
		},
		{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": ["","Branch","Grade","Department","Designation"]
		},
	],
	onload: async function(report) {
		frappe.open_dialog = async function (detail_check) {
			let d = new frappe.ui.Dialog({
				title: `${detail_check.employee_name} - Ngày ${detail_check.day}/${detail_check.month}/${detail_check.year}`,
				fields: [
					// Tông hợp
					{
						label: __('Tông hợp'),
						fieldtype:'Section Break',
						collapsible: 1
					},
					{
						label: __('Tab 1'),
						fieldtype: 'HTML',
						fieldname: "html_1",
						options: '<div id="tab1-content">Tông hợp</div>'
					},
					// Đơn từ
					{
						label: __('Đơn từ'),
						fieldtype:'Section Break',
						collapsible: 1
					},
					{
						label: __('Tab 2'),
						fieldtype: 'HTML',
						fieldname: "html_2",
						options: '<div id="tab2-content">Đơn từ</div>'
					},
					// Ngày nghỉ
					{
						label: __('Ngày nghỉ'),
						fieldtype:'Section Break',
						collapsible: 1
					},
					{
						label: __('Tab 2'),
						fieldtype: 'HTML',
						fieldname: "html_3",
						options: '<div id="tab2-content">Ngày nghỉ</div>'
					},
				]
			});
			
			d.$wrapper.find('.modal-dialog').addClass('modal-xl');
			await frappe.call({
				type: "GET",
				method: "mbw_service_v2.api.ess.report.get_report_attendance_sheet",
				args: detail_check,
				callback: function(r) {
					if (!r.exc) {
						// Tông hợp
						var result = r.result
						var html_1 = ""
						for (const [key, value] of Object.entries(result.info_employee)) {
							if(typeof(value) === "object"){
								html_1 += `<div><strong>${key}</strong></div>`
								for (const [k, v] of Object.entries(value)){
									html_1 += `<div>${k}: ${v}</div>`
								}
							}else{
								html_1 += `<div><strong>${key}</strong>: ${value}</div>`
							}
						}				  
						d.fields_dict.html_1.$wrapper.html(html_1);

						// Đơn từ

						// Ngày nghỉ
					}
				}
			});

			d.show();
		}
		return  frappe.call({
			method: "mbw_service_v2.mbw_service_v2.report.mbw_monthly_attendance_sheet_vi_v2.mbw_monthly_attendance_sheet_vi_v2.get_attendance_years",
			callback: function(r) {
				var year_filter = frappe.query_report.get_filter('year');
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});
	},
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		const summarized_view = frappe.query_report.get_filter_value('summarized_view');
		const group_by = frappe.query_report.get_filter_value('group_by');

		if (!summarized_view) {
			if ((group_by && column.colIndex > 3) || (!group_by && column.colIndex > 2)) {
				if (value == 'P' || value == 'WFH')
					value = "<span style='color:green'>" + value + "</span>";
				else if (value == 'A')
					value = "<span style='color:red'>" + value + "</span>";
				else if (value == 'HD')
					value = "<span style='color:orange'>" + value + "</span>";
				else if (value == 'L')
					value = "<span style='color:#318AD8'>" + value + "</span>";
			}
		}

		return value;
	}
}

