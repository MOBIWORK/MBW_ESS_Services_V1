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
		this.fieldDateStart.set_value("");
		this.fieldDateEnd.set_value("");
		this.fieldIdNvHr.set_value("");
	  }
	
	  async sync_data(type_sync, employee_code_dms, date_start, date_end) {
		let date_fm_start = new Date(date_start);
		let date_fm_end = new Date(date_end);
	
		let date_start_new =
		  date_fm_start.getDate() +
		  "/" +
		  (date_fm_start.getMonth() + 1) +
		  "/" +
		  date_fm_start.getFullYear();
		let date_end_new =
		  date_fm_end.getDate() +
		  "/" +
		  (date_fm_end.getMonth() + 1) +
		  "/" +
		  date_fm_end.getFullYear();
	
		let data = { from_date: date_start_new, to_date: date_end_new };
		if (type_sync == "Chọn nhân viên") {
		  data["emplyee_code"] = employee_code_dms;
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
		  method: "mbw_service_v2.api.ess.sync_data.checkin_data",
		  type: "POST",
		  args: data,
		});
	
		frappe.msgprint({
		  title: __("Thông báo"),
		  indicator: "blue",
		  message: __("Thiết lập đồng bộ thành công."),
		});
	  }
	
	  refreshSync() {
		frappe.call({
		  method: "mbw_service_v2.api.ess.dms_sync.get_list_kpi_sync",
		  type: "GET",
		  callback: (res) => {
			if (!res.exc) {
			  this.$content.html(
				frappe.render_template("dms_kpi_sync", {
				  list_sync: res?.result?.data || [],
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
		  let employee_code_dms = this.maNvDms.get_value();
		  let date_start = this.fieldDateStart.get_value();
		  let date_end = this.fieldDateEnd.get_value();
	
		  if (!date_start || !date_end) {
			frappe.msgprint({
			  title: __("Cảnh báo"),
			  indicator: "yellow",
			  message: __("Vui lòng chọn đầy đủ thông tin."),
			});
			return false;
		  }
	
		  if (type_sync == "Chọn nhân viên" && !employee_code_dms) {
			frappe.msgprint({
			  title: __("Cảnh báo"),
			  indicator: "yellow",
			  message: __("Nhân viên không có dữ liệu DMS."),
			});
			return false;
		  }
		  this.sync_data(type_sync, employee_code_dms, date_start, date_end);
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
		  fieldname: "ds_nv",
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
	
		this.maNvDms = this.page.add_field({
		  fieldname: "ma_nv_dms",
		  fieldtype: "Data",
		  in_list_view: 1,
		  label: "Mã nhân viên Dms",
		  read_only: 1,
		  change: () => {
			// console.log(this.maNvDms.get_value());
		  },
		});
		this.maNvDms.toggle(false);
	
		this.fieldDateStart = this.page.add_field({
		  label: "Ngày bắt đầu",
		  fieldtype: "Date",
		  fieldname: "date_start",
		  change: () => {
			let start_date = this.fieldDateStart.get_value();
			let end_date = this.fieldDateEnd.get_value();
			if (end_date && start_date) {
			  let time_start = new Date(start_date);
			  let time_end = new Date(end_date);
			  if ((time_end - time_start) / 1000 > 30 * 24 * 60 * 60) {
				let date_end = time_start.getTime() + 30 * 24 * 60 * 60 * 1000;
				date_end = new Date(date_end);
				let day =
				  String(date_end.getDate()).length == 1
					? "0" + String(date_end.getDate())
					: String(date_end.getDate());
				let mon =
				  String(date_end.getMonth() + 1).length == 1
					? "0" + String(date_end.getMonth() + 1)
					: String(date_end.getMonth() + 1);
	
				let date_new = date_end.getFullYear() + "-" + mon + "-" + day;
	
				this.fieldDateEnd.set_value(date_new);
			  }
			}
		  },
		});
	
		this.fieldDateEnd = this.page.add_field({
		  label: "Ngày kết thúc",
		  fieldtype: "Date",
		  fieldname: "date_end",
		  change: () => {
			let start_date = this.fieldDateStart.get_value();
			let end_date = this.fieldDateEnd.get_value();
			if (end_date && start_date) {
			  let time_start = new Date(start_date);
			  let time_end = new Date(end_date);
			  if ((time_end - time_start) / 1000 > 30 * 24 * 60 * 60) {
				let date_end = time_end.getTime() - 30 * 24 * 60 * 60 * 1000;
				date_end = new Date(date_end);
				let day =
				  String(date_end.getDate()).length == 1
					? "0" + String(date_end.getDate())
					: String(date_end.getDate());
				let mon =
				  String(date_end.getMonth() + 1).length == 1
					? "0" + String(date_end.getMonth() + 1)
					: String(date_end.getMonth() + 1);
	
				let date_new = date_end.getFullYear() + "-" + mon + "-" + day;
	
				this.fieldDateStart.set_value(date_new);
			  }
			}
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