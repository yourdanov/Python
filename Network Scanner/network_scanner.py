import scapy.all as scapy
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Label
import threading
import nmap
import json
import time

# Variables to store scanned data
devices_info = []
alerts = []

# Function to scan the local network using nmap
def network_scan(network_range):
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=network_range, arguments='-n -sT')
        devices = []
        for host in nm.all_hosts():
            device_info = {
                'ip': host,
                'mac': nm[host]['addresses'].get('mac', 'N/A'),
                'status': nm[host].state(),
                'open_ports': nm[host].all_tcp() if 'tcp' in nm[host] else []
            }
            devices.append(device_info)
        return devices
    except Exception as e:
        print(f"Error during network scan: {e}")
        messagebox.showerror("Scan Error", f"An error occurred during network scan: {e}")
        return []

# GUI Setup
class CyberSecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cyber Security Application")
        self.root.geometry("1400x600")
        self.root.configure(bg="#f0f0f0")

        # Frame for Network Scan
        self.scan_frame = ttk.LabelFrame(root, text="Network Scan", padding=(10, 10))
        self.scan_frame.pack(fill="x", padx=10, pady=10)

        self.network_label = ttk.Label(self.scan_frame, text="Enter Network Range (e.g., 192.168.0.0/24):")
        self.network_label.pack(side="left", padx=5, pady=5)

        self.network_entry = ttk.Entry(self.scan_frame, width=30)
        self.network_entry.pack(side="left", padx=5, pady=5)

        self.scan_button = ttk.Button(self.scan_frame, text="Scan Network", command=self.scan_network)
        self.scan_button.pack(side="left", padx=5, pady=5)

        self.devices_tree = ttk.Treeview(self.scan_frame, columns=("IP Address", "MAC Address", "Status", "Open Ports"), show='headings')
        self.devices_tree.heading("IP Address", text="IP Address")
        self.devices_tree.heading("MAC Address", text="MAC Address")
        self.devices_tree.heading("Status", text="Status")
        self.devices_tree.heading("Open Ports", text="Open Ports")
        self.devices_tree.pack(fill="x", pady=10)

        # Frame for Alerts
        self.alerts_frame = ttk.LabelFrame(root, text="Alerts", padding=(10, 10))
        self.alerts_frame.pack(fill="x", padx=10, pady=10)

        self.alerts_listbox = tk.Listbox(self.alerts_frame, height=10)
        self.alerts_listbox.pack(fill="x", pady=5)
        self.alerts_listbox.bind("<Double-Button-1>", self.show_alert_details)

        # Start monitoring logs in a separate thread
        self.start_monitoring_thread()

    def scan_network(self):
        network_range = self.network_entry.get()
        if not network_range:
            messagebox.showerror("Input Error", "Please enter a network range to scan.")
            return

        self.scan_message = tk.Label(self.root, text="Scanning the network, please wait...", bg="#f0f0f0", font=("Helvetica", 12))
        self.scan_message.pack(pady=10)
        
        def perform_scan():
            global devices_info
            devices_info = network_scan(network_range)
            self.update_devices_tree()
            self.scan_message.destroy()
        
        scan_thread = threading.Thread(target=perform_scan)
        scan_thread.start()

    def update_devices_tree(self):
        # Clear existing entries
        for row in self.devices_tree.get_children():
            self.devices_tree.delete(row)

        # Insert new data
        for device in devices_info:
            self.devices_tree.insert("", "end", values=(device['ip'], device['mac'], device['status'], ", ".join(map(str, device['open_ports']))))

    def update_alerts_ui(self):
        # Clear existing alerts
        self.alerts_listbox.delete(0, tk.END)

        # Insert new alerts
        for alert in alerts:
            alert_text = f"{alert['timestamp']} - {alert['description']} - Severity: {alert['severity']}"
            self.alerts_listbox.insert(tk.END, alert_text)

    def start_monitoring_thread(self):
        monitor_thread = threading.Thread(target=self.monitor_logs)
        monitor_thread.daemon = True
        monitor_thread.start()

    def monitor_logs(self):
        while True:
            # Simulate log monitoring
            log_entry = f"Suspicious activity detected at {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}"
            alert_details = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'description': 'Suspicious activity detected on the network',
                'severity': 'High',
                'recommended_action': 'Investigate the source IP immediately.',
                'ip_addresses': [device['ip'] for device in devices_info],
                'mac_addresses': [device['mac'] for device in devices_info],
                'open_ports': [device['open_ports'] for device in devices_info]
            }
            alerts.append(alert_details)
            self.update_alerts_ui()
            time.sleep(10)

    def show_alert_details(self, event):
        # Get selected alert index
        selected_index = self.alerts_listbox.curselection()
        if not selected_index:
            return

        alert = alerts[selected_index[0]]

        # Create a new window for alert details
        alert_window = Toplevel(self.root)
        alert_window.title("Alert Details")
        alert_window.geometry("400x500")

        # Display alert details
        Label(alert_window, text=f"Timestamp: {alert['timestamp']}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"Description: {alert['description']}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"Severity: {alert['severity']}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"Recommended Action: {alert['recommended_action']}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"IP Addresses Involved: {', '.join(alert['ip_addresses'])}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"MAC Addresses Involved: {', '.join(alert['mac_addresses'])}").pack(anchor="w", padx=10, pady=5)
        Label(alert_window, text=f"Open Ports Involved: {', '.join([str(port) for ports in alert['open_ports'] for port in ports])}").pack(anchor="w", padx=10, pady=5)

if __name__ == '__main__':
    root = tk.Tk()
    app = CyberSecurityApp(root)
    root.mainloop()
