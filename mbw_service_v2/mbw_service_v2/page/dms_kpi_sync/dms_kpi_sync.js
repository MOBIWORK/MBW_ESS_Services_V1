frappe.pages['dms-kpi-sync'].on_page_load = function(wrapper) {
	const dms_kpi_sync = new DmsKpiSync(wrapper);
	$(wrapper).bind("show", () => {
	  dms_kpi_sync.show();
	});


}

class DmsKpiSync {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Đồng bộ dữ liệu KPI DMS"),
			single_column: true,
		  });
	  
		  this.page.main.addClass("frappe-card");
		  this.page.body.append('<div class="table-area"></div>');
		  this.$content = $(this.page.body).find(".table-area");
	  
		  this.make_filters();
	}

	show() {
		this.refreshSync();
	  }

	refreshFilters() {
	this.fieldTypeSync.set_value("Tất cả");
	this.fieldMonth.set_value("");
	this.fieldYear.set_value("");
	this.fieldIdNvHr.set_value("");
	}

	async sync_data(type_sync, employee_code, month, year) {		
	let data = { month, year };
	if (type_sync == "Chọn nhân viên") {
		data["emplyee_code"] = employee_code;
	}

	let doc = await frappe.db.get_doc(
		"DMS Basic Authen Settings",
		"DMS Basic Authen Settings"
	);

	if (!doc?.id || !doc?.token_key) {
		frappe.msgprint({
		title: __("Cảnh báo"),
		indicator: "yellow",
		message: __("Vui lòng cấu hình DMS Basic Authen."),
		});
		return false;
	}

	data["id_dms"] = doc?.id;
	data["token_key"] = doc?.token_key;

	frappe.call({
		method: "mbw_service_v2.api.ess.sync_data.kpi_data",
		type: "POST",
		args: data,
	});

	frappe.msgprint({
		title: __("Thông báo"),
		indicator: "blue",
		message: __("Thiết lập đồng bộ thành công."),
	});
	}

	paging(page_num) {
		if(!page_num ) return [1]
		else {
			let arr_page = []
			for(let i=1 ;i<=page_num;i++) {
				arr_page.push(i)
			}
			return arr_page
		}


			
	}
	refreshSync(page) {
	frappe.call({
		method: "mbw_service_v2.api.ess.dms_sync.get_list_kpi_sync",
		args: {
			page
		},
		type: "GET",
		callback: (res) => {
		if (!res.exc) {
			$('#paging').innerHTML = "ok"
			this.$content.html(
			frappe.render_template("dms_kpi_sync", {
				list_sync: res?.result?.data || [],
				paging: {
					array: this.paging( res?.result?.total_page),
					change_page:() => {}
				},
			})
			);
			let auto_refresh = this.auto_refresh.get_value();
			if (frappe.get_route()[0] === "dms-kpi-sync" && auto_refresh) {
			setTimeout(() => this.refreshSync(), 2000);
			}
		} else {
			frappe.msgprint({
			title: __("Error"),
			indicator: "red",
			message: __("Có lỗi xảy ra."),
			});
		}
		},
	});
	}

	make_filters() {
	this.btnSync = this.page.set_primary_action("Đồng bộ", () => {
		let type_sync = this.fieldTypeSync.get_value();
		let employee_code = this.employeeCode.get_value();
		let month = this.fieldMonth.get_value();
		let year = this.fieldYear.get_value();

		if (!month || !year) {
		frappe.msgprint({
			title: __("Cảnh báo"),
			indicator: "yellow",
			message: __("Vui lòng chọn đầy đủ thông tin."),
		});
		return false;
		}

		if (type_sync == "Chọn nhân viên" && !employee_code) {
		frappe.msgprint({
			title: __("Cảnh báo"),
			indicator: "yellow",
			message: __("Nhân viên không có dữ liệu DMS."),
		});
		return false;
		}
		this.sync_data(type_sync, employee_code, month, year);
	});

	this.btnFresh = this.page.set_secondary_action("Làm mới", () => {
		this.refreshFilters();
	});

	this.fieldTypeSync = this.page.add_field({
		label: "Đồng bộ cho",
		fieldtype: "Select",
		fieldname: "type_sync",
		default: "Tất cả",
		options: ["Tất cả", "Chọn nhân viên"],
		change: () => {
		if (this.fieldTypeSync.get_value() === "Chọn nhân viên") {
			this.fieldIdNvHr.toggle(true);
		} else {
			this.fieldIdNvHr.toggle(false);
			this.fieldIdNvHr.set_value("");
		}
		},
	});

	this.fieldIdNvHr = this.page.add_field({
		label: "Nhân viên",
		fieldtype: "Link",
		fieldname: "employee_code",
		options: "Employee",
		change: async () => {
		let name = this.fieldIdNvHr.get_value();
		this.maNvDms.toggle(name);
		if (name) {
			let doc = await frappe.db.get_doc("Employee", name, [
			"employee_code_dms",
			]);

			if (!doc?.employee_code_dms) {
			frappe.msgprint({
				title: __("Cảnh báo"),
				indicator: "yellow",
				message: __("Nhân viên không có dữ liệu DMS."),
			});
			}

			this.maNvDms.set_value(doc?.employee_code_dms);
		}
		},
	});

	this.fieldIdNvHr.toggle(false);

	this.employeeCode = this.page.add_field({
		fieldname: "employee_code",
		fieldtype: "Data",
		in_list_view: 1,
		label: "Mã nhân viên Dms",
		read_only: 1,
		change: () => {
		// console.log(this.maNvDms.get_value());
		},
	});
	this.employeeCode.toggle(false);

	this.fieldMonth = this.page.add_field({
		label: "Tháng",
		fieldtype: "Select",
		fieldname: "month",
		options: [
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
		change: () => {

		},
	});

	this.fieldYear = this.page.add_field({
		label: "Năm",
		fieldtype: "Int",
		fieldname: "year",
		change: () => {
		},
	});

	this.auto_refresh = this.page.add_field({
		label: __("Tự động"),
		fieldname: "auto_refresh",
		fieldtype: "Check",
		default: 1,
		change: () => {
		if (this.auto_refresh.get_value()) {
			this.refreshSync();
		}
		},
	});
	}
	


}