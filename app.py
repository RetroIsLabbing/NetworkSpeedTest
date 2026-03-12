import customtkinter as ctk
import threading
import requests
import time
import subprocess
import platform
import socket
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FAST_API_URL = "https://api.fast.com/netflix/speedtest/v2?https=true&token=YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm&urlCount=5"

SERVERS = {
    "⚡ Fast.com (Netflix CDN)": {
        "download": "fast",
        "upload": "https://httpbin.org/post"
    },
    "🇬🇧 UK (ThinkBroadband)": {
        "download": "http://ipv4.download.thinkbroadband.com/10MB.zip",
        "upload": "https://httpbin.org/post"
    },
    "🇺🇸 USA (Linode Newark)": {
        "download": "http://speedtest.newark.linode.com/100MB-newark.bin",
        "upload": "https://httpbin.org/post"
    },
    "🇩🇪 Germany (Hetzner)": {
        "download": "http://speed.hetzner.de/10MB.bin",
        "upload": "https://httpbin.org/post"
    },
    "🇸🇬 Singapore (Linode)": {
        "download": "http://speedtest.singapore.linode.com/100MB-singapore.bin",
        "upload": "https://httpbin.org/post"
    },
    "🇿🇦 South Africa (TENET)": {
        "download": "http://speedtest.tenet.ac.za/10mb.tst",
        "upload": "https://httpbin.org/post"
    },
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def get_ip_prefix():
    ip = get_local_ip()
    parts = ip.split(".")
    return ".".join(parts[:3]) + "."

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🌐 Network Toolkit")
        self.geometry("700x800")
        self.resizable(False, False)
        self.history = []
        self.speed_data = {"download": [], "upload": [], "time": []}
        self.alert_threshold = 0

        self.tabview = ctk.CTkTabview(self, width=680, height=760)
        self.tabview.pack(padx=10, pady=10)

        self.tabview.add("⚡ Speed Test")
        self.tabview.add("🔧 Network Tools")
        self.tabview.add("🖥️ Device Scanner")
        self.tabview.add("🌍 My Info")

        self.build_speed_tab()
        self.build_tools_tab()
        self.build_scanner_tab()
        self.build_info_tab()

    # ─────────────────────────────────────────
    # TAB 1: SPEED TEST
    # ─────────────────────────────────────────
    def build_speed_tab(self):
        tab = self.tabview.tab("⚡ Speed Test")

        speed_frame = ctk.CTkFrame(tab)
        speed_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(speed_frame, text="📥 Download", font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=15, pady=8)
        self.download_label = ctk.CTkLabel(speed_frame, text="-- Mbps", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00d4aa")
        self.download_label.grid(row=1, column=0, padx=15, pady=5)

        ctk.CTkLabel(speed_frame, text="📤 Upload", font=ctk.CTkFont(size=13)).grid(row=0, column=1, padx=15, pady=8)
        self.upload_label = ctk.CTkLabel(speed_frame, text="-- Mbps", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00aaff")
        self.upload_label.grid(row=1, column=1, padx=15, pady=5)

        ctk.CTkLabel(speed_frame, text="📶 Ping", font=ctk.CTkFont(size=13)).grid(row=0, column=2, padx=15, pady=8)
        self.ping_label = ctk.CTkLabel(speed_frame, text="-- ms", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffaa00")
        self.ping_label.grid(row=1, column=2, padx=15, pady=5)

        speed_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Server selector
        server_frame = ctk.CTkFrame(tab, fg_color="transparent")
        server_frame.pack(pady=5)
        ctk.CTkLabel(server_frame, text="🌍 Test Server:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.server_var = ctk.StringVar(value=list(SERVERS.keys())[0])
        ctk.CTkOptionMenu(
            server_frame,
            values=list(SERVERS.keys()),
            variable=self.server_var,
            width=280
        ).pack(side="left")

        # Progress bar
        self.progress = ctk.CTkProgressBar(tab, width=620)
        self.progress.pack(pady=8)
        self.progress.set(0)

        # Status
        self.status_label = ctk.CTkLabel(tab, text="Press Start to begin test", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=3)

        # Alert threshold
        alert_frame = ctk.CTkFrame(tab, fg_color="transparent")
        alert_frame.pack(pady=5)
        ctk.CTkLabel(alert_frame, text="🔔 Alert if download below (Mbps):", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.alert_entry = ctk.CTkEntry(alert_frame, width=70, placeholder_text="0")
        self.alert_entry.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=8)

        self.start_button = ctk.CTkButton(
            btn_frame, text="▶ Start Test",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=160,
            command=self.start_speed_test
        )
        self.start_button.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="📋 Copy Results",
            font=ctk.CTkFont(size=13), height=45, width=140,
            fg_color="#333", hover_color="#555",
            command=self.copy_results
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="💾 Export CSV",
            font=ctk.CTkFont(size=13), height=45, width=140,
            fg_color="#333", hover_color="#555",
            command=self.export_csv
        ).pack(side="left", padx=5)

        # Speed graph
        self.fig, self.ax = plt.subplots(figsize=(6, 2.0), facecolor="#2b2b2b")
        self.ax.set_facecolor("#1a1a2e")
        self.ax.tick_params(colors="white")
        self.ax.set_title("Speed History", color="white", fontsize=10)
        self.ax.set_ylabel("Mbps", color="white", fontsize=9)
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#444")
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab)
        self.canvas.get_tk_widget().pack(pady=5)

        # History
        ctk.CTkLabel(tab, text="📋 History", font=ctk.CTkFont(size=13, weight="bold")).pack()
        self.history_box = ctk.CTkTextbox(tab, height=90, width=640)
        self.history_box.pack(padx=10, pady=5)
        self.history_box.insert("end", "No tests run yet.\n")
        self.history_box.configure(state="disabled")

    # ─────────────────────────────────────────
    # TAB 2: NETWORK TOOLS
    # ─────────────────────────────────────────
    def build_tools_tab(self):
        tab = self.tabview.tab("🔧 Network Tools")

        ctk.CTkLabel(tab, text="🎯 Custom Ping", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ping_frame = ctk.CTkFrame(tab, fg_color="transparent")
        ping_frame.pack()
        self.custom_ping_entry = ctk.CTkEntry(ping_frame, placeholder_text="Host or IP (e.g. google.com)", width=320, height=38)
        self.custom_ping_entry.pack(side="left", padx=5)
        self.ping_btn = ctk.CTkButton(ping_frame, text="Ping", width=100, height=38, command=self.start_custom_ping)
        self.ping_btn.pack(side="left")

        ping_result_frame = ctk.CTkFrame(tab)
        ping_result_frame.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(ping_result_frame, text="Min", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, padx=30)
        ctk.CTkLabel(ping_result_frame, text="Avg", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=1, padx=30)
        ctk.CTkLabel(ping_result_frame, text="Max", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=2, padx=30)
        self.ping_min = ctk.CTkLabel(ping_result_frame, text="-- ms", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00d4aa")
        self.ping_min.grid(row=1, column=0, padx=30)
        self.ping_avg = ctk.CTkLabel(ping_result_frame, text="-- ms", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffaa00")
        self.ping_avg.grid(row=1, column=1, padx=30)
        self.ping_max = ctk.CTkLabel(ping_result_frame, text="-- ms", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ff4444")
        self.ping_max.grid(row=1, column=2, padx=30)
        ping_result_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.ping_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self.ping_status.pack()

        ctk.CTkLabel(tab, text="─" * 80, text_color="gray").pack(pady=5)

        ctk.CTkLabel(tab, text="🛤️ Traceroute", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(5, 3))
        trace_frame = ctk.CTkFrame(tab, fg_color="transparent")
        trace_frame.pack()
        self.trace_entry = ctk.CTkEntry(trace_frame, placeholder_text="Host or IP", width=320, height=38)
        self.trace_entry.pack(side="left", padx=5)
        self.trace_btn = ctk.CTkButton(trace_frame, text="Trace", width=100, height=38, command=self.start_traceroute)
        self.trace_btn.pack(side="left")
        self.trace_box = ctk.CTkTextbox(tab, height=100, width=620)
        self.trace_box.pack(pady=5)
        self.trace_box.configure(state="disabled")

        ctk.CTkLabel(tab, text="─" * 80, text_color="gray").pack(pady=5)

        bottom_frame = ctk.CTkFrame(tab, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10)

        dns_frame = ctk.CTkFrame(bottom_frame)
        dns_frame.pack(side="left", padx=5, fill="both", expand=True)
        ctk.CTkLabel(dns_frame, text="🔍 DNS Lookup", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=8)
        self.dns_entry = ctk.CTkEntry(dns_frame, placeholder_text="Domain name", width=180, height=35)
        self.dns_entry.pack(pady=3)
        ctk.CTkButton(dns_frame, text="Lookup", height=35, command=self.dns_lookup).pack(pady=3)
        self.dns_result = ctk.CTkLabel(dns_frame, text="", font=ctk.CTkFont(size=12), text_color="#00d4aa", wraplength=200)
        self.dns_result.pack(pady=5)

        port_frame = ctk.CTkFrame(bottom_frame)
        port_frame.pack(side="left", padx=5, fill="both", expand=True)
        ctk.CTkLabel(port_frame, text="🔌 Port Checker", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=8)
        self.port_host_entry = ctk.CTkEntry(port_frame, placeholder_text="Host or IP", width=180, height=35)
        self.port_host_entry.pack(pady=3)
        self.port_entry = ctk.CTkEntry(port_frame, placeholder_text="Port number", width=180, height=35)
        self.port_entry.pack(pady=3)
        ctk.CTkButton(port_frame, text="Check Port", height=35, command=self.check_port).pack(pady=3)
        self.port_result = ctk.CTkLabel(port_frame, text="", font=ctk.CTkFont(size=12), wraplength=200)
        self.port_result.pack(pady=5)

    # ─────────────────────────────────────────
    # TAB 3: DEVICE SCANNER
    # ─────────────────────────────────────────
    def build_scanner_tab(self):
        tab = self.tabview.tab("🖥️ Device Scanner")

        ctk.CTkLabel(tab, text="🖥️ Devices on Your Network", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        ctk.CTkLabel(tab, text=f"Scanning range: {get_ip_prefix()}1 - 254", font=ctk.CTkFont(size=12), text_color="gray").pack()

        self.scan_btn = ctk.CTkButton(tab, text="🔍 Scan Network", height=45, width=180,
                                       font=ctk.CTkFont(size=14, weight="bold"), command=self.start_scan)
        self.scan_btn.pack(pady=10)

        self.scan_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.scan_status.pack()

        self.scan_progress = ctk.CTkProgressBar(tab, width=600)
        self.scan_progress.pack(pady=5)
        self.scan_progress.set(0)

        self.devices_box = ctk.CTkTextbox(tab, height=480, width=640, font=ctk.CTkFont(family="Courier", size=12))
        self.devices_box.pack(padx=10, pady=5)
        self.devices_box.insert("end", "Press 'Scan Network' to discover devices.\n")
        self.devices_box.configure(state="disabled")

    # ─────────────────────────────────────────
    # TAB 4: MY INFO
    # ─────────────────────────────────────────
    def build_info_tab(self):
        tab = self.tabview.tab("🌍 My Info")

        ctk.CTkLabel(tab, text="🌍 Your Network Info", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

        self.info_frame = ctk.CTkFrame(tab)
        self.info_frame.pack(padx=20, pady=10, fill="x")

        self.info_labels = {}
        fields = ["Local IP", "Hostname", "Public IP", "ISP", "City", "Region", "Country", "Timezone"]
        for i, field in enumerate(fields):
            ctk.CTkLabel(self.info_frame, text=f"{field}:", font=ctk.CTkFont(size=13), text_color="gray").grid(row=i, column=0, sticky="w", padx=20, pady=6)
            lbl = ctk.CTkLabel(self.info_frame, text="--", font=ctk.CTkFont(size=13, weight="bold"))
            lbl.grid(row=i, column=1, sticky="w", padx=20, pady=6)
            self.info_labels[field] = lbl

        self.info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(tab, text="🔄 Refresh Info", height=40, width=160, command=self.load_info).pack(pady=15)
        self.load_info()

    # ─────────────────────────────────────────
    # SPEED TEST LOGIC
    # ─────────────────────────────────────────
    def start_speed_test(self):
        self.start_button.configure(state="disabled", text="Testing...")
        self.download_label.configure(text="-- Mbps", text_color="#00d4aa")
        self.upload_label.configure(text="-- Mbps", text_color="#00aaff")
        self.ping_label.configure(text="-- ms", text_color="#ffaa00")
        self.progress.set(0)
        try:
            self.alert_threshold = float(self.alert_entry.get())
        except:
            self.alert_threshold = 0
        threading.Thread(target=self.run_speed_test, daemon=True).start()

    def run_speed_test(self):
        try:
            self.status_label.configure(text="📶 Testing ping...")
            self.progress.set(0.1)
            ping = self.measure_ping("https://www.google.com")
            self.ping_label.configure(text=f"{ping:.0f} ms")
            self.progress.set(0.2)

            self.status_label.configure(text="📥 Testing download...")
            download = self.measure_download()
            color = "#00d4aa" if download > 10 else "#ffaa00" if download > 3 else "#ff4444"
            self.download_label.configure(text=f"{download:.1f} Mbps", text_color=color)
            self.progress.set(0.6)

            self.status_label.configure(text="📤 Testing upload...")
            upload = self.measure_upload()
            color = "#00d4aa" if upload > 5 else "#ffaa00" if upload > 1 else "#ff4444"
            self.upload_label.configure(text=f"{upload:.1f} Mbps", text_color=color)
            self.progress.set(1.0)

            self.status_label.configure(text="✅ Test complete!")
            self.add_history(download, upload, ping)
            self.update_graph(download, upload)

            if self.alert_threshold > 0 and download < self.alert_threshold:
                messagebox.showwarning("⚠️ Speed Alert", f"Download speed ({download:.1f} Mbps) is below your threshold ({self.alert_threshold} Mbps)!")

        except Exception as e:
            self.status_label.configure(text=f"❌ Error: {str(e)}")
            self.progress.set(0)
        finally:
            self.start_button.configure(state="normal", text="▶ Start Test")

    def measure_ping(self, url):
        times = []
        for _ in range(5):
            start = time.time()
            requests.get(url, timeout=5)
            times.append((time.time() - start) * 1000)
        return sum(times) / len(times)

    def get_fast_urls(self):
        response = requests.get(FAST_API_URL, timeout=10)
        data = response.json()
        return [target["url"] for target in data["targets"]]

    def measure_download(self):
        server = self.server_var.get()

        if SERVERS[server]["download"] == "fast":
            # Use Fast.com Netflix CDN
            self.status_label.configure(text="📥 Fetching Fast.com servers...")
            urls = self.get_fast_urls()
            total_bytes = 0
            start = time.time()
            for url in urls:
                try:
                    response = requests.get(url, stream=True, timeout=15)
                    for chunk in response.iter_content(chunk_size=8192):
                        total_bytes += len(chunk)
                except:
                    continue
            elapsed = time.time() - start
            if elapsed == 0 or total_bytes == 0:
                raise Exception("Fast.com download failed")
            return (total_bytes * 8) / (elapsed * 1_000_000)
        else:
            url = SERVERS[server]["download"]
            start = time.time()
            response = requests.get(url, stream=True, timeout=30)
            total = sum(len(chunk) for chunk in response.iter_content(chunk_size=8192))
            return (total * 8) / ((time.time() - start) * 1_000_000)

    def measure_upload(self):
        upload_urls = [
            SERVERS[self.server_var.get()]["upload"],
            "https://httpbin.org/post",
            "https://postman-echo.com/post",
        ]
        data = b"x" * 2 * 1024 * 1024  # 2MB

        for url in upload_urls:
            try:
                start = time.time()
                requests.post(url, data=data, timeout=20)
                elapsed = time.time() - start
                return (len(data) * 8) / (elapsed * 1_000_000)
            except:
                continue

        raise Exception("All upload servers failed. Check your connection.")

    def update_graph(self, download, upload):
        self.speed_data["download"].append(download)
        self.speed_data["upload"].append(upload)
        self.speed_data["time"].append(datetime.now().strftime("%H:%M:%S"))

        self.ax.clear()
        self.ax.set_facecolor("#1a1a2e")
        self.ax.tick_params(colors="white", labelsize=8)
        self.ax.set_title("Speed History", color="white", fontsize=10)
        self.ax.set_ylabel("Mbps", color="white", fontsize=9)
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#444")

        x = range(len(self.speed_data["download"]))
        self.ax.plot(x, self.speed_data["download"], color="#00d4aa", marker="o", label="Download")
        self.ax.plot(x, self.speed_data["upload"], color="#00aaff", marker="o", label="Upload")
        self.ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=8)
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.speed_data["time"], rotation=30, fontsize=7)
        self.fig.tight_layout()
        self.canvas.draw()

    def add_history(self, download, upload, ping):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.append({"time": timestamp, "download": download, "upload": upload, "ping": ping})
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        for item in reversed(self.history):
            self.history_box.insert("end", f"[{item['time']}]  ↓ {item['download']:.1f} Mbps  ↑ {item['upload']:.1f} Mbps  ping {item['ping']:.0f} ms\n")
        self.history_box.configure(state="disabled")

    def copy_results(self):
        dl = self.download_label.cget("text")
        ul = self.upload_label.cget("text")
        ping = self.ping_label.cget("text")
        text = f"Download: {dl} | Upload: {ul} | Ping: {ping}"
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied!", f"Results copied to clipboard:\n{text}")

    def export_csv(self):
        if not self.history:
            messagebox.showwarning("No Data", "Run a speed test first!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["time", "download", "upload", "ping"])
                writer.writeheader()
                writer.writerows(self.history)
            messagebox.showinfo("Exported!", f"Results saved to:\n{path}")

    # ─────────────────────────────────────────
    # NETWORK TOOLS LOGIC
    # ─────────────────────────────────────────
    def start_custom_ping(self):
        host = self.custom_ping_entry.get().strip()
        if not host:
            self.ping_status.configure(text="⚠️ Enter a host or IP", text_color="#ffaa00")
            return
        self.ping_btn.configure(state="disabled", text="Pinging...")
        self.ping_min.configure(text="-- ms")
        self.ping_avg.configure(text="-- ms")
        self.ping_max.configure(text="-- ms")
        self.ping_status.configure(text=f"Pinging {host}...", text_color="gray")
        threading.Thread(target=self.run_custom_ping, args=(host,), daemon=True).start()

    def run_custom_ping(self, host):
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            result = subprocess.run(["ping", param, "10", host], capture_output=True, text=True, timeout=30)
            times = []
            for line in result.stdout.splitlines():
                line = line.lower()
                if "time=" in line:
                    try:
                        t = line.split("time=")[1].split("ms")[0].strip()
                        times.append(float(t))
                    except:
                        pass
                elif "time<" in line:
                    times.append(1.0)

            if times:
                self.ping_min.configure(text=f"{min(times):.1f} ms")
                self.ping_avg.configure(text=f"{sum(times)/len(times):.1f} ms")
                self.ping_max.configure(text=f"{max(times):.1f} ms")
                self.ping_status.configure(text=f"✅ {len(times)} replies from {host}", text_color="#00d4aa")
            else:
                self.ping_status.configure(text=f"❌ No response from {host}", text_color="#ff4444")
        except Exception as e:
            self.ping_status.configure(text=f"❌ Error: {str(e)}", text_color="#ff4444")
        finally:
            self.ping_btn.configure(state="normal", text="Ping")

    def start_traceroute(self):
        host = self.trace_entry.get().strip()
        if not host:
            return
        self.trace_btn.configure(state="disabled", text="Tracing...")
        self.trace_box.configure(state="normal")
        self.trace_box.delete("1.0", "end")
        self.trace_box.insert("end", f"Tracing route to {host}...\n")
        self.trace_box.configure(state="disabled")
        threading.Thread(target=self.run_traceroute, args=(host,), daemon=True).start()

    def run_traceroute(self, host):
        try:
            cmd = ["tracert", host] if platform.system().lower() == "windows" else ["traceroute", host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.trace_box.configure(state="normal")
            self.trace_box.delete("1.0", "end")
            self.trace_box.insert("end", result.stdout)
            self.trace_box.configure(state="disabled")
        except Exception as e:
            self.trace_box.configure(state="normal")
            self.trace_box.insert("end", f"\n❌ Error: {str(e)}")
            self.trace_box.configure(state="disabled")
        finally:
            self.trace_btn.configure(state="normal", text="Trace")

    def dns_lookup(self):
        domain = self.dns_entry.get().strip()
        if not domain:
            return
        try:
            ip = socket.gethostbyname(domain)
            self.dns_result.configure(text=f"✅ {domain}\n→ {ip}", text_color="#00d4aa")
        except Exception as e:
            self.dns_result.configure(text=f"❌ {str(e)}", text_color="#ff4444")

    def check_port(self):
        host = self.port_host_entry.get().strip()
        port_str = self.port_entry.get().strip()
        if not host or not port_str:
            return
        try:
            port = int(port_str)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                self.port_result.configure(text=f"✅ Port {port} is OPEN on {host}", text_color="#00d4aa")
            else:
                self.port_result.configure(text=f"❌ Port {port} is CLOSED on {host}", text_color="#ff4444")
        except Exception as e:
            self.port_result.configure(text=f"❌ Error: {str(e)}", text_color="#ff4444")

    # ─────────────────────────────────────────
    # DEVICE SCANNER LOGIC
    # ─────────────────────────────────────────
    def start_scan(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.scan_progress.set(0)
        self.devices_box.configure(state="normal")
        self.devices_box.delete("1.0", "end")
        self.devices_box.insert("end", "Scanning network...\n\n")
        self.devices_box.configure(state="disabled")
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        prefix = get_ip_prefix()
        devices = []
        total = 254

        for i in range(1, total + 1):
            ip = f"{prefix}{i}"
            self.scan_progress.set(i / total)
            self.scan_status.configure(text=f"Scanning {ip}...")
            try:
                param = "-n" if platform.system().lower() == "windows" else "-c"
                ping = subprocess.run(
                    ["ping", param, "1", "-w", "300", ip],
                    capture_output=True, timeout=1
                )
                if ping.returncode == 0:
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = "Unknown"
                    devices.append((ip, hostname, "🟢 Online"))
            except:
                pass

        self.devices_box.configure(state="normal")
        self.devices_box.delete("1.0", "end")

        if devices:
            self.devices_box.insert("end", f"{'IP Address':<18} {'Hostname':<35} {'Status'}\n")
            self.devices_box.insert("end", "─" * 70 + "\n")
            for ip, hostname, status in devices:
                self.devices_box.insert("end", f"{ip:<18} {hostname:<35} {status}\n")
            self.devices_box.insert("end", f"\n✅ Found {len(devices)} device(s)\n")
        else:
            self.devices_box.insert("end", "❌ No devices found on the network.\n")

        self.devices_box.configure(state="disabled")
        self.scan_status.configure(text=f"✅ Scan complete — {len(devices)} device(s) found")
        self.scan_progress.set(1.0)
        self.scan_btn.configure(state="normal", text="🔍 Scan Network")

    # ─────────────────────────────────────────
    # MY INFO LOGIC
    # ─────────────────────────────────────────
    def load_info(self):
        threading.Thread(target=self.fetch_info, daemon=True).start()

    def fetch_info(self):
        try:
            self.info_labels["Local IP"].configure(text=get_local_ip())
            self.info_labels["Hostname"].configure(text=socket.gethostname())
            data = requests.get("https://ipinfo.io/json", timeout=5).json()
            self.info_labels["Public IP"].configure(text=data.get("ip", "--"))
            self.info_labels["ISP"].configure(text=data.get("org", "--"))
            self.info_labels["City"].configure(text=data.get("city", "--"))
            self.info_labels["Region"].configure(text=data.get("region", "--"))
            self.info_labels["Country"].configure(text=data.get("country", "--"))
            self.info_labels["Timezone"].configure(text=data.get("timezone", "--"))
        except Exception as e:
            self.info_labels["Public IP"].configure(text=f"Error: {str(e)}")

    # ─────────────────────────────────────────
    # CLEAN SHUTDOWN
    # ─────────────────────────────────────────
    def on_close(self):
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()