# In your Frappe backend code
import frappe

@frappe.whitelist()
def handle_realtime_event(data):
    # Process the data and broadcast the update
    frappe.publish_realtime(event='some-event', message=data, user='admin', doctype='My DocType', docname='My Doc', after_commit=True, everyone=True, now=True, ondelete=True, room=frappe.get_request_site_address())