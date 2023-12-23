// Copyright (c) 2023, chuyendev and contributors
// For license information, please see license.txt

function bonus_sell(rate, actually) {

	if(rate >= 1.2) {
		return actually*0.15
	}
	else if (rate >=1.1) {
		return actually*0.12
	}
	else if (rate >=1) {
		return actually*0.1
	}
	else if (rate >= 0.9) {
		return actually*0.08
	}
	else if (rate >=0.8) {
		return actually*0.05
	}
	else return 0

}

function bonus_kpi(rate) {
	if (rate >=1) {
		return 600000
	}
	else if (rate >= 0.9) {
		return 500000
	}
	else if (rate >=0.8) {
		return 400000
	}
	else return 0
}

frappe.ui.form.on('DMS KPI', {
	// refresh: function(frm) {

	// }
	actually_achieved_sell_out: async (frm) => {
		let spending_sell_out = frm.doc.spending_sell_out
		if(spending_sell_out) {
			let rate_sell_out = parseFloat((frm.doc.actually_achieved_sell_out)/spending_sell_out,2)
			frm.set_value("rate_sell_out",rate_sell_out*100)
			frm.set_value("bonus_sales",bonus_sell(rate_sell_out,frm.doc.actually_achieved_sell_out))
		}
	},
	actually_achieved_sell_in: async (frm) => {
		let spending_sell_in = frm.doc.spending_sell_in
		if(spending_sell_in) {
			let rate_sell_in = parseFloat((frm.doc.actually_achieved_sell_in)/spending_sell_in,2)
			frm.set_value("rate_sell_in",rate_sell_in*100)
		}
	},
	actually_achieved_kpi1: async (frm) => {
		let spending_kpi1 = frm.doc.spending_kpi1
		if(spending_kpi1) {
			let rate_kpi1 = parseFloat((frm.doc.actually_achieved_kpi1)/spending_kpi1,2)
			frm.set_value("rate_kpi1",rate_kpi1*100)
			frm.set_value("bonus_kpi1",bonus_kpi(rate_kpi1))
		}
	}

});
