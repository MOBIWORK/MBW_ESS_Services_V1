import frappe
import json
from frappe import _

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    distance_of_two,
    get_language
)

from datetime import datetime

from mbw_service_v2.config_translate import i18n

# Get the doctype
TimeSheetPosition = frappe.qb.DocType('ESS TimeSheet Position')
TimeSheetWifi = frappe.qb.DocType('TimeSheet Wifi')
TimeSheetWifiIntermediate = frappe.qb.DocType('ESS TimeSheet Wifi intermediate')
EmployeeChild = frappe.qb.DocType('ESS Employee Child')
ShiftAssignment = frappe.qb.DocType('Shift Assignment')
ShiftType = frappe.qb.DocType('Shift Type')


# Get the list of cases
@frappe.whitelist()
def get_list_ca(**kwargs):
    try:
        kwargs = frappe._dict(kwargs)
        my_filter = {}

        name = kwargs.get('name')
        if name:
            my_filter["name"] = ['like', f'%{name}%']
        page_size = 20 if not kwargs.get(
            'page_size') else int(kwargs.get('page_size'))

        page = 0 if not kwargs.get('page') or int(
            kwargs.get('page')) <= 0 else int(kwargs.get('page')) - 1
        start = page * page_size

        shift_type = frappe.db.get_list('Shift Type',
                                        filters=my_filter,
                                        fields=[
                                            'name', 'start_time', 'end_time'],
                                        order_by='name desc',
                                        start=start,
                                        page_length=page_size,
                                        )
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), shift_type)
    except Exception as e:
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# Get list of attendance locations
@frappe.whitelist(methods="GET")
def get_list_timesheet_location(**kwargs):
    try:
        employee_id = get_employee_id()
        mobile_long = False if not kwargs.get(
            'longitude') else float(kwargs.get('longitude'))
        mobile_lat = False if not kwargs.get(
            'latitude') else float(kwargs.get('latitude'))

        timesheet_position = (frappe.qb.from_(TimeSheetPosition)
                              .inner_join(EmployeeChild)
                              .on(TimeSheetPosition.name == EmployeeChild.parent)
                              .where((EmployeeChild.employee_id == employee_id) | (TimeSheetPosition.is_limited == "All employee"))                              
                              .select(TimeSheetPosition.name, TimeSheetPosition.name_address, TimeSheetPosition.address,TimeSheetPosition.geofence, TimeSheetPosition.longitude, TimeSheetPosition.latitude).run(as_dict=True))
        
        timesheet_position_all = (frappe.qb.from_(TimeSheetPosition)                          
                            .where(TimeSheetPosition.is_limited == "All employee")                              
                            .select(TimeSheetPosition.name, TimeSheetPosition.name_address, TimeSheetPosition.address,TimeSheetPosition.geofence, TimeSheetPosition.longitude, TimeSheetPosition.latitude).run(as_dict=True))
        timesheet_position = timesheet_position + timesheet_position_all
        
        shift_type = (frappe.qb.from_(ShiftAssignment)
                      .inner_join(EmployeeChild)
                      .on(EmployeeChild.employee_id == ShiftAssignment.employee)
                      .inner_join(ShiftType)
                      .on(ShiftAssignment.shift_type == ShiftType.name)
                      .where((EmployeeChild.employee_id == employee_id) & ((datetime.now() >= ShiftAssignment.start_date) &
                                                                           (datetime.now() <= ShiftAssignment.end_date)))
                      .select(ShiftAssignment.shift_type, ShiftType.start_time, ShiftType.end_time, ShiftType.begin_check_in_before_shift_start_time, ShiftType.allow_check_out_after_shift_end_time).run(as_dict=True))
        if mobile_lat != False and mobile_long != False:
            for x in timesheet_position:
                wifi = get_wifi_timesheet(x['name'])
                distance = distance_of_two(long_client=mobile_long, lat_client=mobile_lat, long_compare=float(
                    x['longitude']), lat_compare=float(x["latitude"]))
                x["distance"] = distance
                x["wifi"] = wifi
            timesheet_position = sorted(timesheet_position, key=lambda x: x['distance'])
        gen_response(200, i18n.t('translate.successfully', locale=get_language()), {
            "timesheet_position": timesheet_position,
            "shift_type": shift_type
        })

    except Exception as e:
        exception_handel(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()), [])


# wifi attendance location
def get_wifi_timesheet(name):
    data = (frappe.qb.from_(TimeSheetPosition)
            .inner_join(TimeSheetWifiIntermediate)
            .on(TimeSheetPosition.name == TimeSheetWifiIntermediate.parent)
            .where(TimeSheetPosition.name == name)
            .select(TimeSheetWifiIntermediate.wifi_name,TimeSheetWifiIntermediate.wifi_address)
            .run(as_dict=True)
            )
    return data
