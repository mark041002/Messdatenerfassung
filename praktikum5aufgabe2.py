import numpy as np
import matplotlib.pyplot as plt
import csv

# ----- Konfiguration -----
#TODO: Werte einfügen

FREQ_1   = None
AMP_1    = None

FREQ_2   = None
AMP_2    = None

ABTASTRATE = None    #Samples pro Sekunde (muss > 2*max(FREQ) sein, Nyquist!)
DAUER      = 1.0     #Länge des simulierten Zeitfensters in S

CSV_DATEI  = "frequenzanalyse.csv"

# ----- Signale erzeugen -----
n_samples = int(ABTASTRATE * DAUER)
t = np.linspace(0, DAUER, n_samples, endpoint=False)

# ----- Aufgabe 2a: Erster Sinus -----
# TODO: Erzeuge das Sinus-Signal "sinus_1" mit np.sin() und den definierten Konstanten AMP_1 und FREQ_1
sinus_1 = None

# ----- Aufgabe 2b: Zweiter Sinus -----
# TODO: Erzeuge das Sinus-Signal "sinus_2" mit np.sin() und den definierten Konstanten
sinus_2 = None

# ----- Aufgabe 2d: Beide Sinusschwingungen -----
# TODO: Überlagere sinus_1 und sinus_2
ueberlagert = None

# ----- Aufgabe 2e: Frequenzanalyse des überlagerten Signals -----
def berechne_spektrum(signal, abtastrate):
    n = len(signal)

    # Nutze die Numpy.fft Bibliothek-Funktionen, Dokumentation online angucken
    spektrum = None  # TODO: ersetzen

    frequenzen = None  # TODO: ersetzen

    # Formel zum normieren der Spektrumswerte
    # TODO: Was fehlt in dieser Formel noch? (Hat mit rfft zu tun)
    amplitude = np.abs(spektrum) / n

    return frequenzen, amplitude


freq_achse, amplitude_spektrum = berechne_spektrum(ueberlagert, ABTASTRATE)

# ----- Aufgabe 2g: Export der Frequenzanalyse-Daten in ein Tabellendokument -----
with open(CSV_DATEI, "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file, delimiter=";")
    writer.writerow(["Frequenz in Hz", "Amplitude"])
    for f_wert, a_wert in zip(freq_achse, amplitude_spektrum):
        writer.writerow([f"{f_wert:.4f}", f"{a_wert:.6f}"])
print(f"Frequenzanalyse-Daten exportiert nach: {CSV_DATEI}")

# ----- Plot-Setup -----
fig, (ax_zeit, ax_fft) = plt.subplots(2, 1, figsize=(8, 6)) #Direkt achsen per Tupel genommen
fig.suptitle("Praktikum 5 – Aufgabe 2: Funktionsgenerator & Frequenzanalyse")

# ----- Zeitbereich: alle drei Signale in einem Graphen (Aufgabe 2d) -----
ax_zeit.plot(t, sinus_1, label=f"Sinus 1 ({FREQ_1} Hz, A={AMP_1})", color="blue")
ax_zeit.plot(t, sinus_2, label=f"Sinus 2 ({FREQ_2} Hz, A={AMP_2})", color="red")
ax_zeit.plot(t, ueberlagert, label="Überlagerung", color="green")
ax_zeit.set_title("Sinus-Kurven")
ax_zeit.set_xlabel("Zeit (s)")
ax_zeit.set_ylabel("Amplitude")
ax_zeit.set_xlim(0, 0.25)
ax_zeit.grid(True, alpha=0.3)
ax_zeit.legend(loc="upper right")

# ----- Frequenzbereich: FFT der Überlagerung (Aufgabe 2e) -----
ax_fft.plot(freq_achse, amplitude_spektrum, color="green")
ax_fft.set_title("Fourier-Analyse")
ax_fft.set_xlabel("Frequenz (Hz)")
ax_fft.set_ylabel("Amplitude")
ax_fft.set_xlim(0, 110)
ax_fft.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()