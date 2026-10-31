import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox, ttk
import serial
import threading
import time
from collections import deque

# --- Variabel Global & Thread Locks ---
hasil = {}
hor_pos = 0.0
ver_pos = 0.0
trig_level = 0.5
adc_reference = 3.3
after_id = None

# Buffer dan Locks untuk keamanan Thread (Mencegah Race Condition)
data_lock_1 = threading.Lock()
sample_timestamps = deque(maxlen=12000)
adc_data = deque(maxlen=12000)
sample_index = deque(maxlen=12000)

data_lock_2 = threading.Lock()
sample_timestamps_2 = deque(maxlen=12000)
adc_data_2 = deque(maxlen=12000)
sample_index_2 = deque(maxlen=12000)

# Tracker Serial
serial_generator = None
serial_generator_lock = threading.Lock()
serial_generator_status = None
esp1_numeric_lines = 0
esp1_last_raw = None
esp1_last_line = ""

def safe_float(widget, default):
    try:
        raw = widget.get().strip()
        if not raw: return float(default)
        value = float(raw)
        return value if np.isfinite(value) else float(default)
    except (ValueError, TypeError, AttributeError):
        return float(default)

def hitung_ukuran_dari_data(hasil):
    if not hasil or "sinyal" not in hasil or "waktu" not in hasil:
        return {"frekuensi_terukur": None, "duty_cycle_terukur": None, "tegangan_peak2peak": None, 
                "tegangan_max": None, "tegangan_min": None, "tegangan_rms": None}

    sinyal_float = hasil["sinyal"].astype(float)
    waktu = hasil["waktu"]
    n = len(sinyal_float)

    periode_terdeteksi = None
    indeks_naik = [i for i in range(1, n) if sinyal_float[i - 1] == 0 and sinyal_float[i] == 1]

    if len(indeks_naik) >= 2:
        dt = waktu[indeks_naik[1]] - waktu[indeks_naik[0]]
        if dt > 0: periode_terdeteksi = dt
    frekuensi_terukur = (1.0 / periode_terdeteksi) if periode_terdeteksi else None

    duty_cycle_terukur = None
    if periode_terdeteksi and len(indeks_naik) > 0:
        total_high = 0
        count = 0
        for idx in indeks_naik[:4]:
            for j in range(idx + 1, n):
                if sinyal_float[j - 1] == 1 and sinyal_float[j] == 0:
                    total_high += (waktu[j] - waktu[idx])
                    count += 1
                    break
            if count >= 4: break
        if count > 0 and periode_terdeteksi > 0:
            duty_cycle_terukur = (total_high / (count * periode_terdeteksi)) * 100

    sinial_shifted = sinyal_float + ver_pos
    tegangan_max = float(sinial_shifted.max()) if len(sinial_shifted) > 0 else None
    tegangan_min = float(sinial_shifted.min()) if len(sinial_shifted) > 0 else None
    tegangan_peak2peak = tegangan_max - tegangan_min if (tegangan_max is not None and tegangan_min is not None) else None
    tegangan_rms = float(np.sqrt(np.mean(sinial_shifted ** 2))) if len(sinial_shifted) > 0 else None

    return {
        "frekuensi_terukur": round(frekuensi_terukur, 2) if frekuensi_terukur else None,
        "duty_cycle_terukur": round(duty_cycle_terukur, 1) if duty_cycle_terukur else None,
        "tegangan_peak2peak": round(tegangan_peak2peak, 2) if tegangan_peak2peak else None,
        "tegangan_max": round(tegangan_max, 2) if tegangan_max else None,
        "tegangan_min": round(tegangan_min, 2) if tegangan_min else None,
        "tegangan_rms": round(tegangan_rms, 3) if tegangan_rms else None,
    }

def run_simulation(frekuensi, duty_cycle, durasi):
    jumlah_titik = 2000
    waktu = np.linspace(0, durasi, jumlah_titik)
    periode = 1 / frekuensi
    waktu_high = periode * duty_cycle / 100
    waktu_low = periode - waktu_high

    posisi = (waktu % periode) / periode
    sinyal = (posisi < duty_cycle / 100).astype(int)

    return {
        "frekuensi": frekuensi, "periode": periode, "duty_cycle": duty_cycle,
        "waktu_high": waktu_high, "waktu_low": waktu_low, "sinyal": sinyal, "waktu": waktu,
    }

def penjelasan(hasil):
    lines = [
        f"Frekuensi   : {hasil['frekuensi']} Hz",
        f"Periode     : {hasil['periode']:.3f} detik",
        f"Duty Cycle  : {hasil['duty_cycle']}%",
        f"Waktu HIGH  : {hasil['waktu_high']:.3f} detik",
        f"Waktu LOW   : {hasil['waktu_low']:.3f} detik",
    ]
    lines.append("Sinyal memiliki waktu HIGH dan LOW yang sama." if hasil["duty_cycle"] == 50 else
                 "Sinyal memiliki waktu HIGH lebih singkat daripada LOW." if hasil["duty_cycle"] < 50 else
                 "Sinyal memiliki waktu HIGH lebih lama daripada LOW.")

    ukuran = hitung_ukuran_dari_data(hasil)
    if ukuran["frekuensi_terukur"]: lines.append(f"Frekuensi terukur: {ukuran['frekuensi_terukur']} Hz")
    if ukuran["duty_cycle_terukur"]: lines.append(f"Duty cycle terukur: {ukuran['duty_cycle_terukur']}%")
    if ukuran["tegangan_peak2peak"]: lines.append(f"Tegangan peak-to-peak: {ukuran['tegangan_peak2peak']} V")
    if ukuran["tegangan_max"]: lines.append(f"Tegangan max: {ukuran['tegangan_max']} V")
    if ukuran["tegangan_min"]: lines.append(f"Tegangan min: {ukuran['tegangan_min']} V")
    if ukuran["tegangan_rms"]: lines.append(f"Tegangan RMS: {ukuran['tegangan_rms']} V")
    return "\n".join(lines)

def toggle_mode():
    pass # Loops dipertahankan, Matplotlib artist akan ditangani fungsi render

def on_generate():
    global hasil
    try:
        frekuensi, duty_cycle, durasi = float(entry_frekuensi.get()), float(entry_duty.get()), float(entry_durasi.get())
        if frekuensi <= 0 or not (0 <= duty_cycle <= 100): raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Parameter tidak valid.")
        return

    hasil = run_simulation(frekuensi, duty_cycle, durasi)
    text_result.config(text=penjelasan(hasil))
    update_plot(durasi)

def auto_scale():
    try:
        active_mode = mode.get()
        if active_mode == "REAL-TIME" and adc_data:
            with data_lock_1: raw = np.asarray(list(adc_data), dtype=float)
            scale_max = max(safe_float(spin_adc_ref, 2.67), 0.001)
            values = (raw / 4095.0) * scale_max
        elif active_mode == "REAL-TIME2" and adc_data_2:
            with data_lock_2: raw = np.asarray(list(adc_data_2), dtype=float)
            scale_max = max(safe_float(spin_adc_ref2, 3.3), 0.001)
            values = (raw / 4095.0) * scale_max
        elif active_mode == "SIMULASI" and hasil and "sinyal" in hasil:
            values = np.asarray(hasil["sinyal"], dtype=float)
        else:
            return messagebox.showinfo("Auto Scale", "Belum ada data cukup.")

        values = values[np.isfinite(values)]
        if values.size < 2: return
        
        span = float(np.max(values)) - float(np.min(values))
        recommended = min(5.0, max(0.1, float(np.ceil(((max((span * 1.25) / 8.0, 0.1)) - 1e-12) / 0.1) * 0.1)))

        spin_volt_div.delete(0, "end")
        spin_volt_div.insert(0, f"{recommended:.1f}")
        
        if active_mode == "SIMULASI": root.after(0, lambda: update_plot(safe_float(entry_durasi, 2.0)))
    except Exception as exc:
        messagebox.showerror("Auto Scale gagal", f"Error:\n{exc}")

# --- Window Utama Tkinter (Tidak Diubah) ---
root = tk.Tk()
root.title("WaveMind AI - Simulasi PWM")
root.geometry("1150x760")

mode = tk.StringVar(master=root, value="SIMULASI")
mode.trace_add("write", lambda *args: toggle_mode())

frame_controls = tk.Frame(root)
frame_controls.pack(pady=5)

# Spinboxes
labels_spins = [("Time/div (s):", "1", 0.1, 10), ("Volt/div (V):", "1", 0.1, 5),
                ("Hor Pos (s):", "0.0", 0.0, 10.0), ("Ver Pos (V):", "0.0", -5.0, 5.0)]
spins = {}
for i, (txt, default, f, t) in enumerate(labels_spins):
    tk.Label(frame_controls, text=txt).grid(row=0, column=i*2)
    sp = tk.Spinbox(frame_controls, from_=f, to=t, increment=0.1 if f>=0 else 0.5, width=5)
    sp.grid(row=0, column=i*2+1)
    sp.delete(0, "end"); sp.insert(0, default)
    spins[txt] = sp

spin_time_div, spin_volt_div, spin_hor_pos, spin_ver_pos = spins.values()

tk.Label(frame_controls, text="Trig Lvl (V):").grid(row=1, column=0)
spin_trig_level = tk.Spinbox(frame_controls, from_=0.0, to=3.3, increment=0.1, width=5)
spin_trig_level.grid(row=1, column=1)
spin_trig_level.delete(0, "end"); spin_trig_level.insert(0, "1.3")

dac_max_var, adc_ref2_var = tk.StringVar(value="2.67"), tk.StringVar(value="3.3")
spin_adc_ref, spin_adc_ref2 = dac_max_var, adc_ref2_var

def open_calibration_window():
    win = tk.Toplevel(root)
    win.title("Kalibrasi")
    win.resizable(False, False)
    frame = tk.Frame(win, padx=14, pady=12)
    frame.pack(fill="both", expand=True)
    tk.Label(frame, text="Kalibrasi tegangan").grid(row=0, column=0, columnspan=2, sticky="w")
    tk.Label(frame, text="DAC Max ESP32 #1 (V):").grid(row=1, column=0, sticky="w")
    tk.Spinbox(frame, from_=0.1, to=5.0, increment=0.01, width=9, textvariable=dac_max_var).grid(row=1, column=1)
    tk.Label(frame, text="ADC Ref ESP32 #2 (V):").grid(row=2, column=0, sticky="w")
    tk.Spinbox(frame, from_=0.1, to=5.0, increment=0.01, width=9, textvariable=adc_ref2_var).grid(row=2, column=1)
    tk.Button(frame, text="Tutup", command=win.destroy).grid(row=4, column=0, columnspan=2, sticky="e")

tk.Button(frame_controls, text="Kalibrasi...", command=open_calibration_window).grid(row=1, column=2, padx=5, pady=5)
tk.Button(frame_controls, text="Auto Scale", command=auto_scale).grid(row=1, column=3, padx=5, pady=5)

tk.Label(frame_controls, text="Mode:").grid(row=1, column=7, sticky='w')
tk.Radiobutton(frame_controls, text="SIMULASI", variable=mode, value="SIMULASI").grid(row=1, column=8, sticky='w')
tk.Radiobutton(frame_controls, text="REAL-TIME ESP32", variable=mode, value="REAL-TIME").grid(row=1, column=9, sticky='w')
tk.Radiobutton(frame_controls, text="REAL-TIME ESP32 #2", variable=mode, value="REAL-TIME2").grid(row=1, column=10, sticky='w')

frame_input = tk.Frame(root)
frame_input.pack(pady=10)
tk.Label(frame_input, text="Frekuensi (Hz):").grid(row=0, column=0)
entry_frekuensi = tk.Entry(frame_input, width=10); entry_frekuensi.grid(row=0, column=1); entry_frekuensi.insert(0, "4")
tk.Label(frame_input, text="Duty Cycle (%):").grid(row=0, column=2)
entry_duty = tk.Entry(frame_input, width=10); entry_duty.grid(row=0, column=3); entry_duty.insert(0, "25")
tk.Label(frame_input, text="Durasi (s):").grid(row=0, column=4)
entry_durasi = tk.Entry(frame_input, width=10); entry_durasi.grid(row=0, column=5); entry_durasi.insert(0, "2")
tk.Button(frame_input, text="Generate", command=on_generate).grid(row=0, column=6, padx=5)

frame_generator = tk.LabelFrame(root, text="Kontrol Function Generator ESP32 #1 (COM7)")
frame_generator.pack(fill=tk.X, padx=10, pady=3)
waveform_choice = ttk.Combobox(frame_generator, state="readonly", width=12, values=("Sinus", "Kotak", "Segitiga"))
waveform_choice.grid(row=0, column=1, padx=4, pady=4); waveform_choice.current(0)
tk.Button(frame_generator, text="Terapkan Gelombang", command=lambda: send_generator_command(
    {"Sinus": "1", "Kotak": "2", "Segitiga": "3"}.get(waveform_choice.get(), "1"))).grid(row=0, column=2, padx=4, pady=4)
frequency_choice = ttk.Combobox(frame_generator, state="readonly", width=8, values=("1 Hz", "2 Hz", "5 Hz", "10 Hz", "20 Hz", "50 Hz", "100 Hz"))
frequency_choice.grid(row=0, column=4, padx=4, pady=4); frequency_choice.current(1)
tk.Button(frame_generator, text="Atur Frekuensi", command=lambda: send_generator_command("F" + frequency_choice.get().split()[0])).grid(row=0, column=5, padx=4, pady=4)
serial_generator_status = tk.Label(frame_generator, text="Status generator: menunggu", anchor="w")
serial_generator_status.grid(row=1, column=0, columnspan=6, sticky="ew", padx=4, pady=2)

frame_display = tk.Frame(root)
frame_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# --- Optimisasi Matplotlib (Blitting Preparation) ---
fig = plt.Figure(figsize=(8, 4))
ax = fig.add_subplot(111)
line_main, = ax.plot([], [], linewidth=1.0)
line_trig = ax.axhline(0, linestyle="--", linewidth=0.8, alpha=0.55)
ax.grid(True, which="major", alpha=0.65)
ax.set_xlabel("Waktu (detik)")
ax.set_ylabel("Tegangan (V)")

canvas = FigureCanvasTkAgg(fig, master=frame_display)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

text_result = tk.Label(frame_display, text="", justify=tk.LEFT)
text_result.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

# --- Pengambilan Data Asinkron ---
def read_esp32():
    global serial_generator, esp1_numeric_lines, esp1_last_raw, esp1_last_line
    while True:
        try:
            with serial_generator_lock: ser, need_open = serial_generator, (serial_generator is None or not serial_generator.is_open)
            if need_open:
                ser = serial.Serial("COM7", 115200, timeout=0.25, write_timeout=1)
                with serial_generator_lock: serial_generator = ser
                time.sleep(2)
                with serial_generator_lock:
                    if serial_generator is ser and ser.is_open: ser.reset_input_buffer()
            with serial_generator_lock: ser = serial_generator
            if ser is None or not ser.is_open: time.sleep(0.05); continue
            
            line = ser.readline()
            if not line: continue
            text_line = line.decode("ascii", errors="ignore").strip().lstrip("\ufeff")
            esp1_last_line = text_line
            candidate = text_line.split(":", 1)[1].strip() if ":" in text_line else text_line
            
            if candidate.isdigit() and 0 <= (val := int(candidate)) <= 4095:
                stamp = time.monotonic()  # Menggunakan monotonic time base
                with data_lock_1:
                    adc_data.append(val)
                    sample_timestamps.append(stamp)
                    sample_index.append(sample_index[-1] + 1 if sample_index else 0)
                esp1_numeric_lines += 1
                esp1_last_raw = val
        except Exception:
            with serial_generator_lock:
                if serial_generator: 
                    try: serial_generator.close() 
                    except: pass
                serial_generator = None
            time.sleep(1)

def send_generator_command(command):
    try:
        with serial_generator_lock:
            if serial_generator and serial_generator.is_open:
                serial_generator.write((command.strip() + "\n").encode("ascii"))
                serial_generator.flush()
    except Exception as exc: messagebox.showerror("Gagal", str(exc))

def read_esp32_2():
    ser = None
    while True:
        try:
            if ser is None or not ser.is_open:
                if ser: 
                    try: ser.close() 
                    except: pass
                ser = serial.Serial("COM8", 115200, timeout=1)
                time.sleep(2); ser.reset_input_buffer()
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            raw_value = line.split(":", 1)[1] if line.startswith("ADC:") else line
            if raw_value.strip().isdigit() and 0 <= (val := int(raw_value.strip())) <= 4095:
                stamp = time.monotonic() # Standardisasi ke monotonic
                with data_lock_2:
                    adc_data_2.append(val)
                    sample_timestamps_2.append(stamp)
                    sample_index_2.append(sample_index_2[-1] + 1 if sample_index_2 else 0)
        except Exception:
            if ser: 
                try: ser.close() 
                except: pass
            ser = None; time.sleep(2)

# --- Optimisasi Rendering (DRY Principle & set_data) ---
def update_plot(durasi_simulasi):
    if mode.get() != "SIMULASI" or not hasil: return
    time_div, volt_div = max(safe_float(spin_time_div, 0.1), 0.001), max(safe_float(spin_volt_div, 0.5), 0.001)
    hor_pos_value, ver_pos_value, trig_level = safe_float(spin_hor_pos, 0.0), safe_float(spin_ver_pos, 0.0), safe_float(spin_trig_level, 0.5)
    
    waktu, sinyal = hasil["waktu"], hasil["sinyal"].astype(float)
    x_span, x_start = time_div * 10.0, max(0.0, hor_pos_value)
    mask = (waktu >= x_start) & (waktu <= x_start + x_span)
    t_view, y_view = waktu[mask] - x_start, sinyal[mask] + ver_pos_value

    line_main.set_data(t_view, y_view)
    line_trig.set_ydata([trig_level + ver_pos_value, trig_level + ver_pos_value])
    
    y_min = 0.5 - 4.0 * volt_div
    ax.set_xlim(0.0, x_span)
    ax.set_ylim(y_min, 0.5 + 4.0 * volt_div)
    ax.set_xticks([i * time_div for i in range(11)])
    ax.set_yticks([y_min + i * volt_div for i in range(9)])
    ax.set_title("WaveMind AI - Simulasi Gelombang PWM")
    canvas.draw_idle()

def render_realtime_plot(data_buffer, time_buffer, lock, scale_widget, title, is_esp1=False):
    with lock: raw_values, ts = list(data_buffer), list(time_buffer)
    n = min(len(raw_values), len(ts))
    
    if n < 2: 
        if is_esp1: serial_generator_status.config(text=f"COM7 menunggu data (sampel: {n})")
        return
        
    raw_values, ts = raw_values[-n:], ts[-n:]
    time_data = [t - ts[0] for t in ts]
    t_latest = time_data[-1]
    
    scale_max = max(safe_float(scale_widget, 2.67 if is_esp1 else 3.3), 0.001)
    voltages = [(v / 4095.0) * scale_max for v in raw_values]
    
    time_div, volt_div = max(safe_float(spin_time_div, 0.1), 0.001), max(safe_float(spin_volt_div, 0.5), 0.001)
    x_span, hor_offset = time_div * 10.0, safe_float(spin_hor_pos, 0.0)
    ver_pos, trig_level = safe_float(spin_ver_pos, 0.0), safe_float(spin_trig_level, 1.3)
    
    window_end = t_latest - max(0.0, hor_offset)
    window_start = window_end - x_span
    
    crossings = [i for i in range(1, n) if voltages[i-1] < trig_level <= voltages[i] and window_start <= time_data[i] <= window_end]
    if crossings and abs(hor_offset) < 1e-12:
        window_start = time_data[crossings[-1]] - 0.20 * x_span
        window_end = window_start + x_span
        
    indices = [i for i, t in enumerate(time_data) if window_start <= t <= window_end]
    if not indices: indices = list(range(max(0, n - min(n, 2000)), n))

    if indices:
        x_plot = [time_data[i] - window_start for i in indices]
        y_plot = [voltages[i] + ver_pos for i in indices]
        line_main.set_data(x_plot, y_plot)
        vmin, vmax = min(y_plot) - ver_pos, max(y_plot) - ver_pos
        
        info_txt = f"Vmin: {vmin:.3f} V | Vmax: {vmax:.3f} V | Vpp: {vmax-vmin:.3f} V\nSampel tertampil: {len(indices)}"
        if is_esp1: info_txt = f"Kode DAC: {raw_values[-1]} | {info_txt}"
        text_result.config(text=info_txt)
        
        if is_esp1: serial_generator_status.config(text=f"COM7 aktif | angka diterima: {esp1_numeric_lines}")
    
    line_trig.set_ydata([trig_level + ver_pos, trig_level + ver_pos])
    y_min = scale_max / 2.0 + ver_pos - 4.0 * volt_div
    
    ax.set_xlim(0.0, x_span)
    ax.set_ylim(y_min, y_min + 8.0 * volt_div)
    ax.set_xticks([i * time_div for i in range(11)])
    ax.set_yticks([y_min + i * volt_div for i in range(9)])
    ax.set_title(title)
    canvas.draw_idle()

def update_realtime_loop():
    current_mode = mode.get()
    if current_mode == "REAL-TIME":
        render_realtime_plot(adc_data, sample_timestamps, data_lock_1, spin_adc_ref, "WaveMind AI - Keluaran DAC ESP32 #1", True)
    elif current_mode == "REAL-TIME2":
        render_realtime_plot(adc_data_2, sample_timestamps_2, data_lock_2, spin_adc_ref2, "WaveMind AI - Sinyal ADC ESP32 #2", False)
    root.after(100, update_realtime_loop)

# --- Eksekusi ---
on_generate()
threading.Thread(target=read_esp32, daemon=True).start()
threading.Thread(target=read_esp32_2, daemon=True).start()
update_realtime_loop()
root.mainloop()