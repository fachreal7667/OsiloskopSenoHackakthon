import serial
import time

ser = serial.Serial("COM7", 115200, timeout=1)
time.sleep(2)

print("WaveMind AI: menerima data dari ESP32...")
print("Tekan Ctrl+C untuk berhenti.\n")

try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line.startswith("ADC:"):
            print(line)
except KeyboardInterrupt:
    print("\nPengujian selesai.")
finally:
    ser.close()
