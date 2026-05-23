import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
import threading
import time
import json
import platform
from datetime import datetime
from collections import deque

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except:
    plt = None

APP_NAME = "PULSE MONITOR ULTIMATE"

cpu_data = deque(maxlen=30)
ram_data = deque(maxlen=30)
disk_data = deque(maxlen=30)
net_down_data = deque(maxlen=30)
net_up_data = deque(maxlen=30)

last_net = psutil.net_io_counters()
last_time = time.time()
latest_report = {}


root = tk.Tk()
root.title(APP_NAME)
root.geometry("1400x820")
root.configure(bg="black")


def cyber_label(parent, text, size=12, color="lime"):
    return tk.Label(parent, text=text, fg=color, bg="black", font=("Consolas", size, "bold"))


title = cyber_label(root, APP_NAME, 25, "lime")
title.pack(pady=8)

top = tk.Frame(root, bg="black")
top.pack(fill="x", padx=10)

clock_label = cyber_label(top, "", 12, "cyan")
clock_label.pack(side="left")

health_label = cyber_label(top, "SYSTEM HEALTH: SAFE", 14, "lime")
health_label.pack(side="right")

main = tk.Frame(root, bg="black")
main.pack(fill="both", expand=True, padx=10, pady=5)

left = tk.Frame(main, bg="black")
left.pack(side="left", fill="both", expand=True)

right = tk.Frame(main, bg="#050505", width=360)
right.pack(side="right", fill="y", padx=10)

cards = tk.Frame(left, bg="black")
cards.pack(fill="x")


def make_card(parent, title_text):
    frame = tk.Frame(parent, bg="#080808", bd=2, relief="ridge")
    frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
    tk.Label(frame, text=title_text, fg="cyan", bg="#080808",
             font=("Consolas", 11, "bold")).pack(pady=5)
    value = tk.Label(frame, text="0", fg="lime", bg="#080808",
                     font=("Consolas", 22, "bold"))
    value.pack(pady=8)
    return value


cpu_value = make_card(cards, "CPU")
ram_value = make_card(cards, "RAM")
disk_value = make_card(cards, "DISK")
down_value = make_card(cards, "DOWNLOAD")
up_value = make_card(cards, "UPLOAD")

graph_frame = tk.Frame(left, bg="black")
graph_frame.pack(fill="both", expand=True, pady=5)

if plt:
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.tick_params(colors="white")
    ax.set_title("Live Performance Graph", color="lime")
    ax.set_ylim(0, 100)

    cpu_line, = ax.plot([], [], label="CPU")
    ram_line, = ax.plot([], [], label="RAM")
    disk_line, = ax.plot([], [], label="DISK")

    legend = ax.legend()
    for text in legend.get_texts():
        text.set_color("white")

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
else:
    tk.Label(graph_frame, text="Matplotlib not installed. Graph disabled.",
             fg="red", bg="black", font=("Consolas", 14, "bold")).pack(pady=80)

table_title = cyber_label(left, "TOP RESOURCE PROCESSES", 13, "lime")
table_title.pack(pady=5)

columns = ("Process", "PID", "CPU %", "RAM MB", "Threads", "Status")
tree = ttk.Treeview(left, columns=columns, show="headings", height=8)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=130)

tree.pack(fill="x", pady=5)

terminal_title = cyber_label(left, "LIVE SYSTEM LOGS", 13, "lime")
terminal_title.pack(pady=3)

terminal = tk.Text(left, height=8, bg="black", fg="lime", font=("Consolas", 10))
terminal.pack(fill="x")

tk.Label(right, text="SYSTEM INFORMATION", fg="lime", bg="#050505",
         font=("Consolas", 14, "bold")).pack(pady=12)

system_info = tk.Label(right, text="", fg="white", bg="#050505",
                       justify="left", font=("Consolas", 10))
system_info.pack(padx=10, anchor="w")

tk.Label(right, text="NETWORK STATUS", fg="lime", bg="#050505",
         font=("Consolas", 14, "bold")).pack(pady=12)

network_info = tk.Label(right, text="", fg="cyan", bg="#050505",
                        justify="left", font=("Consolas", 10))
network_info.pack(padx=10, anchor="w")

tk.Label(right, text="ALERT PANEL", fg="lime", bg="#050505",
         font=("Consolas", 14, "bold")).pack(pady=12)

alert_box = tk.Listbox(right, bg="black", fg="red", font=("Consolas", 10), height=10)
alert_box.pack(fill="x", padx=10)


def log(message):
    terminal.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
    terminal.see(tk.END)


def add_alert(message):
    alert_box.insert(0, f"{datetime.now().strftime('%H:%M:%S')} - {message}")
    if alert_box.size() > 12:
        alert_box.delete(12)


def bytes_to_mb(value):
    return round(value / 1024 / 1024, 2)


def update_clock():
    clock_label.config(text=datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))
    root.after(1000, update_clock)


def export_report():
    if not latest_report:
        messagebox.showwarning("Warning", "No report data yet.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON File", "*.json"), ("Text File", "*.txt")]
    )

    if not path:
        return

    try:
        if path.endswith(".json"):
            with open(path, "w", encoding="utf-8") as file:
                json.dump(latest_report, file, indent=4)
        else:
            with open(path, "w", encoding="utf-8") as file:
                for key, value in latest_report.items():
                    file.write(f"{key}: {value}\n")

        log("Performance report exported successfully.")
        messagebox.showinfo("Success", "Report exported.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def kill_selected_process():
    selected = tree.selection()

    if not selected:
        messagebox.showwarning("Warning", "Select a process first.")
        return

    item = tree.item(selected)
    pid = item["values"][1]

    try:
        psutil.Process(pid).terminate()
        log(f"Process terminated: PID {pid}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def monitor():
    global last_net, last_time, latest_report

    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent

            current_net = psutil.net_io_counters()
            current_time = time.time()
            time_diff = current_time - last_time

            down_speed = bytes_to_mb((current_net.bytes_recv - last_net.bytes_recv) / time_diff)
            up_speed = bytes_to_mb((current_net.bytes_sent - last_net.bytes_sent) / time_diff)

            last_net = current_net
            last_time = current_time

            cpu_data.append(cpu)
            ram_data.append(ram)
            disk_data.append(disk)
            net_down_data.append(down_speed)
            net_up_data.append(up_speed)

            processes = []

            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "num_threads", "status"]):
                try:
                    processes.append({
                        "name": proc.info["name"] or "Unknown",
                        "pid": proc.info["pid"],
                        "cpu": proc.info["cpu_percent"],
                        "ram": bytes_to_mb(proc.info["memory_info"].rss),
                        "threads": proc.info["num_threads"],
                        "status": proc.info["status"]
                    })
                except:
                    pass

            processes = sorted(processes, key=lambda x: x["ram"], reverse=True)[:10]

            latest_report = {
                "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "cpu_percent": cpu,
                "ram_percent": ram,
                "disk_percent": disk,
                "download_mb_s": down_speed,
                "upload_mb_s": up_speed,
                "system": platform.system(),
                "computer": platform.node(),
                "processor": platform.processor(),
                "top_processes": processes
            }

            root.after(0, update_ui, cpu, ram, disk, down_speed, up_speed, processes)

        except Exception as e:
            log(f"ERROR: {e}")

        time.sleep(1)


def update_ui(cpu, ram, disk, down_speed, up_speed, processes):
    cpu_value.config(text=f"{cpu}%")
    ram_value.config(text=f"{ram}%")
    disk_value.config(text=f"{disk}%")
    down_value.config(text=f"{down_speed} MB/s")
    up_value.config(text=f"{up_speed} MB/s")

    tree.delete(*tree.get_children())

    for p in processes:
        tree.insert("", tk.END, values=(
            p["name"],
            p["pid"],
            p["cpu"],
            p["ram"],
            p["threads"],
            p["status"]
        ))

    system_info.config(text=f"""
OS        : {platform.system()} {platform.release()}
Computer  : {platform.node()}
Processor : {platform.processor()}
Cores     : {psutil.cpu_count(logical=True)}
Boot Time : {datetime.fromtimestamp(psutil.boot_time()).strftime('%d.%m.%Y %H:%M')}
""")

    network_info.config(text=f"""
Download Speed : {down_speed} MB/s
Upload Speed   : {up_speed} MB/s
Total Sent      : {bytes_to_mb(psutil.net_io_counters().bytes_sent)} MB
Total Received  : {bytes_to_mb(psutil.net_io_counters().bytes_recv)} MB
""")

    if cpu > 90 or ram > 90 or disk > 90:
        health_label.config(text="SYSTEM HEALTH: CRITICAL", fg="red")
        add_alert("Critical resource usage detected.")
    elif cpu > 70 or ram > 75 or disk > 80:
        health_label.config(text="SYSTEM HEALTH: WARNING", fg="orange")
    else:
        health_label.config(text="SYSTEM HEALTH: SAFE", fg="lime")

    if plt:
        x = list(range(len(cpu_data)))
        cpu_line.set_data(x, list(cpu_data))
        ram_line.set_data(x, list(ram_data))
        disk_line.set_data(x, list(disk_data))
        ax.set_xlim(0, max(30, len(cpu_data)))
        canvas.draw_idle()

    log("System scan updated.")


button_frame = tk.Frame(root, bg="black")
button_frame.pack(pady=6)

tk.Button(button_frame, text="EXPORT REPORT", bg="cyan", fg="black",
          font=("Consolas", 11, "bold"), command=export_report).grid(row=0, column=0, padx=10)

tk.Button(button_frame, text="KILL SELECTED PROCESS", bg="red", fg="white",
          font=("Consolas", 11, "bold"), command=kill_selected_process).grid(row=0, column=1, padx=10)

tk.Button(button_frame, text="CLEAR LOGS", bg="lime", fg="black",
          font=("Consolas", 11, "bold"), command=lambda: terminal.delete("1.0", tk.END)).grid(row=0, column=2, padx=10)

update_clock()

thread = threading.Thread(target=monitor, daemon=True)
thread.start()

root.mainloop()