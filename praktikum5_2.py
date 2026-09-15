"""Der Hauptunterschied liegt darin, wie Daten empfangen und angezeigt werden:
Ein Waveform Chart (Diagramm) fügt neue Messwerte fortlaufend an eine bestehende Historie an
Waveform Chart: Verarbeitet einzelne Datenpunkte oder Arrays nacheinander.
Besitzt einen eingebauten Puffer (History) für vergangene Werte.
Aktualisiert sich fließend im laufenden Betrieb.

Ideal für Live-Messungen und langsame Prozesse (z. B. Temperatur).
Zeigt den aktuellen Wert direkt im zeitlichen Verlauf an.

Waveform Graph (Graph) das gesamte Bild bei jedem neuen Datenpaket komplett erneuert.
Waveform Graph: Benötigt ein kompletter Array oder Block an Messwerten auf einmal.
Überschreibt die alte Ansicht bei jedem neuen Befehl vollständig.
Speichert von Haus aus keine Historie alter Datenpakete.

Ideal für m Datensätze, Dateien oder schnelle Signale (z. B. Audio).
Dient der nachträglichen Analyse eines abgeschlossenen Blocks.
"""

import numpy as np
import matplotlib.pyplot as plt
import csv

# ----- Konfiguration -----
FREQ_1   = 10
AMP_1    = 5

FREQ_2   = 50
AMP_2    = 10

ABTASTRATE = 1000    #Samples pro Sekunde (muss > 2*max(FREQ) sein, Nyquist!)
DAUER      = 1.0     #Länge des simulierten Zeitfensters in S

CSV_DATEI  = "frequenzanalyse.csv"

# ----- Signale erzeugen -----
n_samples = int(ABTASTRATE * DAUER)
t = np.linspace(0, DAUER, n_samples, endpoint=False)

sinus_1 = AMP_1 * np.sin(2 * np.pi * FREQ_1 * t)
sinus_2 = AMP_2 * np.sin(2 * np.pi * FREQ_2 * t)  #2 pi = 360°, Umrechnung auf Bogenmaß

# ----- Aufgabe 2d: Beide Sinusschwingungen -----
ueberlagert = sinus_1 + sinus_2

# ----- Aufgabe 2e: Frequenzanalyse des überlagerten Signals -----
def berechne_spektrum(signal, abtastrate):
    n = len(signal)
    spektrum = np.fft.rfft(signal)
    """
    real fft, da wir reele Zahlen haben (keine komplexen Werte)
    -> Spektrum ist symmetrisch, reel berechnet dann nur die positivie Hälfte, spart Leistung und Zeit. 
    n/2+1 Werte
    X(k)= Summe von j=0 bis n-1 von x[j] * e^(-i*2(PI)kj/n)
    Gibt aus wie gut Signal mit einer Sinus-/Kosinusschwingung der Frequenz k übereinstimmt.
    Passt Frequenz k sehr gut zu dem Signal addieren sie sich, passt sie nicht heben sie sich auf
    """

    frequenzen = np.fft.rfftfreq(n, d=1 / abtastrate)
    """
    rfft liefert Werte des Spektrums (an Position 0, 1, 2, 3, …), 
    nicht welche Frequenz in Hz diese Position repräsentiert. 
    Das Ergebnis ist ein Array wie [0, 4, 8] Hz (Beispielwerte), 
    das du direkt für die x-Achse deines FFT-Plots nutzt.

    F(i) = (i*abtastrate)/Samples
    Sagt welche Frequenz für das Ergebnis von Spektrum/Amplitude genutzt wird
    """
    amplitude = np.abs(spektrum) * 2 / n
    #amplitude[0] /= 2 #braucht man das? eigentlich nicht?
    """
    np.abs(spektrum) nimmt den Betrag der komplexen Zahlen – 
    das ist die reine Stärke jeder Frequenz, unabhängig von der Phase.

    * 2 / n: Reine Skalierungs-/Normierungsfrage. 
    Ohne Werte mit der Anzahl der Samples n (mehr Samples → größere Rohwerte)
    außerdem wird nur halbe tatsächliche Amplitude zeigen (weil rfft ja die andere Spiegelhälfte 
    weggelassen hat) 
"""

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