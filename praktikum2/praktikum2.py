import nidaqmx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from nidaqmx.constants import LineGrouping, TerminalConfiguration
# ----- Konfiguration -----
AI_CHANNEL  = "Dev1/ai0"
AO_CHANNEL  = "Dev1/ao0"
DO_CHANNEL  = "Dev1/port0/line0:2"   # p0.0=ROT, p0.1=GELB, p0.2=GRÜN
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 10.0
N_SAMPLES   = 200
UPDATE_MS   = 20
RSE = TerminalConfiguration.RSE    # RSE = Messung gegen analoge Masse, für bessere Werte

# ----- LED-Zustände -----
ROT   = [True,  False, False]
GELB  = [False, True,  False]
GRUEN = [False, False, True ]
ALLE  = [True,  True,  True ]
AUS   = [False, False, False]

# ----- Schwellwerte → LED-Zustand -----
def get_led_state(voltage):
    if voltage < 0.2:
        return ALLE
    elif 0.4 <= voltage <= 4.0:
        return GRUEN
    elif 4.0 < voltage <= 8.0:
        return GELB
    elif voltage > 8.0:
        return ROT
    else:
        return AUS

# ----- DAQmx Tasks -----
ao_task = nidaqmx.Task()
ao_task.ao_channels.add_ao_voltage_chan(AO_CHANNEL, min_val=0.0, max_val=10.0)
ao_task.write(MAX_VOLTAGE)
ao_task.start()
print(f"AO0 eingeschaltet: {MAX_VOLTAGE} V")
ai_task = nidaqmx.Task()
ai_task.ai_channels.add_ai_voltage_chan(AI_CHANNEL, min_val=MIN_VOLTAGE, max_val=MAX_VOLTAGE, terminal_config=RSE)
print("AI0 eingeschaltet")
do_task = nidaqmx.Task()
do_task.do_channels.add_do_chan(DO_CHANNEL,line_grouping=LineGrouping.CHAN_PER_LINE)
do_task.start()
do_task.write(AUS)
print("DO p0.0–p0.2 bereit")

# ----- Plot -----
data  = [0.0] * N_SAMPLES
x_ms  = [i * UPDATE_MS for i in range(N_SAMPLES)]
fig, ax = plt.subplots(figsize=(12, 8))
fig.suptitle("Potentiometer – Live-Anzeige", fontsize=13)
ax.grid(True, alpha=0.3)
ax.set_xlim(x_ms[0], x_ms[-1])
ax.set_xlabel("Zeit (ms)")
ax.set_ylim(MIN_VOLTAGE, MAX_VOLTAGE)
ax.set_ylabel("Spannung (V)")
line = ax.plot(x_ms, data, color="blue") [0]    # hier einmal mit [0], alternativ kann man auch line, schreiben
voltage_text = ax.text(
    0.02, 0.95, "", transform=ax.transAxes,
    fontsize=11, va="top", color="blue"
)

# ----- Update-Funktion -----
def update(frame):
    value = ai_task.read()
    data.append(value)
    data.pop(0)
    t_end = frame * UPDATE_MS

    # Berechnet N_SAMPLES Zeitstempel mit Abstand UPDATE_MS, endend bei t_end (gleitendes Fenster)
    new_x = list(range(t_end - (N_SAMPLES - 1) * UPDATE_MS, t_end + UPDATE_MS, UPDATE_MS))


    line.set_data(new_x, data)
    #Passt die X-Achse den Daten an damit es fortlaufend bleibt
    ax.set_xlim(new_x[0], new_x[-1])
    voltage_text.set_text(f"{value:.3f} V")
    do_task.write(get_led_state(value))


ani = FuncAnimation(fig, update, interval=UPDATE_MS,cache_frame_data=False)

try:
    plt.show()
finally:
    do_task.write(AUS)
    do_task.close()
    ai_task.close()
    ao_task.write(0.0)
    ao_task.close()
    print("Erfolgreich beendet")