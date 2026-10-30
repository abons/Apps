"""Hulpmiddelen om een eigen mesh naar een zijaanzicht-referentie te vervormen en dat beeld erop te projecteren
(wolf_tripo.py). Alleen numpy, ook buiten Blender bruikbaar.

- `segmenteer(rgb)`: dier los van een gladde (blauwgrijze) studio-achtergrond: achtergrond als veelterm in x, y
  gefit op koele pixels, dier = afwijking of warm, grootste component, gaten dicht.
- `raster_masker(P2, T, H, W)`: silhouet van driehoeken (pixelcoordinaten).
- `contour(m)` (Moore, met de klok mee in beeldcoordinaten) en `herbemonster(c, stap)`.
- `tps_fit` / `tps_pas`: thin-plate spline 2D -> 2D; `tps_jac`: determinant (vouwcontrole).
- `paren(cs, cd, ankers)`: punten langs twee contouren tussen ankerparen, op gelijke boogfractie.
- `uitbreiden(rgb, m)`: kleur van het dier naar buiten uitsmeren (bemonsteren net naast de rand).
"""
from collections import deque

import numpy as np


def segmenteer(a, drempel=14.0):
    a = np.asarray(a, float)
    if a.max() <= 1.0:
        a = a * 255.0
    H, W, _ = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    u, v = xx / W - 0.5, yy / H - 0.5
    X = np.stack([np.ones_like(u), u, v, u * u, v * v, u * v, u ** 3, v ** 3, u * u * v, u * v * v], -1).reshape(-1, 10)
    bt = (a[..., 2] - a[..., 0] >= 2.5).reshape(-1)
    for _ in range(3):
        co, *_ = np.linalg.lstsq(X[bt], a.reshape(-1, 3)[bt], rcond=None)
        bg = (X @ co).reshape(H, W, 3)
        d = np.abs(a - bg).sum(-1)
        bt = ((d < 8) & (a[..., 2] - a[..., 0] >= 1)).reshape(-1)
    m = (d > drempel) | (a[..., 0] - a[..., 2] > -1.0)
    m = grootste(m)
    return ~grootste(~m, rand=True)


def grootste(m, rand=False):
    """Grootste 4-samenhangende component (rand=True: alles wat de beeldrand raakt)."""
    H, W = m.shape
    lab = np.zeros((H, W), np.int32)
    n, best, beste = 0, 0, 0
    starts = ([(r, c) for r in range(H) for c in (0, W - 1)] + [(r, c) for c in range(W) for r in (0, H - 1)]) if rand \
        else zip(*np.nonzero(m))
    uit = np.zeros((H, W), bool)
    for r, c in starts:
        if not m[r, c] or lab[r, c]:
            continue
        n += 1
        q = deque([(r, c)])
        lab[r, c] = n
        s = 0
        while q:
            y, x = q.popleft()
            s += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                Y, X_ = y + dy, x + dx
                if 0 <= Y < H and 0 <= X_ < W and m[Y, X_] and not lab[Y, X_]:
                    lab[Y, X_] = n
                    q.append((Y, X_))
        if rand:
            uit |= False
        elif s > beste:
            beste, best = s, n
    if rand:
        return lab > 0
    return lab == best


def raster_masker(P2, T, H, W):
    m = np.zeros((H, W), bool)
    for a, b, c in T:
        xs = np.array([P2[a, 0], P2[b, 0], P2[c, 0]])
        ys = np.array([P2[a, 1], P2[b, 1], P2[c, 1]])
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        k = (l0 >= -1e-3) & (l1 >= -1e-3) & (1 - l0 - l1 >= -1e-3)
        m[(gy[k] - 0.5).astype(int), (gx[k] - 0.5).astype(int)] = True
    return m


def contour(m):
    H, W = m.shape
    mm = np.zeros((H + 2, W + 2), bool)
    mm[1:-1, 1:-1] = m
    ys, xs = np.nonzero(mm)
    i = np.lexsort((xs, ys))[0]
    start = (ys[i], xs[i])
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    c, b, uit = start, (start[0], start[1] - 1), [start]
    while len(uit) < 200000:
        k = nb.index((b[0] - c[0], b[1] - c[1]))
        for j in range(1, 9):
            d = nb[(k + j) % 8]
            p = (c[0] + d[0], c[1] + d[1])
            if mm[p]:
                pb = nb[(k + j - 1) % 8]
                b, c = (c[0] + pb[0], c[1] + pb[1]), p
                break
        if c == start:
            break
        uit.append(c)
    return (np.array(uit)[:, ::-1] - 1).astype(float)


def herbemonster(c, stap=2.0):
    cc = np.r_[c, c[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]
    s = np.arange(0, d[-1], stap)
    return np.stack([np.interp(s, d, cc[:, 0]), np.interp(s, d, cc[:, 1])], 1)


def _U(r2):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.nan_to_num(0.5 * r2 * np.log(r2))


def tps_fit(src, dst, lam=0.5):
    n = len(src)
    s, sc = src.mean(0), src.std()
    A = (src - s) / sc
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = _U(((A[:, None] - A[None]) ** 2).sum(-1)) + lam * np.eye(n)
    Pm = np.c_[np.ones(n), A]
    L[:n, n:], L[n:, :n] = Pm, Pm.T
    Y = np.zeros((n + 3, 2))
    Y[:n] = dst
    return A, np.linalg.solve(L, Y), s, sc


def tps_pas(t, X):
    A, W, s, sc = t
    B = (np.asarray(X, float) - s) / sc
    uit = np.zeros((len(B), 2))
    for i in range(0, len(B), 4000):
        b = B[i:i + 4000]
        uit[i:i + 4000] = _U(((b[:, None] - A[None]) ** 2).sum(-1)) @ W[:len(A)] + np.c_[np.ones(len(b)), b] @ W[len(A):]
    return uit


def tps_jac(t, X, h=0.5):
    X = np.asarray(X, float)
    fx = (tps_pas(t, X + [h, 0]) - tps_pas(t, X - [h, 0])) / (2 * h)
    fy = (tps_pas(t, X + [0, h]) - tps_pas(t, X - [0, h])) / (2 * h)
    return fx[:, 0] * fy[:, 1] - fx[:, 1] * fy[:, 0]


def dichtst(c, p):
    return int(np.argmin(np.linalg.norm(c - np.asarray(p, float), axis=1)))


def paren(cs, cd, ankers):
    """ankers: [(i_src, i_dst)] in contourvolgorde van de bron; tussenpunten op gelijke fractie."""
    ns, nd = len(cs), len(cd)
    S, D = [], []

    def ip(c, i):
        i0 = int(np.floor(i)) % len(c)
        f = i - np.floor(i)
        return c[i0] * (1 - f) + c[(i0 + 1) % len(c)] * f
    for k in range(len(ankers)):
        a0, b0 = ankers[k]
        a1, b1 = ankers[(k + 1) % len(ankers)]
        la, lb = (a1 - a0) % ns, (b1 - b0) % nd
        m = max(2, int(max(la, lb) / 3))
        for j in range(m):
            S.append(ip(cs, a0 + j / m * la))
            D.append(ip(cd, b0 + j / m * lb))
    return np.array(S), np.array(D)


def uitbreiden(rgb, m, stappen=40):
    """Kleur van de pixels in m stap voor stap naar de buren buiten m (gemiddelde van de gezette buren)."""
    rgb = np.array(rgb, np.float32)
    m = m.copy()
    for _ in range(stappen):
        acc = np.zeros_like(rgb)
        n = np.zeros(m.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb * m[..., None], dy, 0), dx, 1)
            n += mm
        nieuw = (~m) & (n > 0)
        if not nieuw.any():
            break
        rgb[nieuw] = acc[nieuw] / n[nieuw][:, None]
        m = m | nieuw
    return rgb, m


def bilineair(img, x, y):
    H, W = img.shape[:2]
    x = np.clip(x - 0.5, 0, W - 1.001)
    y = np.clip(y - 0.5, 0, H - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
