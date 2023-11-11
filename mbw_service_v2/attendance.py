import frappe
from frappe.utils import cint, flt
from datetime import datetime, timedelta
import time


def calc_minutes(time_shift, time_real, type_calc='late_entry'):
    fmt = '%H:%M:%S'
    time_shift_obj = time_shift
    time_real_obj = time_real
    time_real_obj = timedelta(
        hours=time_real_obj.hour, minutes=time_real_obj.minute, seconds=time_real_obj.second)

    d1 = datetime.strptime(str(time_shift_obj), fmt)
    d2 = datetime.strptime(str(time_real_obj), fmt)
    d1_ts = time.mktime(d1.timetuple())
    d2_ts = time.mktime(d2.timetuple())

    if type_calc == "late_entry":
        late_check_in = round((d2_ts-d1_ts) / 60)
    else:
        late_check_in = round((d1_ts-d2_ts) / 60)
    minutes = late_check_in if late_check_in > 0 else 0

    return minutes


@frappe.whitelist()
def calculate_late_working_hours(doc, method):
    if doc.shift:
        shift_type = frappe.db.get_value('Shift Type', doc.shift, [
            'start_time', 'end_time', 'late_entry_grace_period', 'early_exit_grace_period'], as_dict=True)

        if shift_type:
            # Late check-in time
            start_time = shift_type.get('start_time')
            late_entry_grace_period = shift_type.get(
                'late_entry_grace_period') if shift_type.get('late_entry_grace_period') else 0
            if doc.in_time:
                minutes = calc_minutes(
                    start_time, doc.in_time, "late_entry") - late_entry_grace_period
                doc.late_check_in = minutes
            else:
                doc.late_check_in = 0

            # Early check-out time
            end_time = shift_type.get('end_time')
            early_exit_grace_period = shift_type.get(
                'early_exit_grace_period') if shift_type.get('early_exit_grace_period') else 0
            if doc.out_time:
                minutes = calc_minutes(
                    end_time, doc.out_time, 'early_exit') - early_exit_grace_period
                doc.early_check_out = minutes
            else:
                doc.early_check_out = 0
        else:
            doc.late_check_in = 0
            doc.early_check_out = 0
    else:
        doc.late_check_in = 0
        doc.early_check_out = 0
