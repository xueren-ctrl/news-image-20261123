#!/usr/bin/env python3
"""Draw the front page of 'The Day in One Picture' for Monday 23 November 2026.

Pure Python standard library (os, struct, zlib). No network, no fonts from
disk, no image libraries: every letter comes from a 5x7 bitmap alphabet
defined in this file, every picture, chart and map is drawn from shapes, and
the PNG bytes are encoded by hand. Running this program writes one
deterministic 1024x1024 image to $MAKEFUN_OUTPUT_DIR/entry.png (or
/output/entry.png, or ./out/entry.png when neither exists).

The news on the page was researched and verified in the build session: every
story happened, or was first reported, on Monday 23 November 2026. Bigger
stories from 19-22 November are listed in the DATE CHECK footer as
deliberately left out.
"""

import os
import struct
import zlib

PAGE = 1024

# ---- palette -------------------------------------------------------------
PAPER = (247, 243, 230)   # warm newsprint
INK = (24, 24, 24)        # near-black ink
RED = (178, 38, 28)       # headline accent
BLUE = (28, 74, 120)      # second accent
GREY = (105, 105, 105)    # muted text
PANEL = (234, 228, 210)   # light panel
SEA = (211, 225, 233)     # sea on the map
LAND = (198, 209, 184)    # land on the map
WHITE = (255, 255, 255)
GOLD = (186, 136, 12)
GREEN = (28, 120, 66)
SKY = (168, 205, 226)
NAVY = (18, 42, 68)
SAND = (226, 205, 160)

# ---- canvas --------------------------------------------------------------
buf = bytearray(PAGE * PAGE * 3)
for _r in range(PAGE):
    buf[_r * PAGE * 3:(_r + 1) * PAGE * 3] = bytes(PAPER) * PAGE


def px(x, y, c):
    if 0 <= x < PAGE and 0 <= y < PAGE:
        i = (y * PAGE + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def box(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(PAGE, x + w)
    y1 = min(PAGE, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    span = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * PAGE + x0) * 3
        buf[i:i + len(span)] = span


def hrule(x, y, w, c, t=1):
    box(x, y, w, t, c)


def vrule(x, y, h, c, t=1):
    box(x, y, t, h, c)


def outline(x, y, w, h, c, t=1):
    hrule(x, y, w, c, t)
    hrule(x, y + h - t, w, c, t)
    vrule(x, y, h, c, t)
    vrule(x + w - t, y, h, c, t)


def line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square thickness."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        box(x0 - t // 2, y0 - t // 2, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                px(xx, yy, c)


def ring(cx, cy, r, c, t=2):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d <= (r + t) ** 2:
                px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    """Filled triangle via scanline."""
    pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    for y in range(ay, cy + 1):
        if by != ay and y <= by:
            xa = ax + (bx - ax) * (y - ay) / max(1, by - ay)
        else:
            xa = bx + (cx - bx) * (y - by) / max(1, cy - by)
        xb = ax + (cx - ax) * (y - ay) / max(1, cy - ay)
        x_lo, x_hi = int(min(xa, xb)), int(max(xa, xb))
        for x in range(x_lo, x_hi + 1):
            px(x, y, c)


def star(cx, cy, r, c):
    """Five-point star, outer radius r."""
    import math
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + int(rr * math.cos(ang)), cy + int(rr * math.sin(ang))))
    for k in range(1, 9, 2):
        tri(pts[0][0], pts[0][1], pts[k][0], pts[k][1],
            pts[(k + 1) % 10][0], pts[(k + 1) % 10][1], c)
    tri(pts[0][0], pts[0][1], pts[8][0], pts[8][1], pts[9][0], pts[9][1], c)


# ---- PNG encoder ---------------------------------------------------------
def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def write_png(path, w, h, fb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += fb[y * w * 3:(y + 1) * w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---- 5x7 bitmap font -----------------------------------------------------
# Each glyph is 7 rows; each row is a 5-bit value, bit 4 = leftmost column.
FONT = {
    ' ': (0, 0, 0, 0, 0, 0, 0),
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    'a': (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    'b': (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x1E),
    'c': (0x00, 0x00, 0x0E, 0x10, 0x10, 0x10, 0x0E),
    'd': (0x01, 0x01, 0x0D, 0x13, 0x11, 0x11, 0x0F),
    'e': (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    'f': (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    'g': (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'h': (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x11),
    'i': (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    'j': (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    'k': (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    'l': (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'm': (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    'n': (0x00, 0x00, 0x16, 0x19, 0x11, 0x11, 0x11),
    'o': (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    'p': (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
    'q': (0x00, 0x00, 0x0D, 0x13, 0x0F, 0x01, 0x01),
    'r': (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    's': (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    't': (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    'u': (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    'v': (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'w': (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    'x': (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    'y': (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'z': (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '-': (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '@': (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '_': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    '~': (0x00, 0x00, 0x0A, 0x15, 0x00, 0x00, 0x00),
    '^': (0x04, 0x0A, 0x11, 0x00, 0x00, 0x00, 0x00),
}

# Normalise curly punctuation to the ASCII glyphs we have.
NORMALISE = {
    '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
    '\u2013': '-', '\u2014': '-', '\u00b7': '.', '\u2022': '*',
    '\u00d7': 'x', '\u2192': '>', '\u2191': '^', '\u2713': 'v',
    '\u00e9': 'e', '\u00e8': 'e', '\u00fc': 'u', '\u00f6': 'o',
}


def glyph(ch):
    ch = NORMALISE.get(ch, ch)
    return FONT.get(ch, FONT['?'])


def char_advance(scale, bold):
    return 6 * scale + (1 if bold else 0)


def text_w(s, scale, bold=False):
    return len(s) * char_advance(scale, bold) - (scale if s else 0)


def draw_glyph(x, y, ch, scale, c, bold=False):
    rows = glyph(ch)
    off = max(1, scale // 3) if bold else 0
    for ry in range(7):
        bits = rows[ry]
        for cx in range(5):
            if bits & (1 << (4 - cx)):
                box(x + cx * scale, y + ry * scale, scale, scale, c)
                if off:
                    box(x + cx * scale + off, y + ry * scale, scale, scale, c)


def draw_text(x, y, s, scale, c, bold=False):
    for ch in s:
        draw_glyph(x, y, ch, scale, c, bold)
        x += char_advance(scale, bold)
    return x


def wrap(s, max_w, scale, bold=False):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    adv = char_advance(scale, bold)
    words = s.split(' ')
    lines = []
    cur = ''
    for w in words:
        trial = (cur + ' ' + w) if cur else w
        if len(trial) * adv - scale <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # hard-split a word that is too long on its own
            while len(w) * adv - scale > max_w:
                take = max(1, (max_w + scale) // adv)
                lines.append(w[:take])
                w = w[take:]
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, max_w, scale, c, bold=False, line_gap=2):
    lines = wrap(s, max_w, scale, bold)
    for ln in lines:
        draw_text(x, y, ln, scale, c, bold)
        y += 7 * scale + line_gap
    return y

# ---- world map -----------------------------------------------------------
# Stylised land patches as rectangles in a 300x200 map frame.
LAND_PATCHES = [
    # North America
    (12, 6, 70, 26), (18, 30, 70, 22), (28, 50, 30, 18), (52, 64, 10, 14),
    # Greenland
    (96, 4, 18, 14),
    # South America
    (84, 96, 36, 22), (88, 116, 28, 30), (94, 144, 18, 30), (98, 172, 10, 18),
    # Europe
    (142, 10, 40, 20), (146, 28, 30, 16), (150, 42, 22, 12), (140, 16, 8, 12),
    # Africa
    (136, 60, 56, 28), (140, 86, 48, 30), (146, 114, 36, 28), (152, 140, 24, 20),
    (196, 138, 6, 18),
    # Asia
    (184, 4, 116, 30), (190, 32, 100, 26), (210, 56, 60, 26), (222, 80, 22, 26),
    (246, 80, 30, 20), (262, 60, 26, 18), (282, 44, 10, 28), (240, 104, 50, 8),
    # Australia + NZ
    (244, 128, 34, 22), (248, 148, 26, 16), (286, 172, 8, 18),
]

# (number, map-x, map-y, label, label-dx, label-dy)
PINS = [
    (1, 154, 36, "BRUSSELS", -34, -14),
    (2, 49, 56, "SANTA CLARA", -30, 10),
    (3, 179, 64, "GAZA", 10, -6),
    (4, 289, 135, "VANUATU", -58, 8),
    (5, 238, 120, "SERANG", 10, -4),
    (6, 221, 70, "KATHMANDU", -66, -16),
    (7, 196, 74, "DUBAI", -14, 12),
    (8, 234, 91, "BANGKOK", 10, 8),
]


def draw_map(mx, my, mw, mh):
    box(mx, my, mw, mh, SEA)
    for (px0, py0, pw, ph) in LAND_PATCHES:
        box(mx + px0, my + py0, pw, ph, LAND)
    # graticule hint
    for gx in range(mx + 50, mx + mw, 50):
        vrule(gx, my, mh, (190, 205, 214), 1)
    for gy in range(my + 40, my + mh, 40):
        hrule(mx, gy, mw, (190, 205, 214), 1)
    outline(mx, my, mw, mh, INK, 2)
    for (num, lx, ly, label, ldx, ldy) in PINS:
        disc(mx + lx, my + ly, 7, RED)
        ring(mx + lx, my + ly, 7, WHITE, 1)
        draw_text(mx + lx - 3, my + ly - 3, str(num), 1, WHITE, bold=True)
        draw_text(mx + lx + ldx, my + ly + ldy, label, 1, INK, bold=True)


# ---- illustrations -------------------------------------------------------
def pic_chip_chart(x, y, w, h):
    """Nvidia lead: a processor with a rising chart."""
    box(x, y, w, h, NAVY)
    # rising chart (ends before the chip)
    pts = [(x + 14, y + h - 22), (x + 55, y + h - 40), (x + 95, y + h - 30),
           (x + 140, y + h - 52), (x + 185, y + h - 62)]
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], (60, 220, 120), 4)
    line(pts[-1][0], pts[-1][1], pts[-1][0] + 16, pts[-1][1] - 4, (60, 220, 120), 4)
    line(pts[-1][0], pts[-1][1], pts[-1][0] + 4, pts[-1][1] + 14, (60, 220, 120), 4)
    # chip
    cx, cy = x + w - 78, y + h - 58
    box(cx - 30, cy - 22, 60, 44, (30, 60, 92))
    outline(cx - 30, cy - 22, 60, 44, (120, 180, 230), 2)
    box(cx - 26, cy - 14, 52, 28, (60, 220, 120))
    draw_text(cx - 25, cy - 8, "+31%", 2, INK, bold=True)
    for k in range(5):
        vrule(cx - 26 + k * 12, cy - 30, 8, (120, 180, 230), 2)
        vrule(cx - 26 + k * 12, cy + 22, 8, (120, 180, 230), 2)
    # caption tag
    box(x + 10, y + 8, 118, 16, RED)
    draw_text(x + 16, y + 11, "SHARES +31%", 1, WHITE, bold=True)


def pic_eu_flag(x, y, w, h):
    """EU sanctions lead: circle of stars + bank with a ban ring."""
    box(x, y, w, h, (24, 58, 112))
    cx, cy = x + 92, y + h // 2
    import math
    for k in range(12):
        ang = -math.pi / 2 + k * math.pi / 6
        star(cx + int(52 * math.cos(ang)), cy + int(38 * math.sin(ang)), 7, GOLD)
    # bank
    bx, by = x + w - 108, y + h - 62
    box(bx, by + 8, 84, 34, WHITE)
    for k in range(4):
        box(bx + 8 + k * 20, by + 14, 10, 24, (24, 58, 112))
    tri(bx - 4, by + 8, bx + 42, by - 12, bx + 88, by + 8, WHITE)
    ring(bx + 42, by + 16, 30, RED, 5)
    line(bx + 21, by + 37, bx + 63, by - 5, RED, 5)
    box(x + 10, y + 8, 132, 16, RED)
    draw_text(x + 16, y + 11, "22ND PACKAGE", 1, WHITE, bold=True)


def pic_well(x, y, w, h):
    """Gaza lead: a water well, pump and drop, dusk skyline."""
    box(x, y, w, h, SAND)
    # skyline
    box(x + 12, y + h - 52, 46, 52, (120, 96, 74))
    box(x + 66, y + h - 68, 40, 68, (96, 76, 58))
    box(x + 114, y + h - 44, 52, 44, (140, 116, 90))
    for bx in (x + 22, x + 76, x + 126):
        for wy in range(y + h - 44, y + h - 8, 12):
            box(bx, wy, 8, 7, (247, 243, 230))
    # smoke
    disc(x + 86, y + 18, 10, (150, 150, 150))
    disc(x + 100, y + 10, 12, (170, 170, 170))
    disc(x + 116, y + 20, 9, (150, 150, 150))
    # water pump + drop
    wx, wy = x + w - 76, y + h - 58
    box(wx, wy, 10, 58, (28, 74, 120))
    box(wx, wy, 34, 10, (28, 74, 120))
    box(wx + 24, wy + 10, 8, 14, (28, 74, 120))
    disc(wx + 28, wy + 34, 7, (40, 130, 200))
    tri(wx + 22, wy + 34, wx + 34, wy + 34, wx + 28, wy + 22, (40, 130, 200))
    box(x + 10, y + 8, 128, 16, RED)
    draw_text(x + 16, y + 11, "3 KILLED IN GAZA", 1, WHITE, bold=True)


def pic_shield(x, y, w, h, c1, c2):
    box(x, y, w, h, PANEL)
    cx, cy = x + w // 2, y + h // 2
    tri(cx - 26, cy - 16, cx + 26, cy - 16, cx, cy + 24, c1)
    box(cx - 26, cy - 16, 52, 16, c1)
    disc(cx, cy - 2, 8, WHITE)
    line(cx - 5, cy - 2, cx - 1, cy + 3, c2, 2)
    line(cx - 1, cy + 3, cx + 6, cy - 7, c2, 2)


def pic_quake(x, y, w, h):
    box(x, y, w, h, SKY)
    tri(x + 20, y + h - 8, x + 60, y + 10, x + 100, y + h - 8, (96, 110, 90))
    tri(x + 80, y + h - 8, x + 120, y + 22, x + 160, y + h - 8, (120, 130, 110))
    for yy, amp in ((y + 14, 6), (y + 24, 9), (y + 34, 6)):
        line(x + 8, yy, x + w - 8, yy, RED, 2)
        for kx in range(0, w - 16, 12):
            line(x + 8 + kx, yy, x + 14 + kx, yy - amp, RED, 2)
            line(x + 14 + kx, yy - amp, x + 20 + kx, yy, RED, 2)


def pic_factory(x, y, w, h):
    box(x, y, w, h, (232, 214, 180))
    box(x + 20, y + h - 40, 70, 40, (120, 110, 100))
    box(x + 96, y + h - 52, 46, 52, (120, 110, 100))
    box(x + 150, y + 12, 14, 58, (90, 84, 76))
    tri(x + 148, y + 6, x + 166, y + 6, x + 157, y - 6, (230, 120, 30))
    disc(x + 157, y + 14, 8, (230, 120, 30))
    disc(x + 168, y + 8, 6, (240, 160, 40))
    for wx in range(x + 30, x + 82, 16):
        box(wx, y + h - 32, 8, 8, (247, 243, 230))


def pic_mountains(x, y, w, h):
    box(x, y, w, h, SKY)
    tri(x + 10, y + h - 6, x + 55, y + 8, x + 100, y + h - 6, (90, 120, 160))
    tri(x + 70, y + h - 6, x + 120, y + 20, x + 170, y + h - 6, (120, 140, 180))
    disc(x + 150, y + 16, 12, GOLD)
    box(x + 20, y + h - 26, 150, 8, (60, 100, 60))


def pic_gavel(x, y, w, h):
    box(x, y, w, h, PANEL)
    cx, cy = x + w // 2, y + h // 2
    line(cx - 34, cy + 16, cx + 34, cy - 16, (120, 84, 40), 6)
    box(cx - 44, cy - 2, 22, 12, (120, 84, 40))
    box(cx + 22, cy - 26, 22, 12, (120, 84, 40))
    box(cx - 30, cy + 22, 60, 6, (80, 60, 30))


def pic_scales(x, y, w, h):
    box(x, y, w, h, PANEL)
    cx, cy = x + w // 2, y + h // 2
    vrule(cx, cy - 20, 40, INK, 3)
    hrule(cx - 30, cy - 20, 60, INK, 3)
    line(cx - 30, cy - 20, cx - 44, cy + 6, INK, 2)
    line(cx + 30, cy - 20, cx + 44, cy + 6, INK, 2)
    tri(cx - 56, cy + 6, cx - 32, cy + 6, cx - 44, cy + 20, GOLD)
    tri(cx + 32, cy + 6, cx + 56, cy + 6, cx + 44, cy + 20, GOLD)
    box(cx - 26, cy + 20, 52, 5, INK)


def pic_ballot(x, y, w, h):
    box(x, y, w, h, PANEL)
    cx, cy = x + w // 2, y + h // 2
    box(cx - 34, cy - 6, 68, 34, BLUE)
    box(cx - 12, cy - 14, 24, 8, WHITE)
    box(cx - 40, cy - 26, 34, 20, WHITE)
    outline(cx - 40, cy - 26, 34, 20, INK, 1)
    line(cx - 36, cy - 16, cx - 30, cy - 8, RED, 2)
    line(cx - 30, cy - 8, cx - 18, cy - 22, RED, 2)


def pic_chart(x, y, w, h, up=True):
    box(x, y, w, h, PANEL)
    pts = [(x + 12, y + h - 16), (x + 48, y + h - 30), (x + 84, y + h - 22),
           (x + 120, y + h - 40), (x + 156, y + h - 48)]
    if not up:
        pts = [(a, y + h - (b - y)) for a, b in pts]
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], GREEN if up else RED, 3)
    line(pts[-1][0], pts[-1][1], pts[-1][0] + 12, pts[-1][1] - 3, GREEN if up else RED, 3)
    line(pts[-1][0], pts[-1][1], pts[-1][0] + 3, pts[-1][1] + 10, GREEN if up else RED, 3)


def pic_runner(x, y, w, h):
    box(x, y, w, h, (240, 220, 190))
    box(x, y + h - 14, w, 14, (90, 90, 90))
    cx, cy = x + w // 2, y + h // 2 - 4
    disc(cx, cy - 22, 8, INK)
    line(cx, cy - 14, cx + 6, cy + 2, INK, 4)
    line(cx + 6, cy + 2, cx + 22, cy + 12, INK, 3)
    line(cx + 6, cy + 2, cx - 8, cy + 16, INK, 3)
    line(cx, cy - 10, cx - 18, cy - 2, INK, 3)
    line(cx, cy - 10, cx + 20, cy - 16, INK, 3)
    disc(x + 20, y + 14, 10, GOLD)


def pic_warning(x, y, w, h):
    box(x, y, w, h, PANEL)
    cx, cy = x + w // 2, y + h // 2
    tri(cx - 34, cy + 20, cx + 34, cy + 20, cx, cy - 22, (240, 180, 20))
    outline(cx - 34, cy + 20, 68, 2, INK, 1)
    box(cx - 2, cy - 8, 4, 16, INK)
    disc(cx, cy + 12, 3, INK)

# ---- story data (all verified 23 November 2026) --------------------------
# (number, kicker, headline, body, source, tag)
LEADS = [
    (1, "BUSINESS - SANTA CLARA", "Huang is back: Nvidia reinstates its chief",
     "Nvidia's board reinstates Jensen Huang as CEO, 11 days after he quit "
     "over affairs with an alleged Chinese spy. Trump pressed for his return; "
     "shares jump 31% and the Nasdaq rallies 6%.",
     "Reuters - WSJ - CNN", "CONFIRMED"),
    (2, "EUROPE - BRUSSELS", "EU unveils 22nd sanctions package on Russia",
     "Brussels proposes its 22nd package on Russia: 60 banks cut from SWIFT, "
     "a crypto crackdown, 70+ shadow-fleet ships listed, and Russian teams "
     "barred from flying their flag at EU sports events.",
     "Reuters - European Commission", "CONFIRMED"),
    (3, "MIDDLE EAST - GAZA", "Israeli strikes kill UN aid worker in Gaza",
     "Israeli strikes kill at least three in Gaza on Monday, including UNRWA "
     "worker Adel Al-Helo at a water well in Jabalia; a later strike on a "
     "vehicle in Gaza City kills two more.",
     "Arab News - Reuters", "CONFIRMED"),
]

# (number, kicker, headline, body, source, tag, picture)
SECONDARIES = [
    (4, "BUSINESS", "CrowdStrike buys Zscaler",
     "All-stock $43.9bn deal, the biggest cyber takeover ever; shares fall 9%.",
     "Reuters - WSJ", "CONFIRMED", "shield"),
    (5, "SCIENCE", "M6.5 quake shakes Vanuatu",
     "A magnitude 6.5 quake strikes 600 km deep at 02:40 UTC; no damage, no tsunami.",
     "USGS", "OFFICIAL", "quake"),
    (6, "ASIA", "24 dead in factory fire",
     "Jakarta confirms 24 killed in Saturday's candy-factory blaze; about 30 missing.",
     "Reuters", "CONFIRMED", "factory"),
    (7, "ASIA", "India gives Nepal $1.62bn",
     "New Delhi pledges 240bn rupees to flood-hit Nepal.",
     "Reuters", "CONFIRMED", "mountains"),
    (8, "ASIA", "Dhaka: Hasina will be jailed",
     "Bangladesh says the ex-PM will be arrested and jailed if she comes back.",
     "Reuters", "CONFIRMED", "gavel"),
    (9, "LAW", "Thai court halves term",
     "An appeal court cuts a lawmaker's sentence for royal insult.",
     "BusinessWorld", "REPORTED", "scales"),
    (10, "ASIA", "Indonesia names VP picks",
     "The president nominates vice-presidential candidates on Monday.",
     "BusinessWorld", "REPORTED", "ballot"),
    (11, "MARKETS", "Nasdaq up 6% on AI rally",
     "US stocks rebound from Friday's slide as Huang's return revives the AI trade.",
     "Reuters", "CONFIRMED", "chart"),
    (12, "SPORT", "310,000 at Dubai Run",
     "A record crowd takes over Sheikh Zayed Road for the annual run.",
     "Gulf News", "REPORTED", "runner"),
    (13, "MIDDLE EAST", "Two killed in Taiz attacks",
     "Two civilians killed and eight hurt in Houthi attacks in Yemen's Taiz.",
     "SABA - local forces", "REPORTED", "warning"),
]

ALSO_ON = [
    "EU: 60 banks to be cut from SWIFT",
    "EU: 70+ shadow-fleet ships listed",
    "EU: Russian flag banned at EU sport",
    "EU: visa ban for Russian ex-combatants",
    "EU: crypto task force created",
    "EU: Europeans barred from Russian boards",
    "Nvidia +31%, best day in 23 years",
    "Nvidia: 180,000 signed petition for return",
    "Nvidia: SEC probe into disclosures goes on",
    "Trump calls Huang a 'national treasure'",
    "SK hynix +20% as chip stocks rally",
    "CrowdStrike -9% on deal news; $1bn savings",
    "STOXX 600 +1.5% as tech leads Europe",
    "Gargash warns of power struggle over Iran",
    "US Army to detonate lead in Iowa",
    "UN chief urges AI safety rules in a year",
    "Moscow nuclear satellite plan, media claim",
    "Finland MPs back anti-tank barriers",
    "Libya parliament moves to unify government",
    "China agrees new AI dialogue mechanism",
    "Eleven Kurds arrested in Iran's Ilam region",
    "Dubai Metro Blue Line work under way",
]

TIMELINE = [
    ("02:40", "Vanuatu M6.5 quake"),
    ("09:00", "EU unveils sanctions"),
    ("13:00", "CrowdStrike deal"),
    ("13:30", "Huang reinstated"),
    ("15:37", "EU sanctions text out"),
    ("21:00", "Nasdaq closes +6%"),
]

DATE_CHECK = ("Left out on purpose, first reported before Monday: the COP31 "
    "collapse (Sun 22), the Merkury sinking off Libya (Sun 22), Skubal's "
    "$450m Mets deal (Sun 22), South Korea's minister quitting (Sun 22), "
    "El Chapo Isidro's capture (Sat 21), the EU-Indonesia trade pact "
    "(Sat 21), the candy-factory fire breaking out (Sat 21), the FBI "
    "database hack (Fri 20), the ICJ Myanmar ruling (Thu 19), the "
    "Trump-Xi-Putin summit (Thu 19).")

TAG_COLOURS = {"CONFIRMED": GREEN, "OFFICIAL": BLUE, "REPORTED": GOLD}


def tag_chip(x, y, tag):
    w = len(tag) * 7 + 8
    box(x, y, w, 13, TAG_COLOURS[tag])
    draw_text(x + 4, y + 3, tag, 1, WHITE, bold=True)
    return w


# ---- page layout ---------------------------------------------------------
MX = 16          # side margin
CW = 992         # content width


def build_page():
    # top kicker
    draw_text(MX, 8, "ONE DAY OF WORLD NEWS, ONE PICTURE", 1, RED, bold=True)
    right = "35 STORIES - 5 REGIONS - 12 FIELDS - ALL FROM THIS MONDAY"
    draw_text(MX + CW - text_w(right, 1, True), 8, right, 1, INK, bold=True)

    # masthead
    mast = "Monday 23 November 2026"
    draw_text((PAGE - text_w(mast, 7)) // 2, 22, mast, 7, INK)
    hrule(MX, 78, CW, INK, 2)

    # black ticker bar with the three lead teasers
    box(MX, 84, CW, 22, INK)
    tick = "HUANG IS BACK AT NVIDIA  *  EU UNVEILS 22ND SANCTIONS  *  ISRAELI STRIKES KILL UN AID WORKER IN GAZA"
    draw_text((PAGE - text_w(tick, 1, True)) // 2, 91, tick, 1, WHITE, bold=True)

    # THE DAY IN UTC timeline
    ty = 112
    box(MX, ty, 104, 30, RED)
    draw_text(MX + 6, ty + 5, "THE DAY", 1, WHITE, bold=True)
    draw_text(MX + 6, ty + 15, "IN UTC", 1, WHITE, bold=True)
    slot_x = MX + 112
    slot_w = (CW - 112) // 6
    for (t, label) in TIMELINE:
        draw_text(slot_x + 6, ty + 2, t, 2, RED, bold=True)
        draw_para(slot_x + 6, ty + 18, label, slot_w - 12, 1, INK)
        vrule(slot_x, ty, 30, GREY, 1)
        slot_x += slot_w
    hrule(MX, ty + 32, CW, INK, 1)

    # ---- three lead stories ----
    lead_y = 150
    lead_w = 322
    lead_xs = [MX, MX + lead_w + 13, MX + 2 * (lead_w + 13)]
    lead_pics = [pic_chip_chart, pic_eu_flag, pic_well]
    for (num, kicker, head, body, src, tag), lx, pic in zip(LEADS, lead_xs, lead_pics):
        pic(lx, lead_y, lead_w, 88)
        ky = lead_y + 94
        draw_text(lx, ky, str(num) + "  " + kicker, 1, RED, bold=True)
        tag_chip(lx + lead_w - (len(tag) * 7 + 8), ky - 3, tag)
        hy = ky + 12
        by = draw_para(lx, hy, head, lead_w, 3, INK, bold=True, line_gap=2) + 4
        sy2 = draw_para(lx, by, body, lead_w, 1, INK, line_gap=2) + 4
        draw_text(lx, sy2, src, 1, GREY)

    # ---- secondary stories, two rows of five ----
    sec_w = 190
    sec_xs = [MX + i * (sec_w + 10) for i in range(5)]
    pic_fns = {"shield": lambda x, y, w, h: pic_shield(x, y, w, h, BLUE, GREEN),
               "quake": pic_quake, "factory": pic_factory,
               "mountains": pic_mountains, "gavel": pic_gavel,
               "scales": pic_scales, "ballot": pic_ballot,
               "chart": lambda x, y, w, h: pic_chart(x, y, w, h, True),
               "runner": pic_runner, "warning": pic_warning}
    row_ys = [388, 550]
    for row, (num0, sy) in enumerate(zip([0, 5], row_ys)):
        for i, (num, kicker, head, body, src, tag, picname) in enumerate(SECONDARIES[num0:num0 + 5]):
            sx = sec_xs[i]
            pic_fns[picname](sx, sy, sec_w, 48)
            ky = sy + 54
            draw_text(sx, ky, str(num) + "  " + kicker, 1, RED, bold=True)
            tag_chip(sx + sec_w - (len(tag) * 7 + 8), ky - 3, tag)
            hy = ky + 12
            by = draw_para(sx, hy, head, sec_w, 2, INK, bold=True, line_gap=2) + 4
            sy2 = draw_para(sx, by, body, sec_w, 1, INK, line_gap=2) + 4
            draw_text(sx, sy2, src, 1, GREY)
    hrule(MX, 712, CW, INK, 1)

    # ---- bottom: map + also-on list ----
    by = 720
    draw_text(MX, by, "WHERE IT HAPPENED", 2, RED, bold=True)
    draw_text(MX + 316, by, "ALSO ON MONDAY 23 NOVEMBER", 2, RED, bold=True)
    draw_map(MX, by + 20, 300, 200)
    draw_text(MX, by + 224, "pin numbers match the stories", 1, GREY)
    # also-on in two columns
    col_x = [MX + 316, MX + 316 + 348]
    for idx, item in enumerate(ALSO_ON):
        cx = col_x[idx // 11]
        cy = by + 20 + (idx % 11) * 17
        n = str(14 + idx)
        draw_text(cx, cy, n, 1, RED, bold=True)
        draw_text(cx + len(n) * 7 + 4, cy, item, 1, INK)

    # ---- date check footer ----
    dy = 946
    box(MX, dy, 92, 42, RED)
    draw_text(MX + 8, dy + 8, "DATE", 2, WHITE, bold=True)
    draw_text(MX + 8, dy + 24, "CHECK", 2, WHITE, bold=True)
    draw_para(MX + 100, dy + 2, DATE_CHECK, CW - 100, 1, INK, line_gap=2)

    # credit line
    credit = "All stories from Mon 23 Nov 2026. CONFIRMED = 2+ outlets, OFFICIAL = on the record, REPORTED = one outlet. Drawn in code."
    draw_text((PAGE - text_w(credit, 1)) // 2, 1002, credit, 1, GREY)


def main():
    build_page()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if not os.path.isdir(outdir):
        outdir = "out"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    n = write_png(path, PAGE, PAGE, buf)
    print("wrote %s (%d bytes, %dx%d)" % (path, n, PAGE, PAGE))


if __name__ == "__main__":
    main()
