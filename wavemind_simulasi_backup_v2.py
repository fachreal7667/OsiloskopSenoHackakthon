import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FixedLocator
import tkinter as tk
from tkinter import messagebox

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

    # Update plot
    ax.clear()
    ax.set_xlim(0, durasi)
    ax.set_ylim(0, 1)

    # X-axis: ticks at regular intervals based on durasi
    n_ticks = 5
    step = durasi / (n_ticks - 1) if durasi > 0 else 1
    tick_locs = [round(i * step, 3) for i in range(n_ticks)]
    ax.set_xticks(tick_locs)
    ax.set_xticklabels([f'{t:.1f}' for t in tick_locs])

    # Y-axis: only 0 and 1
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['0', '1'])

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