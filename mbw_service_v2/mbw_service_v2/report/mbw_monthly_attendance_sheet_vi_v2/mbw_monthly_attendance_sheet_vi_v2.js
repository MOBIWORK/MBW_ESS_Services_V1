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
		{
			"fieldname":"summarized_view",
			"label": __("Summarized View"),
			"fieldtype": "Check",
			"Default": 0,
		}
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
						var result = r.result
						var html_1 = ""
						var html_2 = ""
						var html_3 = ""

						// Tông hợp
						var info_synthesis = result.info_synthesis
						for (const [k, v] of Object.entries(info_synthesis)) {
							if(k != "thong_tin_cham_cong"){
								if(typeof(v.value) === "object"){
									html_1 += `<div><strong>${v.label}</strong></div>`
									for (const [k1, v1] of Object.entries(v.value)){
										html_1 += `<div>${v1.label}: ${v1.value}</div>`
									}
								}else{
									html_1 += `<div><strong>${v.label}</strong>: ${v.value}</div>`
								}
							}else{
								html_1 += `<div><strong>${v.label}</strong></div>`
								let head_table = '';
								v.value.head_table.forEach(el => {
									head_table+= `<th scope="col">${el}</th>`
								});
								let body_table = ''
								if (v.value.data.length){
									v.value.data.forEach(el => {
										body_table += "<tr>"
										body_table+= `
												<th scope="row">${el.shift_name}</th>
												<td>${el.work_hour}</td>
												<td>${el.attendance_work}</td>
												<td>${el.reality_hour}</td>
												<td>${el.reality_attendance_work}</td>
											`
										body_table += "<td>"
										el.checkin.forEach(el1 => {
											body_table += `<p><a href="${el1.link}" class="link-primary">${el1.label}</a></p>`
										})
										body_table += "</td></tr>"
									});
								}else{
									body_table = `<tr class="text-center">
									<td colspan="${v.value.head_table.length}">${v.value.message_empty}</td>
								  </tr>`
								}

								html_1 += `
								<div style="overflow: auto">
									<table class="table table-bordered" style="min-width: 1000px">
										<thead>
											<tr>
											${head_table}
											</tr>
										</thead>
										<tbody>
											${body_table}
										</tbody>
									</table>
								</div>
								`
							}
						}
						// Don tu
						var leaves = result.leaves
						var head_table = ""
						var body_table = ""
						leaves.head_table.forEach(el => {
							head_table+= `<th scope="col">${el}</th>`
						});

						if (leaves.data.length){
							leaves.data.forEach(el => {
								body_table += "<tr>"
								body_table+= `
										<th scope="row">${el.leave_type}</th>
										<td>${el.creation}</td>
										<td>${el.shift}</td>
										<td>${el.attendance_change}</td>
										<td>${el.status}</td>
										<td><p><a href="${el.link}" class="link-primary">${el.name}</a></p></td>
										<td>${el.receive_salary}</td>
									`
							});
						}else{
							body_table = `<tr class="text-center">
							<td colspan="${leaves.head_table.length}">${leaves.message_empty}</td>
						  </tr>`
						}

						html_2 += `
							<div style="overflow: auto">
								<table class="table table-bordered" style="min-width: 1000px">
									<thead>
										<tr>
										${head_table}
										</tr>
									</thead>
									<tbody>
										${body_table}
									</tbody>
								</table>
							</div>
						`
						// Ngay nghi
						head_table = ""
						body_table = ""
						var holidays = result.holidays
						holidays.head_table.forEach(el => {
							head_table+= `<th scope="col">${el}</th>`
						});

						if (holidays.data.length){
							holidays.data.forEach(el => {
								body_table += "<tr>"
								body_table+= `
										<th scope="row">${el.stt}</th>
										<td>${el.holiday_date}</td>
										<td>${el.description}</td>
										<td>${el.receive_salary}</td>
									`
							});
						}else{
							body_table = `<tr class="text-center">
							<td colspan="${holidays.head_table.length}">${holidays.message_empty}</td>
						  </tr>`
						}

						html_3 += `
							<div style="overflow: auto">
								<table class="table table-bordered" style="min-width: 1000px">
									<thead>
										<tr>
										${head_table}
										</tr>
									</thead>
									<tbody>
										${body_table}
									</tbody>
								</table>
							</div>
						`

						d.fields_dict.html_1.$wrapper.html(html_1);
						d.fields_dict.html_2.$wrapper.html(html_2);
						d.fields_dict.html_3.$wrapper.html(html_3);

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

