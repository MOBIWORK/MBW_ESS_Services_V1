import frappe
@frappe.whitelist(methods="GET",allow_guest= True)
def get_ip_network():
    try:
        # # Lấy địa chỉ IP của người dùng từ tiêu đề HTTP "X-Forwarded-For"
        remote_ip = frappe.get_request_header("X-Forwarded-For")

        if remote_ip:
            # Nếu có giá trị X-Forwarded-For, nó chứa địa chỉ IP của người dùng
            print(f"Địa chỉ IP của người dùng 1: {remote_ip}")
        else:
            # Nếu không có X-Forwarded-For, thử lấy từ REMOTE_ADDR
            remote_ip = frappe.local.request.environ.get('REMOTE_ADDR')
            print(f"Địa chỉ IP của người dùng 2: {remote_ip}")

        return remote_ip        
    except Exception as e:
        return e
        # exception_handel(e)

