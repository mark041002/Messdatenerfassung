import os
import glob
import csv

import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox

# ----- Konfiguration -----
TON_ORDNER = "ton"
CSV_EINZEL = "frequenzanalyse.csv"
CSV_KOMBI = "frequenzanalyse_kombiniert.csv"

STANDARD_XLIM_ZEIT = (0.0, 0.05)
STANDARD_XLIM_FFT = (0.0, 2050.0)


# ----- Hilfsfunktionen (unverändert aus 3a/3b) -----
def wav_einlesen(pfad):
    """
    Liest eine WAV-Datei ein und gibt (abtastrate, signal) zurück.
    Bei Stereo-Dateien wird nur der erste Kanal (links) verwendet.
    Das Signal wird auf den Bereich [-1, 1] normiert.
    """
    abtastrate, signal = wavfile.read(pfad)

    if signal.ndim > 1:                # Stereo -> nur linken Kanal nehmen
        signal = signal[:, 0]

    signal = signal.astype(np.float64)
    max_wert = np.max(np.abs(signal))
    if max_wert > 0:
        signal = signal / max_wert     # Normierung auf [-1, 1]

    return abtastrate, signal


def berechne_spektrum(signal: np.ndarray, abtastrate: float):
    n = len(signal)
    spektrum = np.fft.rfft(signal)
    frequenzen = np.fft.rfftfreq(n, d=1 / abtastrate)
    amplitude = np.abs(spektrum) * 2 / n
    return frequenzen, amplitude


def spektrum_exportieren(pfad, frequenzen, amplituden):
    with open(pfad, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(["Frequenz in Hz", "Amplitude"])
        for f_wert, a_wert in zip(frequenzen, amplituden):
            writer.writerow([f"{f_wert:.4f}", f"{a_wert:.6f}"])
    print(f"Exportiert nach: {pfad}")

# ----- Figure & Layout -----
fig = plt.figure(figsize=(13, 8))
fig.suptitle("Frequenzanalyse (interaktiv)", fontsize=13)

# Hauptplots (rechts, volle Höhe, nichts überlagert sie)
ax_zeit = fig.add_axes([0.40, 0.56, 0.57, 0.36])
ax_fft = fig.add_axes([0.40, 0.10, 0.57, 0.36])

# ----- linke Spalte: alle Eingaben -----
LINKS_X = 0.04
LINKS_BREITE = 0.30

def label(y, text):
    ax = fig.add_axes([LINKS_X, y, LINKS_BREITE, 0.025])
    ax.axis("off")
    ax.text(0, 0, text, fontsize=9)


def eingabe(y, initial=""):
    ax = fig.add_axes([LINKS_X, y, LINKS_BREITE, 0.045])
    return TextBox(ax, "", initial=initial)


# Dateiauswahl
label(0.90, "Datei 1 (Pfad):")
tb_datei1 = eingabe(0.85, initial="")

label(0.80, "Datei 2 (Pfad, optional):")
tb_datei2 = eingabe(0.75, initial="")

ax_btn_analyse = fig.add_axes([LINKS_X, 0.68, LINKS_BREITE, 0.05])
btn_analyse = Button(ax_btn_analyse, "Analysieren")

# X-Achsen Zeitbereich
label(0.57, "Zeit-Achse min (s) / max (s):")
tb_zeit_min = eingabe(0.53, initial=str(STANDARD_XLIM_ZEIT[0]))
tb_zeit_min.ax.set_position([LINKS_X, 0.52, LINKS_BREITE * 0.47, 0.045])
tb_zeit_max = eingabe(0.53, initial=str(STANDARD_XLIM_ZEIT[1]))
tb_zeit_max.ax.set_position([LINKS_X + LINKS_BREITE * 0.53, 0.52, LINKS_BREITE * 0.47, 0.045])

# X-Achsen FFT-Bereich
label(0.47, "FFT-Achse min (Hz) / max (Hz):")
tb_fft_min = eingabe(0.425, initial=str(STANDARD_XLIM_FFT[0]))
tb_fft_min.ax.set_position([LINKS_X, 0.42, LINKS_BREITE * 0.47, 0.045])
tb_fft_max = eingabe(0.425, initial=str(STANDARD_XLIM_FFT[1]))
tb_fft_max.ax.set_position([LINKS_X + LINKS_BREITE * 0.53, 0.42, LINKS_BREITE * 0.47, 0.045])

ax_btn_xlim = fig.add_axes([LINKS_X, 0.35, LINKS_BREITE, 0.05])
btn_xlim = Button(ax_btn_xlim, "X-Achsen übernehmen")


# ----- Kernlogik -----
def analysieren(event):
    datei1 = tb_datei1.text.strip()
    datei2 = tb_datei2.text.strip()

    if not datei1:
        print("Fehler: Bitte Datei 1 angeben.")
        return

    try:
        abtastrate1, signal1 = wav_einlesen(datei1)
    except Exception as e:
        print(f"Fehler beim Einlesen von Datei 1 ({datei1}): {e}")
        return

    print(f"Datei 1: {datei1}  |  Samples: {len(signal1)}  |  "
          f"Abtastrate: {abtastrate1} Hz  |  Dauer: {len(signal1)/abtastrate1:.2f} s")

    if datei2:
        try:
            abtastrate2, signal2 = wav_einlesen(datei2)
        except Exception as e:
            print(f"Fehler beim Einlesen von Datei 2 ({datei2}): {e}")
            return

        if abtastrate1 != abtastrate2:
            print("Fehler: Beide Dateien müssen dieselbe Abtastrate haben! "
                  f"Datei 1: {abtastrate1} Hz, Datei 2: {abtastrate2} Hz")
            return

        abtastrate = abtastrate1
        n_min = min(len(signal1), len(signal2))
        signal = signal1[:n_min] + signal2[:n_min]
        titel = f"{os.path.basename(datei1)} + {os.path.basename(datei2)} (überlagert)"
        csv_pfad = CSV_KOMBI

    else:
        abtastrate = abtastrate1
        signal = signal1
        titel = os.path.basename(datei1)
        csv_pfad = CSV_EINZEL

    t = np.arange(len(signal)) / abtastrate
    freq, amplitude = berechne_spektrum(signal, abtastrate)
    spektrum_exportieren(csv_pfad, freq, amplitude)

    # ----- Plots neu zeichnen -----
    ax_zeit.clear()
    ax_zeit.plot(t, signal, color="blue")
    ax_zeit.set_title("Zeitbereich")
    ax_zeit.set_xlabel("Zeit (s)")
    ax_zeit.set_ylabel("Amplitude")
    ax_zeit.grid(True, alpha=0.3)

    ax_fft.clear()
    ax_fft.plot(freq, amplitude, color="green")
    ax_fft.set_title("Fourier-Analyse (Magnitude Peak, linear)")
    ax_fft.set_xlabel("Frequenz (Hz)")
    ax_fft.set_ylabel("Amplitude")
    ax_fft.grid(True, alpha=0.3)

    fig.suptitle(f"Frequenzanalyse: {titel}", fontsize=13)

    xlim_anwenden()  # aktuelle Werte aus den Textfeldern übernehmen
    fig.canvas.draw_idle()


def pruefe_wert(wert, fallback):
    if isinstance(wert, float):
        return wert
    return fallback


#----- User Eingaben überpüfen und übernehmen -----
def xlim_anwenden(event):
    z_min = pruefe_wert(tb_zeit_min.text, STANDARD_XLIM_ZEIT[0])
    z_max = pruefe_wert(tb_zeit_max.text, STANDARD_XLIM_ZEIT[1])
    f_min = pruefe_wert(tb_fft_min.text, STANDARD_XLIM_FFT[0])
    f_max = pruefe_wert(tb_fft_max.text, STANDARD_XLIM_FFT[1])

    if z_min < z_max:
        ax_zeit.set_xlim(z_min, z_max)
    if f_min < f_max:
        ax_fft.set_xlim(f_min, f_max)

    fig.canvas.draw_idle()


btn_analyse.on_clicked(analysieren)
btn_xlim.on_clicked(xlim_anwenden)
plt.show()