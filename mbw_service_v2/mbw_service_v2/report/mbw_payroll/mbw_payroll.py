# Copyright (c) 2023, chuyendev and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee"},
		{"fieldname": "employee_name", "label": "Employee name", "fieldtype": "Data"},
		{"fieldname": "positions", "label": "Positions", "fieldtype": "Data"},
		{"fieldname": "area_manager", "label": "Area manager", "fieldtype": "Data"},
		{"fieldname": "wage", "label": "Wage", "fieldtype": "Data"},
		{"fieldname": "dependent_person", "label": "Dependent person", "fieldtype": "Data"},
		{"fieldname": "days", "label": "Days", "fieldtype": "Data"},
		{"fieldname": "salary_and_allowance", "label": "Salary and allowance", "fieldtype": "Data"},
		{"fieldname": "total_not_bonuses", "label": "Total not bonuses", "fieldtype": "Float"},
		{"fieldname": "spending_sell_in", "label": "Spending sell in", "fieldtype": "Float"},
		{"fieldname": "actually_achieved_sell_in", "label": "Actually achieved sell in", "fieldtype": "Float"},
		{"fieldname": "rate_sell_in", "label": "Rate sell in", "fieldtype": "Float"},
		{"fieldname": "spending_sell_out", "label": "Spending sell out", "fieldtype": "Float"},
		{"fieldname": "actually_achieved_sell_out", "label": "Actually achieved sell out", "fieldtype": "Float"},
		{"fieldname": "rate_sell_out", "label": "Rate sell out", "fieldtype": "Float"},
		{"fieldname": "bonus_sales", "label": "Bonus sales", "fieldtype": "Float"},
		{"fieldname": "spending_kpi1", "label": "Spending KPI1", "fieldtype": "Float"},
		{"fieldname": "actually_achieved_kpi1", "label": "Actually achieved KPI1", "fieldtype": "Float"},
		{"fieldname": "rate_kpi1", "label": "Rate KPI1", "fieldtype": "Float"},
		{"fieldname": "bonus_kpi1", "label": "Bonus KPI1", "fieldtype": "Float"},
		{"fieldname": "spending_kpi2", "label": "Spending KPI2", "fieldtype": "Float"},
		{"fieldname": "actually_achieved_kpi2", "label": "Actually achieved KPI2", "fieldtype": "Float"},
		{"fieldname": "rate_kpi2", "label": "Rate KPI2", "fieldtype": "Float"},
		{"fieldname": "bonus_kpi2", "label": "Bonus KPI2", "fieldtype": "Float"},
		{"fieldname": "other_bonuses", "label": "Other bonuses", "fieldtype": "Float"},
		{"fieldname": "gross_pay", "label": "Gross pay", "fieldtype": "Float"},
		{"fieldname": "tax_deductions", "label": "Tax deductions", "fieldtype": "Float"},
		{"fieldname": "taxable_income", "label": "Taxable income", "fieldtype": "Float"},
		{"fieldname": "tax", "label": "Tax", "fieldtype": "Float"},
		{"fieldname": "social_insurance", "label": "Social insurance", "fieldtype": "Float"},
		{"fieldname": "minus_advance", "label": "Minus advance", "fieldtype": "Float"},
		{"fieldname": "other_deductions", "label": "Other deductions", "fieldtype": "Float"},
		{"fieldname": "total_deductions", "label": "Total deductions", "fieldtype": "Float"},
		{"fieldname": "real_total", "label": "Real total", "fieldtype": "Float"},
	]

	data = frappe.get_all("Payroll MBW", 
					   filters=filters, 
					   fields=["*"])
	result = []

	for d in data:
		row = [d.employee, d.employee_name, d.positions, d.area_manager, d.wage, d.dependent_person
		 , d.days, d.salary_and_allowance, d.total_not_bonuses, d.spending_sell_in, d.actually_achieved_sell_in
		 , d.rate_sell_in, d.spending_sell_out, d.actually_achieved_sell_out , d.rate_sell_out
		 , d.bonus_sales, d.spending_kpi1, d.actually_achieved_kpi1, d.rate_kpi1, d.bonus_kpi1
		 , d.spending_kpi2, d.actually_achieved_kpi2, d.rate_kpi2, d.bonus_kpi2, d.other_bonuses
		 , d.gross_pay, d.tax_deductions, d.taxable_income, d.tax, d.social_insurance
		 , d.minus_advance, d.other_deductions, d.total_deductions, d.real_total]
		result.append(row)

	return columns, result
