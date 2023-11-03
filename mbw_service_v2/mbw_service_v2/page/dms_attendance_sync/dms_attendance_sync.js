frappe.pages["dms-attendance-sync"].on_page_load = function (wrapper) {
  const dms_attendance_sync = new DMSAttendanceSync(wrapper);
};

class DMSAttendanceSync {
  constructor(wrapper) {
    this.page = frappe.ui.make_app_page({
      parent: wrapper,
      title: __("Đồng bộ dữ liệu Chấm Công DMS"),
      single_column: true,
    });

    this.make_filters();
  }

  make_filters() {
    const optionsType_sync = [];
    this.btnSync = this.page.set_primary_action("Đồng bộ", () => {
      console.log("btnSync");
    });

    this.btnFresh = this.page.set_secondary_action("Làm mới", () => {
      this.fieldSelect.set_value("Tất cả");
      this.fieldSelect.set_value("Tất cả");
      this.fieldSelect.set_value("Tất cả");
    });

    this.fieldSelect = this.page.add_field({
      label: "Đồng bộ cho",
      fieldtype: "Select",
      fieldname: "type_sync",
      default: "Tất cả",
      options: ["Tất cả", "Nhân viên cụ thể"],
      change: () => {
        console.log(this.fieldSelect.get_value());
      },
    });

    this.fieldDateStart = this.page.add_field({
      label: "Ngày bắt đầu",
      fieldtype: "Date",
      fieldname: "date_start",
      change: () => {
        console.log(this.fieldDateStart.get_value());
      },
    });

    this.fieldDateEnd = this.page.add_field({
      label: "Ngày kết thúc",
      fieldtype: "Date",
      fieldname: "date_end",
      change: () => {
        console.log(this.fieldDateEnd.get_value());
      },
    });
  }
}
