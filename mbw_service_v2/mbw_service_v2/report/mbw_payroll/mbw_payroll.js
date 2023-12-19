// Copyright (c) 2023, chuyendev and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["MBW Payroll"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1 ,
			"options": [
				{ "value": 1, "label": __("January") },
				{ "value": 2, "label": __("February") },
				{ "value": 3, "label": __("March") },
				{ "value": 4, "label": __("April") },
				{ "value": 5, "label": __("May") },
				{ "value": 6, "label": __("June") },
				{ "value": 7, "label": __("July") },
				{ "value": 8, "label": __("August") },
				{ "value": 9, "label": __("September") },
				{ "value": 10, "label": __("October") },
				{ "value": 11, "label": __("November") },
				{ "value": 12, "label": __("December") },
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
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
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
			"fieldname":"view_mode",
			"label": __("View mode"),
			"fieldtype": "Select",
			"options": [
				{
					value: "em",
					label: __("Employee Sale")
				},
				{
					value: "ss",
					label: __("Sales supervisor")
				},
				{
					value: "asm",
					label: __("Area Sales Manager")
				}
			],
			"default": "em",
			"reqd": 1
		},
	],
	onload: async function(report) {
		frappe.open_dialog = async function (detail_payroll) {
			const {employee,type} = detail_payroll
			let d = new frappe.ui.Dialog({
				title: `${detail_payroll.employee_name} - Ngày ${detail_payroll.day}/${detail_payroll.month}/${detail_payroll.year}`,
				fields: [
					// Tổng hợp
					{
						label: __('Tổng hợp'),
						fieldtype:'Section Break',
						collapsible: 1
					},
					{
						label: __('Tab 1'),
						fieldtype: 'HTML',
						fieldname: "html_1",
						options: '<div id="tab1-content">Tổng hợp</div>'
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
				args: detail_payroll,
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
			method: "mbw_service_v2.mbw_service_v2.report.mbw_payroll.mbw_payroll.get_payroll_years",
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
		// if(value == null) value = ""
		return value;
	},
};
