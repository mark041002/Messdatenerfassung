"""
  Praktikum 4 – Temperaturregelung mit PID-Regler (simple-pid Bibliothek)
=============================================================================
  Sensor:      Honeywell HSCDRRD006MGAA5  (6 mbar, 0.5–4.5 V)
  Temperatur:  AD8495 (5 mV/°C, Offset 1.25 V)
  Thyristorsteller:       A-senco SCR-80x (3.5 V = 0 %, 9.4 V = 100 %)
=============================================================================
"""

import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox, Button
from simple_pid import PID
import csv
from datetime import datetime
import numpy as np

# ----- KONFIGURATION -----
AI_KANAL  = "Dev1/ai0"   # Drucksensor
AI_KANAL1 = "Dev1/ai1"   # Temperatursensor Wasserbad
AI_KANAL2 = "Dev1/ai2"   # Temperatursensor Braukessel
AI_KANAL3 = "Dev1/ai3"   # Kontrollspannung Thyristorsteller
AO_KANAL  = "Dev1/ao0"   # Thyristorsteller

# Diagramm-Variablen
INTERVAL_MS = 100                  # Animationsintervall in ms
DT          = INTERVAL_MS / 1000.0 # Abtastzeit, 0,01 Sekunden (für PID)
N_SAMPLES   = 200                  # Anzahl Punkte im Zeitverlauf
CSV_DATEI   = "praktikum4.csv"


# Drucksensor-Kennwerte
VSUPPLY    = 5.0        # Versorgungsspannung [V]
PMIN, PMAX = 0.0, 6.0  # Messbereich [mbar]

# Temperatursensor-Kennwerte
TEMP_EMPFINDLICHKEIT = 0.005  # V/°C
TEMP_OFFSET          = 1.25   # Offset bei 0 °C [V]

# Thyristorsteller-Kennwerte, Ausgerechnet mit LibreOffice
THYRISTOR_Y_OFFSET = 2.743
THYRISTOR_Y_MAX    = 9.4 # Letzter "Sicherer" Wert nach oben (aus dem Diagramm)
THYRISTOR_X_STEIGUNG = 0.064

AO_MIN, AO_MAX = 0.0, 10.0  # DAQ-Ausgangsgrenzen [V] für den Thyristorsteller

# Regler-Startwerte (per Eingabefeld änderbar)
ZIELTEMPERATUR_C = 35.0
KP, KI, KD       = 1.0, 0.0, 0.0

# ----- PID-REGLER -----
pid = PID(Kp=KP, Ki=KI, Kd=KD, setpoint=ZIELTEMPERATUR_C,
          sample_time=DT, output_limits=(0, 100))  # Stellgröße auf 0-100% begrenzen

# ----- CSV vorbereiten -----
csv_file   = open(CSV_DATEI, "w", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file, delimiter=";")
csv_writer.writerow(["Zeitstempel","Sensorspannung Druck [V]","Druck [mbar]",
                     "Temperatur Wasserbad [°C]","Temperatur Kessel [°C]","Zieltemperatur [°C]",
                     "Fehler Temperatur [°C]","PID-Ausgang [%]","Steuerspannung [V]",
                     "Kontrollspannung [V]"])

# ----- DAQmx Tasks -----
ai_task = nidaqmx.Task()

ai_task.ai_channels.add_ai_voltage_chan(AI_KANAL, min_val=-10.0, max_val=10.0,terminal_config=TerminalConfiguration.RSE)
ai_task.ai_channels.add_ai_voltage_chan(AI_KANAL1, min_val=-10.0, max_val=10.0,terminal_config=TerminalConfiguration.RSE)
ai_task.ai_channels.add_ai_voltage_chan(AI_KANAL2, min_val=-10.0, max_val=10.0,terminal_config=TerminalConfiguration.RSE)
ai_task.ai_channels.add_ai_voltage_chan(AI_KANAL3, min_val=-10.0, max_val=10.0,terminal_config=TerminalConfiguration.RSE)

ao_task = nidaqmx.Task()
ao_task.ao_channels.add_ao_voltage_chan(AO_KANAL, min_val=AO_MIN, max_val=AO_MAX)
ao_task.start()
ao_task.write(0.0)  # Starten mit 0 Volt



# ----- PLOT-LAYOUT -----
#  --------------------------------------------
#  |  Gage (oben links)  |  PID-Controls +     |
#  |                     |  Info-Block         |
#  |---------------------|---------------------|
#  │  Temperaturen       |  Zeitverlauf        |
#  ---------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle(f"Praktikum 4",fontsize=13)

ax_gage, ax_controls = axes[0]  # obere Zeile
ax_temp,  ax_lin      = axes[1]  # untere Zeile

ax_controls.axis("off")
ax_controls.set_title("PID-Regler Einstellungen", fontsize=11)

# ----- Subplot oben links: Druckanzeige (Balken) -----
bar_druck = ax_gage.bar(["Druck"], [0.0], color="orange", width=0.4)
ax_gage.set_ylim(PMIN, PMAX)
ax_gage.set_title("Druckanzeige")
ax_gage.set_ylabel("Druck (mbar)")
ax_gage.grid(True, axis="y", alpha=0.3)
label_druck = ax_gage.text(0, 0, "", ha="center", va="bottom", fontsize=10)

# ----- TextBoxen + Button (oben rechts, figure-Koordinaten) -----

labels = ["Zieltemperatur (°C):", "Kp:", "Ki:", "Kd:"]
inits  = [str(ZIELTEMPERATUR_C), str(KP), str(KI), str(KD)]

tb_ax_ziel = fig.add_axes((0.7, 0.8, 0.1, 0.04))
tb_ax_kp   = fig.add_axes((0.7, 0.75, 0.1, 0.04))
tb_ax_ki   = fig.add_axes((0.7, 0.7, 0.1, 0.04))
tb_ax_kd   = fig.add_axes((0.7, 0.65, 0.1, 0.04))

ax_btn = fig.add_axes((0.7, 0.595, 0.1, 0.04))

tb_ziel_temp = TextBox(tb_ax_ziel,labels[0],initial=inits[0])
tb_kp = TextBox(tb_ax_kp,labels[1],initial=inits[1])
tb_ki = TextBox(tb_ax_ki,labels[2],initial=inits[2])
tb_kd = TextBox(tb_ax_kd,labels[3],initial=inits[3])
btn_apply = Button(ax_btn,"Übernehmen",color="lightcoral",hovercolor="tomato")

def on_apply(event):
    try:
        pid.setpoint = float(tb_ziel_temp.text)
    except ValueError:
        tb_ziel_temp.set_val(f"{pid.setpoint:.2f}")
    # PID-Parameter übernehmen; bei Fehler alle drei Felder zurücksetzen
    try:
        pid.tunings = (float(tb_kp.text), float(tb_ki.text), float(tb_kd.text))
    except ValueError:
        kp, ki, kd = pid.tunings
        tb_kp.set_val(f"{kp:.3f}"); tb_ki.set_val(f"{ki:.3f}"); tb_kd.set_val(f"{kd:.3f}")

btn_apply.on_clicked(on_apply)

# ----- Subplot unten links: Temperaturen -----
TEMP_MIN, TEMP_MAX = -1.0, 105.0
bar_temp = ax_temp.bar(["Wasserbad", "Braukessel"], [0.0, 0.0],
                       color=["tomato", "coral"], width=0.4)
ax_temp.set_ylim(TEMP_MIN, TEMP_MAX)
ax_temp.set_title("Temperatursensoren")
ax_temp.set_ylabel("Temperatur (°C)")
ax_temp.grid(True, axis="y", alpha=0.3)
label_t1 = ax_temp.text(0, 0, "", ha="center", va="bottom", fontsize=10)
label_t2 = ax_temp.text(1, 0, "", ha="center", va="bottom", fontsize=10)


# ----- Subplot unten rechts: Zeitverlauf -----
regel_puffer     = [0.0] * N_SAMPLES            # Ringpuffer aktuelle Regelgröße
spannung_puffer  = [0.0] * N_SAMPLES            # Ringpuffer Steuerspannung (Ausgang)
soll_puffer      = [pid.setpoint] * N_SAMPLES   # Ringpuffer Solltemperatur
x_ms             = [i * INTERVAL_MS for i in range(N_SAMPLES)]  # Zeitachse

ax_lin.set_title("Zeitverlauf: Temperatur & Steuerspannung")
ax_lin.set_xlabel("Zeit (ms)")
ax_lin.set_ylabel("Temperatur Regelgröße (°C)", color="green")
ax_lin.set_xlim(x_ms[0], x_ms[-1])
ax_lin.set_ylim(TEMP_MIN, TEMP_MAX)
ax_lin.grid(True, alpha=0.3)
ax_lin.tick_params(axis="y", labelcolor="green")

linie_regelgroesse, = ax_lin.plot(x_ms, regel_puffer, color="green", label="Temp. Regelgröße [°C]")
linie_soll,         = ax_lin.plot(x_ms, soll_puffer, color="red", linestyle="--", label="Solltemperatur [°C]")

# Zweite Y-Achse für Steuerspannung (teilt sich x-Achse mit ax_lin)
ax_lin2 = ax_lin.twinx()
ax_lin2.set_ylabel("Steuerspannung (V)", color="darkblue")
ax_lin2.set_ylim(AO_MIN-0.1, AO_MAX)
ax_lin2.tick_params(axis="y", labelcolor="darkblue")
linie_steu, = ax_lin2.plot(x_ms, spannung_puffer,color="darkblue", label="Steuerspannung [V]")

# Legende: alle Linien gemeinsam in ax_lin (unten rechts im Graph)
alle_linien = [linie_regelgroesse, linie_soll, linie_steu]
alle_labels = [l.get_label() for l in alle_linien]
ax_lin.legend(alle_linien, alle_labels, loc="upper left", fontsize=8)

# Ampel-Anzeige oberhalb des Zeitverlauf-Plots
diff_text = ax_lin.text(0.5, 1.14, "", transform=ax_lin.transAxes,
                        ha="center", va="bottom", fontsize=11, fontweight="bold",
                        bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.85))

# ----- Umrechnungsfunktionen -----
def spannung_zu_druck_mbar(u):
    # Datenblattformel: P = (U - 0.1·Vs) · (Pmax-Pmin) / (0.8·Vs) + Pmin
    # Mit Vs=5V, Pmin=0, Pmax=6 → P = (U - 0.5) · 1.5
    return (u - 0.1 * VSUPPLY) * (PMAX - PMIN) / (0.8 * VSUPPLY) + PMIN

def spannung_zu_temperatur(u):
    return (u - TEMP_OFFSET) / TEMP_EMPFINDLICHKEIT

def last_zu_spannung(last_pct):
    # Stellgröße [%] → Steuerspannung [V] nach Thyristorsteller-Kennlinie
    wert = (last_pct * THYRISTOR_X_STEIGUNG) + THYRISTOR_Y_OFFSET
    if wert <= THYRISTOR_Y_OFFSET:
        return AO_MIN
    return min(THYRISTOR_Y_MAX, wert)

# ----- Update-Funktion -----
def update(frame):

    # Messwerte lesen: mehrere Messungen einlesen und per Mittelwert
    # zusammenfassen (für glatte Werte)
    rohwerte = []
    for _ in range(5):
        einzelmessung = ai_task.read()
        rohwerte.append(einzelmessung)

    messwerte = np.median(rohwerte, axis=0)

    u_druck    = messwerte[0]
    druck_mbar = spannung_zu_druck_mbar(u_druck)

    wasserbad_c  = spannung_zu_temperatur(messwerte[1])   # Wasserbad
    braukessel_c = spannung_zu_temperatur(messwerte[2])   # Braukessel
    u_kontroll   = messwerte[3]  # Kontrollspannung (Rückmessung ai3)

    regel_temp = wasserbad_c
    #regel_temp = braukessel_c  #Einstellen welche Zieltemeperatur

    stellgroesse_pct = pid(regel_temp)
    fehler_temp      = pid.setpoint - regel_temp  # nur für CSV + Info-Block

    # Stellgröße in Steuerspannung umrechnen
    u_steuer = last_zu_spannung(stellgroesse_pct)
    ao_task.write(u_steuer)

    # Messwerte in CSV schreiben
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    csv_writer.writerow([jetzt, f"{u_druck:.6f}", f"{druck_mbar:.4f}",
                         f"{wasserbad_c:.4f}", f"{braukessel_c:.4f}",
                         f"{pid.setpoint:.4f}", f"{fehler_temp:.4f}",
                         f"{stellgroesse_pct:.2f}", f"{u_steuer:.4f}",
                         f"{u_kontroll:.4f}"])
    csv_file.flush()

    bar_druck[0].set_height(druck_mbar)
    label_druck.set_position((bar_druck[0].get_x() + bar_druck[0].get_width() / 2, druck_mbar))
    label_druck.set_text(f"{druck_mbar:.3f} mbar")

    for i, (bar, label, temp) in enumerate(zip(bar_temp, [label_t1, label_t2], [wasserbad_c, braukessel_c])):
        bar.set_height(temp)
        label.set_position([bar.get_x() + bar.get_width() / 2, temp])
        label.set_text(f"{temp:.2f} °C")

    # Zeitverlauf Diagramm weiterlaufen lassen (wie in letzten Praktikums)
    spannung_puffer.append(u_steuer)
    spannung_puffer.pop(0)
    regel_puffer.append(regel_temp)
    regel_puffer.pop(0)
    soll_puffer.append(pid.setpoint)
    soll_puffer.pop(0)

    t_end = frame * INTERVAL_MS
    new_x = list(range(t_end - (N_SAMPLES-1)*INTERVAL_MS,
                       t_end + INTERVAL_MS, INTERVAL_MS))
    linie_steu.set_data(new_x, spannung_puffer)
    linie_regelgroesse.set_data(new_x, regel_puffer)
    linie_soll.set_data(new_x, soll_puffer)
    ax_lin.set_xlim(new_x[0], new_x[-1])

    # Ampel-Anzeige: Differenz zwischen Steuerspannung (Soll) und Kontrollspannung
    diff_spannung = abs(u_steuer - u_kontroll)
    if diff_spannung <= 0.1:
        farbe = "lightgreen"
    elif diff_spannung <= 1.0:
        farbe = "orange"
    else:
        farbe = "red"
    diff_text.set_text(f"Differenzspannung (Steuer–Kontrolle): {diff_spannung:.3f} V")
    diff_text.get_bbox_patch().set_facecolor(farbe)

ani = FuncAnimation(fig, update, interval=INTERVAL_MS,cache_frame_data=False)
try:
    plt.show()
finally:
    ao_task.write(0.0)
    ao_task.stop()
    ao_task.close()
    ai_task.close()
    csv_file.close()
    print("Erfolgreich beendet")