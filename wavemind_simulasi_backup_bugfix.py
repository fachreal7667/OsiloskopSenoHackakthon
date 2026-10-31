import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FixedLocator
import tkinter as tk
from tkinter import messagebox

# Variabel global untuk menyimpan hasil simulasi
hasil = {}

# Variabel kontrol tampilan tambahan
hor_pos = 0.0  # Horizontal position in seconds (default 0)
ver_pos = 0.0  # Vertical position in volts (default 0)
trig_level = 0.5  # Trigger level in volts (default 0.5)

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
    
    # Dapatkan nilai current dari kontrol Volt/div dan Time/div
    volt_div = float(spin_volt_div.get())
    time_div = float(spin_time_div.get())
    
    # X-axis: auto scale berdasarkan data waktu dengan margin 10%
    # Minimum range adalah Time/div × 10 divisi horizontal
    t_min, t_max = t.min(), t.max()
    margin_t = (t_max - t_min) * 0.1
    x_data_max = max(t_max, time_div * 10)  # minimal time_div * 10
    ax.set_xlim(t_min - margin_t, x_data_max + margin_t)
    
    # Y-axis: auto scale berdasarkan data sinyal dengan margin 10%
    # Tapi tetap menghormati batas Volt/div × 8 divisi vertikal
    data_max = max(data.max(), 1.0)  # minimal 1V untuk sinyal 0-1
    data_min = min(data.min(), 0.0)
    y_range = data_max - data_min
    margin_v = y_range * 0.1 if y_range > 0 else 0.1
    
    # Batas Y: 0 sampai Volt/div × 8 divisi, tetapi bisa di-overide oleh range data
    # jika data melebihi batas standar
    y_standard_max = volt_div * 8
    y_standard_min = 0.0
    
    # Gunakan range yang mencakup data jika data melebihi standar,
    # seangkan standar jika data dalam batas standar
    if data_max > y_standard_max or data_min < y_standard_min:
        # Data melebihi standar, auto scale total
        ax.set_ylim(data_min - margin_v, data_max + margin_v)
    else:
        # Data dalam standar, gunakan batas Volt/div × 8
        ax.set_ylim(y_standard_min, y_standard_max)
    
    # Atur tick sesuai range baru
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    
    canvas.draw()


def update_plot(durasi_simulasi):
    """Update plot using time/div, volt/div, and position controls - oscilloscope style"""
    # Dapatkan nilai dari kontrol tampilan
    time_div = float(spin_time_div.get())
    volt_div = float(spin_volt_div.get())
    hor_pos = float(spin_hor_pos.get())
    ver_pos = float(spin_ver_pos.get())
    trig_level = float(spin_trig_level.get())
    
    # === Time/div: skala waktu per divisi horizontal ===
    # Grafik menampilkan 10 divisi horizontal
    # Rentang waktu total = Time/div × 10 divisi
    # Contoh: Time/div 0.1 → X 0 sampai 1 detik, Time/div 0.2 → X 0 sampai 2 detik
    num_horizontal_divisions = 10
    x_max = time_div * num_horizontal_divisions
    
    # Terapkan Horizontal Position: geser rentang waktu yang ditampilkan
    # hor_pos dalam satuan detik, geser mulai dari posisi tersebut
    x_start = hor_pos
    x_end = hor_pos + x_max
    
    # Hitung indeks data yang sesuai dengan rentang x_start ke x_end
    # data waktu: 0 sampai durasi_simulasi
    n_titik = len(hasil["waktu"])
    # Normalisasi rentang ke domain data 0..n_titik
    idx_start = max(0, min(n_titik - 1, int(n_titik * (x_start / durasi_simulasi) if durasi_simulasi > 0 else 0)))
    idx_end = max(1, min(n_titik, int(n_titik * (x_end / durasi_simulasi) if durasi_simulasi > 0 else n_titik)))
    
    # Ambil subset data untuk ditampilkan - PAKAI YANG SAMA UNTUK KETIGA
    waktu_tampil = hasil["waktu"][idx_start:idx_end]
    sinyal_asli = hasil["sinyal"][idx_start:idx_end]
    
    # Terapkan Vertical Position: geser amplitudo sinyal
    # ver_pos dalam satuan volt, ditambah ke data sinyal float
    sinyal_float = sinyal_asli.astype(float) + ver_pos
    
    # Terapkan Trigger Level: tentukan titik awal berdasarkan persilangan level naik
    # Cari indeks pertama di mana sinyal naik melalui trig_level (dari data sudah di-shift vertikal)
    idx_trigger = 0
    for i in range(1, len(sinyal_float)):
        if sinyal_float[i-1] < trig_level and sinyal_float[i] >= trig_level:
            idx_trigger = i
            break
    
    # Jika ada persilangan naik, geser start index ke sana
    # Tapi pastikan tetap memiliki data yang cukup dan dalam bounds
    if idx_trigger > 0:
        geser = idx_trigger
        # Pastikan tidak melewati batas akhir
        if idx_start + geser < n_titik - 1:
            idx_start_baru = idx_start + geser
            # Sesuaikan end index agar panjang tetap sesuai
            panjang_diperlukan = idx_end - idx_start
            idx_end_baru = min(n_titik, idx_start_baru + panjang_diperlukan)
            
            # Slice ulang dengan indeks baru
            waktu_tampil = hasil["waktu"][idx_start_baru:idx_end_baru]
            # Adjust sinyal_float positions relative to new start
            offset = idx_start_baru - idx_start
            sinyal_float = sinyal_float[offset:offset + (idx_end_baru - idx_start_baru)]
    
    # === Time/div: skala waktu per divisi horizontal ===
    # Grafik menampilkan 10 divisi horizontal
    
    # Clear axes and set up plot
    ax.clear()
    
    # Set x-axis berdasarkan rentang waktu yang telah di-shift
    ax.set_xlim(x_start, x_end)
    
    # Atur tick X sesuai time/div: tampilkan tick setiap 1 divisi
    xtick_vals = [i * time_div for i in range(num_horizontal_divisions + 1)]
    ax.set_xticks(xtick_vals)
    ax.set_xticklabels([f'{t:.1f}' for t in xtick_vals])
    
    # === Volt/div: skala tegangan per divisi vertikal ===
    # Grafik menampilkan 8 divisi vertikal
    # Rentang tegangan total = Volt/div × 8 divisi
    # Contoh: Volt/div 1 → Y 0 sampai 8V, Volt/div 0.5 → Y 0 sampai 4V
    # Sinyal PWM memiliki amplitudo FIXED 0-1V, tampilkan dalam rentang ini
    # Jika Volt/div terlalu kecil, sinyal HIGH akan keluar dari atas grafik (behavior osiloskop)
    num_vertical_divisions = 8
    y_max = volt_div * num_vertical_divisions
    y_min = 0.0
    
    # Atur y-axis: kisaran tetap 0 sampai y_max, tetapi data sekarang sudah
    # memiliki offset vertikal ver_pos
    ax.set_ylim(y_min, y_max)
    
    # Atur tick Y: tampilkan nilai volt setiap 1 divisi
    # Tick values: 0, Volt/div, 2×Volt/div, ..., 8×Volt/div
    ytick_vals = [i * volt_div for i in range(num_vertical_divisions + 1)]
    ax.set_yticks(ytick_vals)
    ax.set_yticklabels([f'{v:.1f}' for v in ytick_vals])
    
    # Plot data - data sinyal telah di-shift vertikal dan dipotong sesuai waktu
    # serta di-trigger sesuai trig_level jika ditemukan
    ax.plot(waktu_tampil, sinyal_float)
    ax.set_title("WaveMind AI - Simulasi Gelombang PWM", pad=10)
    ax.set_xlabel("Waktu (detik)")
    ax.set_ylabel("Tegangan (V)")
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

tk.Label(frame_controls, text="Hor Pos (s):").grid(row=0, column=4)
spin_hor_pos = tk.Spinbox(frame_controls, from_=-10.0, to=10.0, increment=0.5, width=5)
spin_hor_pos.grid(row=0, column=5)
spin_hor_pos.delete(0, "end")
spin_hor_pos.insert(0, "0.0")

tk.Label(frame_controls, text="Ver Pos (V):").grid(row=0, column=6)
spin_ver_pos = tk.Spinbox(frame_controls, from_=-5.0, to=5.0, increment=0.5, width=5)
spin_ver_pos.grid(row=0, column=7)
spin_ver_pos.delete(0, "end")
spin_ver_pos.insert(0, "0.0")

tk.Label(frame_controls, text="Trig Lvl (V):").grid(row=1, column=0)
spin_trig_level = tk.Spinbox(frame_controls, from_=0.0, to=1.0, increment=0.1, width=5)
spin_trig_level.grid(row=1, column=1)
spin_trig_level.delete(0, "end")
spin_trig_level.insert(0, "0.5")

btn_auto_scale = tk.Button(frame_controls, text="Auto Scale", command=auto_scale)
btn_auto_scale.grid(row=1, column=2, padx=5, pady=5)

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
