import nidaqmx
from nidaqmx.constants import TerminalConfiguration, LineGrouping
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv
from datetime import datetime

# ----- Konfiguration -----
AI_CHANNEL      = "Dev1/ai0"
DO_CHANNEL      = "Dev1/port0/line0:2"   # p0.0=ROT, p0.1=GELB, p0.2=GRÜN
INTERVAL_MS     = 10
N_SAMPLES       = 200
RSE             = TerminalConfiguration.RSE
CSV_DATEI       = "messdaten.csv"

EMPFINDLICHKEIT = 0.005
OFFSET_V        = 1.25

# ----- LED-Zustände -----
ROT   = [True,  False, False]
GELB  = [False, True,  False]
GRUEN = [False, False, True ]
AUS   = [False, False, False]

# ----- CSV vorbereiten -----
csv_file   = open(CSV_DATEI, "w", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file, delimiter=";")
csv_writer.writerow(["Zeit", "Temperatur in °C", "Temperatur in °F",
                     "Temperatur in K", "Gemessene Spannung in V"])
print(f"CSV geöffnet: {CSV_DATEI}")

# ----- DAQmx Tasks -----
ai_task = nidaqmx.Task()
ai_task.ai_channels.add_ai_voltage_chan(
    AI_CHANNEL, min_val=-10.0, max_val=10.0, terminal_config=RSE
)
print(f"AI0 eingeschaltet ({AI_CHANNEL})")

do_task = nidaqmx.Task()
do_task.do_channels.add_do_chan(DO_CHANNEL, line_grouping=LineGrouping.CHAN_PER_LINE)
do_task.start()
do_task.write(AUS)
print("DO p0.0–p0.2 bereit (ROT, GELB, GRÜN)")

# ----- Plot-Setup -----
#  [C-Balken]  [F-Balken]
#  [K-Balken ] [V-Linienplot]
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle("Temperaturmessung – AD8495 / Thermoelement", fontsize=13)
ax_c,  ax_f  = axes[0]
ax_k,  ax_v  = axes[1]

# ----- Temperaturbereiche (0 °C = Nullpunkt jedes Balkens) -----
C_MIN,  C_MAX = 0.0, 105.0
F_MIN,  F_MAX = 32.0, 221
K_MIN,  K_MAX = 273.15, 378.15
V_MIN,  V_MAX = 0.0, 5.0

# ----- Celsius-Balken -----
bar_c = ax_c.bar(["°C"], [C_MIN], color="blue",  width=0.4, bottom=C_MIN)
ax_c.set_ylim(C_MIN, C_MAX)
ax_c.set_title("Celsius")
ax_c.set_ylabel("Temperatur (°C)")
ax_c.grid(True, axis="y", alpha=0.3)
label_c = ax_c.text(
    0, C_MIN, "", ha="center", va="bottom", fontsize=10
)

# ----- Fahrenheit-Balken -----
bar_f = ax_f.bar(["°F"], [F_MIN], color="red",   width=0.4, bottom=F_MIN)
ax_f.set_ylim(F_MIN, F_MAX)
ax_f.set_title("Fahrenheit  (0 °C = 32 °F)")
ax_f.set_ylabel("Temperatur (°F)")
ax_f.grid(True, axis="y", alpha=0.3)
label_f = ax_f.text(
    0, F_MIN, "", ha="center", va="bottom", fontsize=10
)

# ----- Kelvin-Balken -----
bar_k = ax_k.bar(["K"],  [K_MIN], color="green", width=0.4, bottom=K_MIN)
ax_k.set_ylim(K_MIN, K_MAX)
ax_k.set_title("Kelvin  (0 °C = 273.15 K)")
ax_k.set_ylabel("Temperatur (K)")
ax_k.grid(True, axis="y", alpha=0.3)
label_k = ax_k.text(
    0, K_MIN, "", ha="center", va="bottom", fontsize=10
)

# ----- Spannungs-Linienplot (gleitendes Fenster – wie in Praktikum 2) -----
volt_data = [0.0] * N_SAMPLES
x_ms      = [i * INTERVAL_MS for i in range(N_SAMPLES)]

ax_v.set_title("Spannungsgraph")
ax_v.set_xlabel("Zeit (ms)")
ax_v.set_ylabel("Spannung (V)")
ax_v.set_xlim(x_ms[0], x_ms[-1])
ax_v.set_ylim(V_MIN, V_MAX)
ax_v.grid(True, alpha=0.3)
volt_line, = ax_v.plot(x_ms, volt_data, color="blue")
volt_text  = ax_v.text(
    0.02, 0.95, "", transform=ax_v.transAxes,
    fontsize=11, va="top", color="blue"
)


# ----- Hilfsfunktionen -----
def get_led_state(celsius):
    if 0 <= celsius <= 10:
        return GRUEN
    elif 10 < celsius <= 20:
        return GELB
    elif celsius > 20:
        return ROT
    else:
        return AUS

def celsius_zu_fahrenheit(celsius):
    return celsius * 9/5 + 32

def celsius_zu_kelvin(celsius):
    return celsius + 273.15

def spannung_zu_temperatur(spannung):
    return (spannung - OFFSET_V) / EMPFINDLICHKEIT

def update_bar(bar_container, label, min, value):
    height = value - min
    bar = bar_container[0]
    bar.set_y(min)
    bar.set_height(height)
    label.set_position([bar.get_x() + bar.get_width() / 2,
                        min + height])
    label.set_text(f"{value:.2f}")

# ----- Update-Funktion -----
def update(frame):
    spannung   = ai_task.read()
    celsius    = spannung_zu_temperatur(spannung)
    fahrenheit = celsius_zu_fahrenheit(celsius)
    kelvin     = celsius_zu_kelvin(celsius)

    # ----- CSV -----
    zeitstempel = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    csv_writer.writerow([zeitstempel,
                         f"{celsius:.4f}", f"{fahrenheit:.4f}",
                         f"{kelvin:.4f}",  f"{spannung:.6f}"])
    csv_file.flush()

    # ----- Balken aktualisieren -----
    update_bar(bar_c, label_c, C_MIN, celsius)
    update_bar(bar_f, label_f, F_MIN, fahrenheit)
    update_bar(bar_k, label_k, K_MIN, kelvin)

    # ----- Spannung aktualisieren -----
    volt_data.append(spannung)
    volt_data.pop(0)
    t_end = frame * INTERVAL_MS
    new_x = list(range(t_end - (N_SAMPLES - 1) * INTERVAL_MS,t_end + INTERVAL_MS,INTERVAL_MS))
    volt_line.set_data(new_x, volt_data)
    ax_v.set_xlim(new_x[0], new_x[-1])
    volt_text.set_text(f"{spannung:.4f} V")

    do_task.write(get_led_state(celsius))


ani = FuncAnimation(fig, update, interval=INTERVAL_MS, cache_frame_data=False)

try:
    plt.show()
finally:
    do_task.write(AUS)
    do_task.close()
    ai_task.close()
    csv_file.close()
    print("Erfolgreich beendet")