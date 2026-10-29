"""Atlasindeling (gedeeld door kaarten.py en de bouwscripts). UV (u0, v0, u1, v1), v0 = voet van de kaart.
Elke cel beslaat in de studio 1 x 1 m (akker_blad 1 x 0,5 m), voet onderaan in het midden."""
I = 4 / 2048                      # inzet tegen doorbloeden
ATLAS = {"naald": (2048, 1024), "sneeuw": (1024, 512), "blad": (2048, 2048), "akker": (1024, 1536)}
CEL = {
    "den_tak": ("naald", (0 + I, 0 + 2 * I, 0.5 - I, 1 - 2 * I)),
    "spar_tak": ("naald", (0.5 + I, 0 + 2 * I, 1 - I, 1 - 2 * I)),
    "den_sneeuw": ("sneeuw", (0 + 2 * I, 0 + 4 * I, 0.5 - 2 * I, 1 - 4 * I)),
    "spar_sneeuw": ("sneeuw", (0.5 + 2 * I, 0 + 4 * I, 1 - 2 * I, 1 - 4 * I)),
    "blad_tros": ("blad", (0 + I, 0 + I, 0.5 - I, 0.5 - I)),
    "blad_fijn": ("blad", (0.5 + I, 0 + I, 1 - I, 0.5 - I)),
    "struik_blad": ("blad", (0 + I, 0.5 + I, 0.5 - I, 1 - I)),
    "bloemen": ("blad", (0.5 + I, 0.5 + I, 1 - I, 1 - I)),
    "tarwe": ("akker", (0 + I, 1 / 3 + I, 1 - I, 1 - I)),
    "akker_blad": ("akker", (0 + I, 0 + I, 1 - I, 1 / 3 - I)),
}


def sub(naam, a, b, c, d):
    """Deelvak binnen een cel (fracties van de cel)."""
    u0, v0, u1, v1 = CEL[naam][1]
    return (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b, u0 + (u1 - u0) * c, v0 + (v1 - v0) * d)
