import frappe
@frappe.whitelist(methods="GET",allow_guest= True)
def get_ip_network():
    try:
        import socket
        client_ip = frappe.local.request.remote_addr
        import netifaces
        import requests
        import psutil

        # Lấy địa chỉ IP mạng của giao diện mạng (ví dụ: eth0)
        network_interfaces = psutil.net_if_addrs().keys() 
        # return network_interfaces
        network_interface = "enp2s0"
        network_ip = netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']
        print(f"Địa chỉ IP mạng của giao diện {network_interface}: {network_ip}")        
        return network_ip
    except Exception as e:
        return e
        # exception_handel(e)

