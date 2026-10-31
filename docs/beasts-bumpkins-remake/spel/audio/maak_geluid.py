"""Eigen synthese voor de Beasts & Bumpkins-remake (audio.md, bron 2): omgeving, werk, dieren en interface.

Alleen numpy (geen scipy nodig). Schrijft 16-bit mono wav op 22050 Hz naar audio/eigen/.
Deterministisch (vaste seed): opnieuw draaien geeft dezelfde bytes, dus geen ruis in git.
Lussen worden in het frequentiedomein gefilterd (circulair) met periodieke omhullenden, dus naadloos.
Niets uit het origineel: het origineel in lokaal/audio_origineel is hooguit naar geluisterd.

    py -3.10 audio/maak_geluid.py          (vanuit spel/)
"""
import os
import wave

import numpy as np

SR = 22050
UIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eigen")
rng = np.random.default_rng(1996)


def schrijf(naam, x, piek=0.89):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x))
    if m > 0:
        x = x / m * piek
    d = (np.clip(x, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(os.path.join(UIT, naam + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(d.tobytes())


def tijd(duur):
    return np.arange(int(duur * SR)) / SR


def band(x, lo, hi, orde=4):
    """Banddoorlaat via FFT (circulair: een lus blijft naadloos)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    f[0] = 1e-3
    m = np.ones_like(f)
    if lo:
        m *= 1.0 / (1.0 + (lo / f) ** orde)
    if hi:
        m *= 1.0 / (1.0 + (f / hi) ** orde)
    return np.fft.irfft(X * m, len(x))


def kleur_ruis(n, macht):
    """Ruis met spectrum 1/f^macht (0 wit, 0.5 roze, 1 bruin), circulair."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1]
    return np.fft.irfft(X / f ** macht, n)


def norm(x):
    m = np.max(np.abs(x))
    return x / m if m > 0 else x


def per(n, cycli, fase=0.0):
    """Periodieke sinus met een geheel aantal cycli over de lus."""
    return np.sin(2 * np.pi * cycli * np.arange(n) / n + fase)


def legg(doel, klank, start, circulair=True):
    """Tel `klank` op in `doel` vanaf sample `start` (circulair om de lus heen)."""
    n = len(doel)
    idx = start + np.arange(len(klank))
    if circulair:
        np.add.at(doel, idx % n, klank)
    else:
        ok = idx < n
        doel[idx[ok]] += klank[ok]


def omhul(n, aanzet, verval):
    t = np.arange(n) / SR
    a = np.minimum(1.0, t / max(aanzet, 1e-4))
    return a * np.exp(-np.maximum(0.0, t - aanzet) / verval)


def galm(x, duur=0.6, mix=0.25):
    n = int(duur * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (duur / 5.0))
    ir = band(ir, 300, 5000)
    y = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n), len(x) + n)
    y = norm(y) * np.max(np.abs(x))
    uit = np.zeros(len(x) + n)
    uit[:len(x)] += x
    return uit + mix * y


def toon(f, duur, partialen=((1, 1.0),), verval=0.5, aanzet=0.005, vibrato=0.0):
    t = tijd(duur)
    fase = 2 * np.pi * f * (t + vibrato * np.sin(2 * np.pi * 5.5 * t) / (2 * np.pi * 5.5))
    x = sum(a * np.sin(fase * k) for k, a in partialen)
    return x * omhul(len(t), aanzet, verval)


# ---------------------------------------------------------------- omgevingslussen

def wind():
    n = int(12 * SR)
    laag = norm(band(kleur_ruis(n, 1.0), 60, 900, 2))
    ruis = norm(band(kleur_ruis(n, 0.5), 300, 2500))
    fluit = norm(band(rng.standard_normal(n), 520, 640, 8))
    g1 = 0.65 + 0.2 * per(n, 2) + 0.15 * per(n, 5, 1.0)
    g2 = np.clip(0.3 + 0.45 * per(n, 3, 2.0) + 0.25 * per(n, 7), 0.0, None)
    g3 = np.clip(per(n, 2, 0.5), 0.0, None) ** 2
    schrijf("wind", laag * g1 + 0.35 * ruis * g2 + 0.12 * fluit * g3, 0.8)


def golven():
    n = int(12 * SR)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for start in (0.0, 4.3, 8.1):            # drie golven, om de lus heen
        d = (t - start) % 12.0
        env += np.where(d < 1.6, (d / 1.6) ** 2, np.exp(-(d - 1.6) / 1.4))
    env = 0.18 + env / env.max()
    rommel = norm(band(kleur_ruis(n, 1.0), 40, 450, 2))
    schuim = norm(band(rng.standard_normal(n), 700, 6500, 2))
    schuim_env = np.roll(env, int(0.4 * SR)) ** 2.2
    schrijf("golven", rommel * env ** 0.7 + 0.45 * schuim * schuim_env, 0.8)


def vuur():
    n = int(6 * SR)
    x = 0.35 * norm(band(kleur_ruis(n, 0.5), 60, 500, 2)) * (0.8 + 0.2 * per(n, 3))
    x += 0.08 * norm(band(rng.standard_normal(n), 2000, 7000))
    for _ in range(140):                      # knetteren
        L = int(rng.uniform(0.002, 0.012) * SR)
        k = band(rng.standard_normal(L), 1500, 9000) * omhul(L, 0.0005, rng.uniform(0.001, 0.004))
        legg(x, k * rng.lognormal(-1.2, 0.7), int(rng.integers(n)))
    for _ in range(9):                        # een paar knallen
        L = int(0.05 * SR)
        k = band(rng.standard_normal(L), 300, 2500) * omhul(L, 0.001, 0.012)
        legg(x, k * rng.uniform(1.0, 1.8), int(rng.integers(n)))
    schrijf("vuur", x, 0.8)


def regen():
    n = int(8 * SR)
    x = 0.5 * norm(band(rng.standard_normal(n), 500, 9000, 2)) * (0.9 + 0.1 * per(n, 4))
    for _ in range(2200):                     # druppels
        L = int(rng.uniform(0.001, 0.004) * SR)
        f0 = rng.uniform(2500, 7000)
        k = np.sin(2 * np.pi * f0 * np.arange(L) / SR) * omhul(L, 0.0002, 0.0012)
        legg(x, k * rng.lognormal(-1.5, 0.6), int(rng.integers(n)))
    schrijf("regen", x, 0.8)


def krekels():
    n = int(4 * SR)
    t = np.arange(n) / SR
    x = 0.05 * norm(band(kleur_ruis(n, 0.5), 200, 1500))
    for f0, chirps, pulsen, sterk in ((4300, 8, 3, 1.0), (4750, 7, 4, 0.7), (3900, 9, 3, 0.5), (5100, 5, 2, 0.35)):
        fase = rng.uniform(0, 1)
        draag = np.sin(2 * np.pi * f0 * t) + 0.2 * np.sin(2 * np.pi * 2 * f0 * t)
        poort = np.zeros(n)
        periode = 4.0 / chirps
        for c in range(chirps):
            for p in range(pulsen):
                s = int(((c + fase) * periode + p * 0.033) * SR) % n
                L = int(0.018 * SR)
                legg(poort, np.sin(np.pi * np.arange(L) / L) ** 2, s)
        x += sterk * draag * poort
    schrijf("krekels", x, 0.75)


# ---------------------------------------------------------------- dieren en natuur (one-shots)

def vogels():
    for i in range(6):
        noten = int(rng.integers(2, 7))
        delen = []
        for _ in range(noten):
            d = rng.uniform(0.04, 0.13)
            t = tijd(d)
            f_van, f_tot = rng.uniform(2200, 4200), rng.uniform(2600, 5200)
            if rng.random() < 0.4:
                f_van, f_tot = f_tot, f_van
            f = f_van + (f_tot - f_van) * (t / d) + rng.uniform(80, 300) * np.sin(2 * np.pi * rng.uniform(25, 60) * t)
            fase = 2 * np.pi * np.cumsum(f) / SR
            e = np.sin(np.pi * t / d) ** 1.5
            delen.append((np.sin(fase) + 0.15 * np.sin(2 * fase)) * e)
            delen.append(np.zeros(int(rng.uniform(0.02, 0.09) * SR)))
        schrijf("vogel_%d" % i, galm(np.concatenate(delen), 0.3, 0.12), 0.7)


def uil():
    for i, patroon in enumerate(((0.0, 0.45), (0.0, 0.25, 0.75, 0.95, 1.15))):
        x = np.zeros(int(2.2 * SR))
        for j, s in enumerate(patroon):
            d = 0.42 if j == 0 else 0.18
            f = 380 - 12 * j + rng.uniform(-5, 5)
            t = tijd(d)
            e = np.sin(np.pi * t / d) ** 2
            k = (np.sin(2 * np.pi * f * t) + 0.12 * np.sin(4 * np.pi * f * t)) * e
            k += 0.04 * band(rng.standard_normal(len(t)), 300, 1500) * e
            legg(x, k, int(s * SR), circulair=False)
        schrijf("uil_%d" % i, galm(x, 0.9, 0.35), 0.6)


def kip():
    for i in range(4):
        x = np.zeros(int(0.9 * SR))
        pos = 0.0
        for j in range(int(rng.integers(2, 5))):
            lang = j == 3 or (j > 0 and rng.random() < 0.2)
            d = rng.uniform(0.16, 0.24) if lang else rng.uniform(0.05, 0.08)
            t = tijd(d)
            f0 = rng.uniform(480, 650) * (1.0 + (0.25 if lang else -0.15) * t / d)
            fase = 2 * np.pi * np.cumsum(f0) / SR
            bron = sum(np.sin(k * fase) / k for k in range(1, 14))
            k = band(bron, 600, 2600, 2) * np.sin(np.pi * t / d) ** 0.6
            legg(x, k, int(pos * SR), circulair=False)
            pos += d + rng.uniform(0.05, 0.12)
        schrijf("tok_%d" % i, x[: int((pos + 0.05) * SR)], 0.7)


# ---------------------------------------------------------------- werk

def zaag():
    for i in range(2):
        delen = []
        for s in range(3):
            d = rng.uniform(0.28, 0.36)
            t = tijd(d)
            tanden = 0.5 + 0.5 * np.sin(2 * np.pi * (70 if s % 2 == 0 else 95) * t)
            k = band(rng.standard_normal(len(t)), 1800 if s % 2 == 0 else 2600, 7000) * tanden
            k *= np.sin(np.pi * t / d) ** 0.8
            delen += [k, np.zeros(int(0.04 * SR))]
        schrijf("zaag_%d" % i, np.concatenate(delen), 0.6)


def houweel():
    for i in range(3):
        L = int(0.28 * SR)
        t = np.arange(L) / SR
        dof = np.sin(2 * np.pi * rng.uniform(75, 110) * t) * omhul(L, 0.002, 0.05)
        aarde = band(rng.standard_normal(L), 250, 2500) * omhul(L, 0.001, rng.uniform(0.04, 0.08))
        kruim = band(rng.standard_normal(L), 2000, 6000) * omhul(L, 0.02, 0.06) * 0.3
        schrijf("houweel_%d" % i, dof + 0.8 * aarde + kruim, 0.7)


def sikkel():
    for i in range(3):
        d = rng.uniform(0.32, 0.42)
        L = int(d * SR)
        t = np.arange(L) / SR
        e = np.sin(np.pi * t / d) ** 2
        x = band(rng.standard_normal(L), 2500, 8000) * e
        x += 0.5 * band(rng.standard_normal(L), 900, 2500) * e ** 2
        for _ in range(12):                    # halmen die knappen
            l = int(0.004 * SR)
            legg(x, band(rng.standard_normal(l), 2000, 8000) * omhul(l, 0.0003, 0.001) * 0.8,
                 int(rng.uniform(0.3, 0.8) * L), circulair=False)
        schrijf("sikkel_%d" % i, x, 0.6)


# ---------------------------------------------------------------- interface en gebouwen

def klik():
    L = int(0.05 * SR)
    t = np.arange(L) / SR
    x = band(rng.standard_normal(L), 2000, 7000) * omhul(L, 0.0003, 0.003)
    x += 0.6 * np.sin(2 * np.pi * 1700 * t) * omhul(L, 0.0005, 0.012)
    schrijf("klik", x, 0.5)


def plaats():
    L = int(0.3 * SR)
    t = np.arange(L) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * omhul(L, 0.001, v) for f, a, v in ((170, 1.0, 0.09), (415, 0.6, 0.05), (980, 0.25, 0.02)))
    x += 0.5 * band(rng.standard_normal(L), 400, 4000) * omhul(L, 0.0005, 0.006)
    schrijf("plaats", x, 0.7)


def klaar():
    x = np.zeros(int(2.4 * SR))
    for j, f in enumerate((783.99, 1046.5, 1318.5)):    # G5 C6 E6
        bel = toon(f, 1.8, ((1, 1.0), (2.0, 0.35), (2.76, 0.25), (5.4, 0.08)), verval=0.55, aanzet=0.002)
        legg(x, bel, int(j * 0.13 * SR), circulair=False)
    schrijf("klaar", galm(x, 0.8, 0.3), 0.7)


def kraak(duur, f_van, f_tot):
    """Hek dat kraakt: stick-slip, een onregelmatige pulstrein met glijdende periode."""
    n = int(duur * SR)
    x = np.zeros(n)
    pos = 0.0
    while pos < duur:
        f = f_van + (f_tot - f_van) * pos / duur
        s = int(pos * SR)
        L = min(int(0.006 * SR), n - s)
        if L > 0:
            x[s:s + L] += rng.uniform(0.6, 1.0) * np.exp(-np.arange(L) / (0.0012 * SR))
        pos += (1.0 / f) * rng.uniform(0.8, 1.25)
    return band(x, 350, 3200) * np.sin(np.pi * np.arange(n) / n) ** 0.5


def klap(sterk):
    L = int(0.2 * SR)
    t = np.arange(L) / SR
    return sterk * (np.sin(2 * np.pi * 140 * t) * omhul(L, 0.001, 0.05) +
                    0.7 * band(rng.standard_normal(L), 300, 3500) * omhul(L, 0.0005, 0.015))


def poort():
    x = np.concatenate([kraak(0.7, 60, 150), np.zeros(int(0.05 * SR))])
    k = klap(0.5) * 0.6
    x = np.concatenate([x, k])
    schrijf("poort_open", x, 0.7)
    y = np.concatenate([kraak(0.45, 140, 80), klap(1.0)])
    schrijf("poort_dicht", y, 0.75)


def blaas(f, duur, helder=1.0, vib=0.0):
    t = tijd(duur)
    e = omhul(len(t), 0.03, duur * 0.9) * np.minimum(1.0, (duur - t) / 0.06)
    fase = 2 * np.pi * f * t + vib * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1.0, t / 0.3)
    x = sum(np.sin(k * fase) / k ** (1.4 - 0.4 * helder) for k in range(1, 14))
    return band(x, 150, 4200) * e


def fanfare():
    x = np.zeros(int(2.6 * SR))
    for s, f, d in ((0.0, 523.25, 0.16), (0.17, 659.25, 0.16), (0.34, 783.99, 0.16), (0.51, 1046.5, 1.2)):
        legg(x, blaas(f, d, 1.0, 1.2 if d > 1 else 0.0), int(s * SR), circulair=False)
        legg(x, 0.5 * blaas(f / 2, d, 0.6), int(s * SR), circulair=False)
    schrijf("missie_geslaagd", galm(x, 1.0, 0.3), 0.8)


def verloren():
    x = np.zeros(int(3.0 * SR))
    for s, f, d in ((0.0, 392.0, 0.35), (0.4, 369.99, 0.35), (0.8, 349.23, 0.35), (1.2, 329.63, 1.2)):
        legg(x, blaas(f, d, 0.4, 2.0 if d > 1 else 0.0), int(s * SR), circulair=False)
    schrijf("missie_verloren", galm(x, 1.0, 0.3), 0.75)


# ---------------------------------------------------------------- wolven, gevecht, leven (2026-10-31, missie 2 en 3)
# Achteraan de lijst in __main__: de rng loopt door, dus alles hierboven blijft byte voor byte gelijk.

def zaagtand(f, duur, ruw=0.0):
    """Zaagtand met glijdende f (array of getal) en ruwheid (AM-ruis): de basis van grom en jank."""
    n = int(duur * SR)
    f = np.broadcast_to(np.asarray(f, dtype=np.float64), (n,))
    f = f * (1.0 + ruw * band(rng.standard_normal(n), 20, 90))
    fase = 2 * np.pi * np.cumsum(f) / SR
    return sum(np.sin(k * fase) / k for k in range(1, 18))


def wolf():
    for i in range(2):                          # grom: laag, ruw, aanzwellend
        d = rng.uniform(0.9, 1.3)
        n = int(d * SR)
        t = np.arange(n) / SR
        f = rng.uniform(85, 110) * (1.0 + 0.08 * np.sin(np.pi * t / d))
        x = band(zaagtand(f, d, 0.35), 120, 1400) * np.sin(np.pi * t / d) ** 0.7
        x *= 0.6 + 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(16, 24) * t))   # ratel
        schrijf("wolf_grom_%d" % i, x, 0.75)
    for i in range(2):                          # hap: tanden die dichtklappen plus een korte grom
        x = np.zeros(int(0.5 * SR))
        L = int(0.03 * SR)
        legg(x, band(rng.standard_normal(L), 1500, 7000) * omhul(L, 0.0005, 0.005), int(0.02 * SR), circulair=False)
        legg(x, 0.7 * klap(1.0)[: int(0.12 * SR)], int(0.02 * SR), circulair=False)
        g = band(zaagtand(rng.uniform(120, 150), 0.32, 0.4), 150, 1600)
        legg(x, 0.6 * g * np.sin(np.pi * np.arange(len(g)) / len(g)), int(0.1 * SR), circulair=False)
        schrijf("wolf_hap_%d" % i, x, 0.8)
    d = 0.55                                    # jank: hoog, dalend (geraakt; lager afgespeeld = dood)
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-1.3 * t / d) + 380
    x = band(zaagtand(f, d, 0.08), 400, 4000) * omhul(n, 0.01, d * 0.5) * np.minimum(1.0, (d - t) / 0.05)
    schrijf("wolf_jank", galm(x, 0.5, 0.2), 0.7)


def zoef(duur, lo, hi):
    """Door de lucht: banddoorlaatruis die aanzwelt en wegsterft."""
    n = int(duur * SR)
    t = np.arange(n) / SR
    return band(rng.standard_normal(n), lo, hi, 2) * np.sin(np.pi * t / duur) ** 2


def gevecht():
    for i in range(2):
        schrijf("worp_%d" % i, zoef(rng.uniform(0.22, 0.3), 500, 2500), 0.5)
    for i in range(3):                          # steen op vacht of grond: dof plus een tik
        L = int(0.22 * SR)
        t = np.arange(L) / SR
        x = np.sin(2 * np.pi * rng.uniform(150, 220) * t) * omhul(L, 0.001, 0.035)
        x += 0.8 * band(rng.standard_normal(L), 800, 5000) * omhul(L, 0.0003, 0.008)
        schrijf("steen_%d" % i, x, 0.7)
    for i in range(2):                          # zwaard: zoef en een metalen klank (onharmonische partialen)
        x = np.zeros(int(0.9 * SR))
        legg(x, 0.6 * zoef(0.18, 1200, 6000), 0, circulair=False)
        f = rng.uniform(1300, 1700)
        legg(x, toon(f, 0.7, ((1, 1.0), (2.76, 0.5), (5.4, 0.25), (8.9, 0.1)), verval=0.12, aanzet=0.001),
             int(0.14 * SR), circulair=False)
        legg(x, 0.5 * band(rng.standard_normal(int(0.02 * SR)), 2000, 8000), int(0.14 * SR), circulair=False)
        schrijf("zwaard_%d" % i, x, 0.7)
    for i in range(2):                          # dorpeling geraakt: een doffe klap
        schrijf("raak_%d" % i, klap(1.0) * omhul(int(0.2 * SR), 0.001, 0.06), 0.7)
    n = int(2.2 * SR)                           # ontploffing (mijn): laag gerommel
    t = np.arange(n) / SR
    x = band(kleur_ruis(n, 1.0), 30, 900) * omhul(n, 0.004, 0.45)
    x += 0.6 * band(rng.standard_normal(n), 500, 5000) * omhul(n, 0.001, 0.05)
    schrijf("boem", x, 0.85)


def leven():
    x = np.zeros(int(3.5 * SR))                 # dood: een lage klok, twee slagen
    for s in (0.0, 1.4):
        legg(x, toon(196.0, 2.0, ((1, 1.0), (2.0, 0.4), (2.4, 0.3), (3.0, 0.2), (4.2, 0.1)), verval=0.7, aanzet=0.003),
             int(s * SR), circulair=False)
    schrijf("dood", galm(x, 1.0, 0.3), 0.6)
    L = int(0.18 * SR)                          # geboorte: plop
    t = np.arange(L) / SR
    f = 260 + 900 * t / 0.18
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * omhul(L, 0.002, 0.04)
    schrijf("plop", x, 0.7)
    for i in range(2):                          # water drinken: belletjes (stijgende sinusjes)
        x = np.zeros(int(0.8 * SR))
        for _ in range(9):
            d = rng.uniform(0.03, 0.07)
            n = int(d * SR)
            tt = np.arange(n) / SR
            f = rng.uniform(350, 700) * (1.0 + 1.2 * tt / d)
            k = np.sin(2 * np.pi * np.cumsum(f) / SR) * omhul(n, 0.002, d * 0.4)
            legg(x, k, int(rng.uniform(0.0, 0.7) * SR), circulair=False)
        x += 0.15 * band(rng.standard_normal(len(x)), 300, 3000) * np.sin(np.pi * np.arange(len(x)) / len(x))
        schrijf("water_%d" % i, x, 0.6)


if __name__ == "__main__":
    os.makedirs(UIT, exist_ok=True)
    for f in (wind, golven, vuur, regen, krekels, vogels, uil, kip, zaag, houweel, sikkel,
              klik, plaats, klaar, poort, fanfare, verloren, wolf, gevecht, leven):
        f()
    namen = sorted(os.listdir(UIT))
    print(len(namen), "bestanden in", UIT, ":", sum(os.path.getsize(os.path.join(UIT, n)) for n in namen) // 1024, "KB")
