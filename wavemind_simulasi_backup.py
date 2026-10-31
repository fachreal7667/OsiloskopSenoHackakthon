import numpy as np
import matplotlib.pyplot as plt

# Parameter sinyal simulasi
frekuensi = 4      # Frekuensi sinyal dalam Hz
duty_cycle = 25     # Persentase waktu sinyal berada pada kondisi HIGH
durasi = 2          # Lama sinyal yang ditampilkan dalam detik
jumlah_titik = 2000

# Membuat sumbu waktu
waktu = np.linspace(0, durasi, jumlah_titik)

# Menghitung posisi sinyal dalam satu periode
periode = 1 / frekuensi
waktu_high = periode * duty_cycle / 100
waktu_low = periode - waktu_high

print("=== HASIL ANALISIS WAVEMIND AI ===")
print(f"Frekuensi   : {frekuensi} Hz")
print(f"Periode     : {periode:.3f} detik")
print(f"Duty Cycle  : {duty_cycle}%")
print(f"Waktu HIGH  : {waktu_high:.3f} detik")
print(f"Waktu LOW   : {waktu_low:.3f} detik")
print("\n=== PENJELASAN WAVEMIND AI ===")

print(
    f"Sinyal ini berulang sebanyak {frekuensi} kali setiap detik."
)

print(
    f"Satu siklus membutuhkan waktu {periode:.3f} detik."
)

print(
    f"Dalam setiap siklus, sinyal berada pada kondisi HIGH "
    f"selama {duty_cycle}% dari total periode."
)

if duty_cycle == 50:
    print("Sinyal memiliki waktu HIGH dan LOW yang sama.")
elif duty_cycle < 50:
    print("Sinyal memiliki waktu HIGH lebih singkat daripada LOW.")
else:
    print("Sinyal memiliki waktu HIGH lebih lama daripada LOW.")
posisi = (waktu % periode) / periode

# Membuat gelombang kotak
sinyal = (posisi < duty_cycle / 100).astype(int)

# Menampilkan grafik
plt.figure(figsize=(10, 4))
plt.plot(waktu, sinyal)
plt.title("WaveMind AI - Simulasi Gelombang PWM")
plt.xlabel("Waktu (detik)")
plt.ylabel("Tegangan relatif")
plt.ylim(-0.2, 1.2)
plt.grid(True)
plt.tight_layout()
plt.show()