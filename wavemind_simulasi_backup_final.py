import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FixedLocator
import tkinter as tk
from tkinter import messagebox

# Variabel global untuk menyimpan hasil simulasi
hasil = {}

# --- Fungsi simulasi (dihormat dari wavemind_simulasi.py) ---
def run_simulation(frekuensi, duty_cycle, durasi):
    jumlah_titik = 2000
    waktu = np.linspace(0, durasi, jumlah_titik)
    periode = 1 / frekuensi
    waktu_high = periode * duty_cycle / 100
    waktu_low = periode - waktu_high

    posisi = (waktu % periode) / periode
    sinyal = (posisi < duty_cycle / 100).astype(int)

    hasil = {
        "frekuensi": frekuensi,
        "periode": periode,
        "duty_cycle": duty_cycle,
        "waktu_high": waktu_high,
        "waktu_low": waktu_low,
        "sinyal": sinyal,
        "waktu": waktu,
    }
    return hasil


# --- Penjelasan hasil dalam bahasa Indonesia ---
def penjelasan(hasil):
    lines = [
        f"Frekuensi   : {hasil['frekuensi']} Hz",
        f"Periode     : {hasil['periode']:.3f} detik",
        f"Duty Cycle  : {hasil['duty_cycle']}%",
        f"Waktu HIGH  : {hasil['waktu_high']:.3f} detik",
        f"Waktu LOW   : {hasil['waktu_low']:.3f} detik",
    ]
    if hasil["duty_cycle"] == 50:
        lines.append("Sinyal memiliki waktu HIGH dan LOW yang sama.")
    elif hasil["duty_cycle"] < 50:
        lines.append("Sinyal memiliki waktu HIGH lebih singkat daripada LOW.")
    else:
        lines.append("Sinyal memiliki waktu HIGH lebih lama daripada LOW.")
    return "\n".join(lines)


# --- Fungsi callback tombol Generate ---
def on_generate():
    global hasil
    try:
        frekuensi = float(entry_frekuensi.get())
        duty_cycle = float(entry_duty.get())
        durasi = float(entry_durasi.get())
    except ValueError:
        messagebox.showerror("Input Error", "Masukkan angka yang valid.")
        return

    if frekuensi <= 0:
        messagebox.showerror("Input Error", "Frekuensi harus lebih besar dari nol.")
        return
    if not (0 <= duty_cycle <= 100):
        messagebox.showerror("Input Error", "Duty cycle harus antara 0 hingga 100 persen.")
        return

    hasil = run_simulation(frekuensi, duty_cycle, durasi)

    # Update text result
    text_result.config(text=penjelasan(hasil))

    # Update plot with display controls (uses current spinbox values)
    update_plot(durasi)


def auto_scale():
    """Auto scale both axes based on current data and display settings"""
    data = hasil["sinyal"]
    t = hasil["waktu"]
    
    # Dapatkan nilai current dari kontrol Volt/div
    volt_div = float(spin_volt_div.get())
    time_div = float(spin_time_div.get())
    
    # X-axis: auto scale berdasarkan data waktu dengan margin 10%
    t_min, t_max = t.min(), t.max()
    margin_t = (t_max - t_min) * 0.1
    
    # Tetapkan rentang X berdasarkan Time/div tapi bisa di-overide auto scale
    # Gunakan data range dengan margin, tapi pastikan minimal 1 divisi
    x_data_max = max(t_max, time_div * 10)  # minimal time_div * 10
    ax.set_xlim(t_min - margin_t, x_data_max + margin_t)
    
    # Y-axis: auto scale berdasarkan data sinyal dengan margin, 
    t_data_min, t_data_max = data.min(), data.max()
    margin_v = (t_data_max - t_data_min) * 0.1 if t_data_max > t_data_min else 0.1
    
    # Sesuaikan Y axis dengan Volt/div setting namun tetap mencakup data
    # Data sinyal adalah 0-1 relative, jadi pasti mencakup 0 dan 1
    y_data_range = max(t_data_max, volt_div) - min(t_data_min, 0)
    y_center = (max(t_data_min, 0) + min(t_data_max, volt_div)) / 2
    y_half = y_data_range / 2 + margin_v
    
    # Pastikan rentang mencakup 0 dan 1, dan sesuai Volt/div
    ax.set_ylim(0, volt_div)
    
    # Atur tick sesuai range baru
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    
    canvas.draw()


def update_plot(durasi_simulasi):
    """Update plot using time/div and volt/div controls"""
    # Dapatkan nilai dari kontrol tampilan
    time_div = float(spin_time_div.get())
    volt_div = float(spin_volt_div.get())
    
    # Time/div: batas sumbu X = 0 sampai Time/div × 10 (10 divisi horizontal)
    # Contoh: Time/div 0.1 → X 0 sampai 1 detik, Time/div 0.2 → X 0 sampai 2 detik
    x_max = time_div * 10
    
    # Plot data pertamakal tanpa clear dulu untuk melihat data range
    # Lalu atur limit dan gambar ulang
    ax.clear()
    
    # Set x-axis dari 0 sampai x_max SEKARANG SETELAH clear()
    ax.set_xlim(0, x_max)
    
    # Atur tick X sesuai time/div: tampilkan tick setiap 1 divisi
    n_ticks = max(2, min(11, int(x_max / time_div) + 1))  # maksimal 10 tick + 1
    step = x_max / (n_ticks - 1) if x_max > 0 else time_div
    tick_locs = [round(i * step, 2) for i in range(n_ticks)]
    ax.set_xticks(tick_locs)
    ax.set_xticklabels([f'{t:.1f}' for t in tick_locs])
    
    # Volt/div: batas sumbu Y = 0 sampai Volt/div (skala tegangan)
    # Data simulasi relatif 0-1 akan discale matplotlib secara otomatis
    # ketika y-axis limits diubah, sehingga HIGH dan LOW tetap terlihat dengan amplitudo yang sama
    y_max = volt_div
    y_min = 0.0
    ax.set_ylim(y_min, y_max)
    
    # Atur tick Y: sesuai skala volt/div dengan menampilkan 0 dan nilai maksimal
    ax.set_yticks([0, y_max])
    ax.set_yticklabels([f'0', f'{y_max:.1f}'])
    
    # Plot data - data sinyal relatif 0-1 akan discale matplotlib secara otomatis
    # ketika y-axis limits diubah, sehingga HIGH dan LOW tetap terlihat dengan amplitudo yang sama
    ax.plot(hasil["waktu"], hasil["sinyal"])
    ax.set_title("WaveMind AI - Simulasi Gelombang PWM", pad=10)
    ax.set_xlabel("Waktu (detik)")
    ax.set_ylabel("Tegangan relatif")
    fig.tight_layout()
    ax.grid(True)
    canvas.draw()


# --- Window utama Tkinter ---
root = tk.Tk()
root.title("WaveMind AI - Simulasi PWM")
root.geometry("800x600")

# --- Kontrol tampilan osiloskop ---
frame_controls = tk.Frame(root)
frame_controls.pack(pady=5)

tk.Label(frame_controls, text="Time/div (s):").grid(row=0, column=0)
spin_time_div = tk.Spinbox(frame_controls, from_=0.1, to=10, increment=0.1, width=5)
spin_time_div.grid(row=0, column=1)
spin_time_div.delete(0, "end")
spin_time_div.insert(0, "1")

tk.Label(frame_controls, text="Volt/div (V):").grid(row=0, column=2)
spin_volt_div = tk.Spinbox(frame_controls, from_=0.1, to=5, increment=0.1, width=5)
spin_volt_div.grid(row=0, column=3)
spin_volt_div.delete(0, "end")
spin_volt_div.insert(0, "1")

btn_auto_scale = tk.Button(frame_controls, text="Auto Scale", command=auto_scale)
btn_auto_scale.grid(row=0, column=4, padx=5)

# Frame input
frame_input = tk.Frame(root)
frame_input.pack(pady=10)

tk.Label(frame_input, text="Frekuensi (Hz):").grid(row=0, column=0)
entry_frekuensi = tk.Entry(frame_input, width=10)
entry_frekuensi.grid(row=0, column=1)
entry_frekuensi.insert(0, "4")

tk.Label(frame_input, text="Duty Cycle (%):").grid(row=0, column=2)
entry_duty = tk.Entry(frame_input, width=10)
entry_duty.grid(row=0, column=3)
entry_duty.insert(0, "25")

tk.Label(frame_input, text="Durasi (s):").grid(row=0, column=4)
entry_durasi = tk.Entry(frame_input, width=10)
entry_durasi.grid(row=0, column=5)
entry_durasi.insert(0, "2")

btn_generate = tk.Button(frame_input, text="Generate", command=on_generate)
btn_generate.grid(row=0, column=6, padx=5)

# Frame untuk grafik dan hasil
frame_display = tk.Frame(root)
frame_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Matplotlib figure ditanam di dalam Tkinter
fig = plt.Figure(figsize=(8, 4))
ax = fig.add_subplot(111)
ax.plot([], [])
canvas = FigureCanvasTkAgg(fig, master=frame_display)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Text result
text_result = tk.Label(frame_display, text="", justify=tk.LEFT)
text_result.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

# Tombol Generate pertama kali menunjukkan hasil default
on_generate()

# Jalankan aplikasi
root.mainloop()