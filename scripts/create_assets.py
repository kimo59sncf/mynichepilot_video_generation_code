#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot - Générateur d'Assets Graphiques & Dégradés Cosmiques
=============================================================================
Génère de manière procédurale :
1. L'icône officielle de la boussole dorée dans un squircle (512x512)
2. Le fond cosmique officiel dégradé à 135° (1080x1920) avec halos ambre/bleu
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

WIDTH = 1080
HEIGHT = 1920

def create_base_background(output_path):
    print(f"Génération du fond cosmique dégradé vers {output_path}...")
    arr = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    y_idx, x_idx = np.mgrid[0:HEIGHT, 0:WIDTH]
    diag = (x_idx / WIDTH * 0.4 + y_idx / HEIGHT * 0.6)
    
    c_top = np.array([0, 11, 21], dtype=float)     # #000b15
    c_mid = np.array([9, 16, 57], dtype=float)     # #091039
    c_bot = np.array([0, 14, 30], dtype=float)     # #000e1e
    
    mask1 = diag < 0.5
    t1 = diag[mask1] / 0.5
    for i in range(3):
        arr[:, :, i][mask1] = ((1 - t1) * c_top[i] + t1 * c_mid[i]).astype(np.uint8)
        
    mask2 = ~mask1
    t2 = (diag[mask2] - 0.5) / 0.5
    for i in range(3):
        arr[:, :, i][mask2] = ((1 - t2) * c_mid[i] + t2 * c_bot[i]).astype(np.uint8)
        
    base = Image.fromarray(arr).convert("RGB")
    
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_g = ImageDraw.Draw(glow)
    draw_g.ellipse([WIDTH // 2 - 400, 300 - 400, WIDTH // 2 + 400, 300 + 400], fill=(235, 136, 59, 25))
    draw_g.ellipse([WIDTH // 2 - 500, 1100 - 500, WIDTH // 2 + 500, 1100 + 500], fill=(7, 41, 79, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    base.paste(glow, (0, 0), glow)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base.save(output_path)
    print("✓ Fond cosmique généré avec succès.")

def create_compass_icon(output_path, size=512):
    print(f"Génération de l'icône de la boussole vers {output_path}...")
    ss = 4
    w = size * ss
    c1 = np.array([245, 158, 11], dtype=float)
    c2 = np.array([249, 115, 22], dtype=float)
    
    y_idx, x_idx = np.mgrid[0:w, 0:w]
    t = (x_idx + y_idx) / (2.0 * w)
    arr = np.zeros((w, w, 4), dtype=np.uint8)
    for c_i in range(3):
        arr[:, :, c_i] = ((1 - t) * c1[c_i] + t * c2[c_i]).astype(np.uint8)
    arr[:, :, 3] = 255
    
    img = Image.fromarray(arr).convert("RGBA")
    mask = Image.new("L", (w, w), 0)
    draw_mask = ImageDraw.Draw(mask)
    rx = int(w * 0.25)
    draw_mask.rounded_rectangle([0, 0, w - 1, w - 1], radius=rx, fill=255)
    img.putalpha(mask)
    
    draw = ImageDraw.Draw(img)
    cx, cy = w / 2.0, w / 2.0
    r = w * 0.25
    sw = int(w * (2.0 / 32.0))
    
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=sw)
    draw.line([cx, w * (4.0 / 32.0), cx, w * (8.0 / 32.0)], fill=(255, 255, 255, 255), width=sw)
    draw.line([cx, w * (24.0 / 32.0), cx, w * (28.0 / 32.0)], fill=(255, 255, 255, 255), width=sw)
    draw.line([w * (4.0 / 32.0), cy, w * (8.0 / 32.0), cy], fill=(255, 255, 255, 255), width=sw)
    draw.line([w * (24.0 / 32.0), cy, w * (28.0 / 32.0), cy], fill=(255, 255, 255, 255), width=sw)
    
    r_dot = w * (3.0 / 32.0)
    draw.ellipse([cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot], fill=(255, 255, 255, 255))
    
    res = img.resize((size, size), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    res.save(output_path)
    print("✓ Icône boussole générée avec succès.")

if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    create_base_background(os.path.join(ASSETS_DIR, "base_bg.png"))
    create_compass_icon(os.path.join(ASSETS_DIR, "compass_icon_512.png"))
