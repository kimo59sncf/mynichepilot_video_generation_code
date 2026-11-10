#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot - Générateur Autonome de Vidéo Publicitaire 9:16 (Full Pipeline)
=============================================================================
Ce script reproduit de A à Z la publicité vidéo officielle pour MyNichePilot
(https://mynichepilot.com) au format vertical 9:16 (1080x1920, 30 FPS).

Architecture complète intégrée :
1. Détection & Résolution des polices (Inter, Playfair Display) et logos
2. Synthèse automatique des assets graphiques (boussole, fond dégradé cosmique)
3. Génération de la voix off neurale Edge-TTS en français (fr-FR-HenriNeural)
4. Synthèse audio procédurale :
   - Piste musicale électro/tech (120 BPM : kick, snare, hi-hats, bassline, arp, pad)
   - Effets sonores (SFX : whoosh, impact sub-bass, clics UI, carillon de succès)
   - Mixage audio avec ducking automatique (compression sidechain pendant la voix)
5. Moteur de rendu graphique Pillow / NumPy :
   - Séquence 1 : Hook Choc (8.60s) - Surcharge mentale & idées confuses
   - Séquence 2 : Problème & Solution (9.20s) - Révélation du Coach IA
   - Séquence 3 : Démonstration SaaS (9.50s) - Cockpit live, score 94/100, roadmap 16 sem.
   - Séquence 4 : Transformation Immédiate (8.50s) - Avant vs Avec NichePilot
   - Séquence 5 : Call to Action (8.50s) - Boussole animée, bouton CTA, offre gratuite
6. Pipeline FFmpeg en streaming direct (RGB24 via stdin -> H.264 / AAC)
7. Concaténation automatique en un master vidéo final prêt à la diffusion

Auteur : MyNichePilot Creative Studio & Video Production
=============================================================================
"""

import os
import sys
import math
import time
import shutil
import asyncio
import argparse
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wav
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Garantit une sortie console UTF-8 (notamment les emojis) sur Windows,
# où le flux stdout des sous-processus est sinon en cp1252 et plante le print().
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# =============================================================================
# 1. CONFIGURATION & CONSTANTES GLOBALES
# =============================================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SAMPLE_RATE = 44100

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
FONTS_DIR = os.path.join(SCRIPT_DIR, "fonts")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# Palette chromatique officielle MyNichePilot
C_WHITE = (255, 255, 255)
C_GOLD = (252, 211, 77)       # #fcd34d
C_AMBER = (236, 167, 96)      # #eca760 (couleur d'accent majeure)
C_ORANGE = (245, 158, 11)     # #f59e0b
C_EMERALD = (52, 211, 153)    # #34d399 (succès / validation)
C_CYAN = (96, 165, 250)       # #60a5fa (données & tech)
C_RED = (239, 68, 68)         # #ef4444 (alerte & surcharge)
C_MUTED = (180, 200, 225)     # Texte secondaire

# Teintes de conteneurs & interfaces solides (sans artefact alpha)
BOX_NAVY = (16, 26, 64)
BOX_NAVY_LIGHT = (22, 36, 85)
BOX_BORDER_SUBTLE = (38, 54, 110)
BOX_RED = (38, 16, 26)
BOX_RED_PILL = (55, 20, 30)
BOX_EMERALD_PILL = (18, 55, 70)
BOX_GOLD_PILL = (55, 38, 15)
BOX_SUBTITLE = (6, 12, 32)

# =============================================================================
# 2. DONNÉES ÉDITORIALES DES 5 SÉQUENCES (VOIX OFF, DURÉES, SFX)
# =============================================================================

SEQUENCES_CONFIG = [
    {
        "id": 1,
        "name": "sequence_1_hook",
        "title": "Hook Choc — Surcharge Mentale",
        "duration": 8.60,
        "voice_text": "Tu veux lancer ton business en ligne, mais tu ne sais pas quelle niche choisir ? Trop d'idées confuses, zéro plan clair et une vraie surcharge mentale.",
        "sfx": [
            ("impact", 0.05, 0.45),
            ("click", 3.0, 0.40),
            ("whoosh", 7.9, 0.55)
        ]
    },
    {
        "id": 2,
        "name": "sequence_2_probleme_solution",
        "title": "Problème & Solution — Coach IA d'Exécution",
        "duration": 9.20,
        "voice_text": "Analyser la concurrence prend des semaines, et le risque d'échec est énorme. Voici NichePilot, le coach IA d'exécution business qui change la donne.",
        "sfx": [
            ("whoosh", 0.05, 0.40),
            ("click", 1.8, 0.35),
            ("click", 3.2, 0.35),
            ("impact", 4.5, 0.60),
            ("click", 6.8, 0.40)
        ]
    },
    {
        "id": 3,
        "name": "sequence_3_demonstration_saas",
        "title": "Démonstration SaaS — Cockpit & Roadmap",
        "duration": 9.50,
        "voice_text": "Regarde ça : diagnostic en direct, score de potentiel validé à 94 sur 100, opportunités rentables détectées et une roadmap concrète sur 16 semaines.",
        "sfx": [
            ("whoosh", 0.05, 0.40),
            ("click", 1.2, 0.35),
            ("success", 4.2, 0.55),
            ("click", 6.2, 0.35),
            ("click", 7.8, 0.35)
        ]
    },
    {
        "id": 4,
        "name": "sequence_4_transformation",
        "title": "Transformation — De la Confusion à la Clarté",
        "duration": 8.50,
        "voice_text": "Finie la confusion ! Tu passes instantanément du doute à la certitude absolue : ta niche est validée, et ton offre irrésistible est prête à vendre.",
        "sfx": [
            ("whoosh", 0.05, 0.40),
            ("impact", 2.2, 0.45),
            ("success", 3.8, 0.50),
            ("click", 5.5, 0.35),
            ("click", 7.0, 0.35)
        ]
    },
    {
        "id": 5,
        "name": "sequence_5_call_to_action",
        "title": "Appel à l'Action — Diagnostic Gratuit",
        "duration": 8.50,
        "voice_text": "Ne laisse plus tes idées au placard. Rends-toi dès aujourd'hui sur mynichepilot.com, fais ton diagnostic gratuit et lance ton business !",
        "sfx": [
            ("whoosh", 0.05, 0.40),
            ("click", 2.5, 0.35),
            ("impact", 4.0, 0.55),
            ("success", 4.3, 0.50)
        ]
    }
]

# =============================================================================
# 3. GESTION DES POLICES & ASSETS
# =============================================================================

_font_cache = {}

def resolve_font_path(preferred_name):
    """Recherche la police demandée dans les répertoires locaux ou système."""
    candidates = [
        os.path.join(FONTS_DIR, f"{preferred_name}-Variable.ttf"),
        os.path.join(FONTS_DIR, f"{preferred_name}.ttf"),
        f"/usr/local/share/fonts/google/{preferred_name}-Variable.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Si introuvable, retourne None pour utiliser la police par défaut de Pillow
    return None

FONT_PLAYFAIR_PATH = resolve_font_path("PlayfairDisplay")
FONT_INTER_PATH = resolve_font_path("Inter")

def get_font(path, size):
    """Met en cache les polices TrueType pour une performance maximale."""
    key = (path, size)
    if key not in _font_cache:
        try:
            if path and os.path.exists(path):
                _font_cache[key] = ImageFont.truetype(path, size)
            else:
                _font_cache[key] = ImageFont.load_default()
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

def generate_base_background():
    """Génère le fond cosmique 135° officiel MyNichePilot (#000b15 -> #091039 -> #000e1e)."""
    bg_file = os.path.join(ASSETS_DIR, "base_bg.png")
    if os.path.exists(bg_file):
        return Image.open(bg_file).convert("RGB")
    
    print("  -> Génération du fond cosmique dégradé...")
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
    
    # Halos lumineux subtils ambre et bleu
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_g = ImageDraw.Draw(glow)
    draw_g.ellipse([WIDTH // 2 - 400, 300 - 400, WIDTH // 2 + 400, 300 + 400], fill=(235, 136, 59, 25))
    draw_g.ellipse([WIDTH // 2 - 500, 1100 - 500, WIDTH // 2 + 500, 1100 + 500], fill=(7, 41, 79, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    base.paste(glow, (0, 0), glow)
    
    os.makedirs(ASSETS_DIR, exist_ok=True)
    base.save(bg_file)
    return base

def generate_compass_icon(size=512):
    """Génère l'icône officielle de la boussole dorée dans son squircle."""
    compass_file = os.path.join(ASSETS_DIR, "compass_icon_512.png")
    if os.path.exists(compass_file):
        return Image.open(compass_file).convert("RGBA")
        
    print("  -> Génération de l'icône vectorielle de la boussole MyNichePilot...")
    ss = 4
    w = size * ss
    c1 = np.array([245, 158, 11], dtype=float) # #f59e0b
    c2 = np.array([249, 115, 22], dtype=float) # #f97316
    
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
    os.makedirs(ASSETS_DIR, exist_ok=True)
    res.save(compass_file)
    return res

BASE_BG = None
COMPASS_ICON = None

def init_assets():
    global BASE_BG, COMPASS_ICON
    BASE_BG = generate_base_background()
    COMPASS_ICON = generate_compass_icon()

# =============================================================================
# 4. COMPOSANTS GRAPHIQUES DE BASE (HEADER, SOUS-TITRES, PARTICULES)
# =============================================================================

def draw_header(img, draw):
    """En-tête de marque persistant avec logo boussole, nom et badges."""
    logo_small = COMPASS_ICON.resize((48, 48), Image.Resampling.LANCZOS)
    img.paste(logo_small, (80, 100), logo_small)
    font_brand = get_font(FONT_PLAYFAIR_PATH, 34)
    draw.text((140, 106), "MyNichePilot", font=font_brand, fill=C_WHITE)
    draw.rounded_rectangle([360, 110, 415, 142], radius=8, fill=BOX_GOLD_PILL, outline=C_ORANGE, width=1)
    font_badge = get_font(FONT_INTER_PATH, 18)
    draw.text((375, 116), "AI", font=font_badge, fill=C_GOLD)
    draw.rounded_rectangle([720, 108, 1000, 144], radius=18, fill=BOX_NAVY, outline=BOX_BORDER_SUBTLE, width=1)
    draw.text((748, 116), "DIAGNOSTIC BUSINESS", font=font_badge, fill=C_AMBER)

def draw_subtitles_dynamic(draw, word_tuples, y_pos=1530):
    """Sous-titres dynamiques haute lisibilité avec conteneur sombre centré."""
    font = get_font(FONT_INTER_PATH, 36)
    widths = []
    total_w = 0
    for w, col in word_tuples:
        bbox = font.getbbox(w + " ")
        w_px = bbox[2] - bbox[0]
        widths.append(w_px)
        total_w += w_px
        
    pad_x = 36
    box_w = min(WIDTH - 100, total_w + pad_x * 2)
    box_h = 76
    x0 = (WIDTH - box_w) // 2
    y0 = y_pos
    x1 = x0 + box_w
    y1 = y0 + box_h
    
    draw.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=BOX_SUBTITLE, outline=C_AMBER, width=2)
    
    cur_x = x0 + pad_x
    cur_y = y0 + 16
    for (w, col), w_px in zip(word_tuples, widths):
        draw.text((cur_x, cur_y), w, font=font, fill=col)
        cur_x += w_px

# =============================================================================
# 4bis. SOUS-TITRES DYNAMIQUES (contenu IA variable)
# =============================================================================
_DYNAMIC_SUBTITLES = {}


def set_dynamic_subtitles(seq_id, voice_text, duration):
    """Découpe la voix off en fenêtres de sous-titres sur la durée (contenu IA)."""
    if not voice_text:
        _DYNAMIC_SUBTITLES.pop(seq_id, None)
        return
    words = voice_text.split()
    n = 4
    if len(words) <= n:
        chunks = list(words)
    else:
        k = math.ceil(len(words) / n)
        chunks = [" ".join(words[i:i + k]) for i in range(0, len(words), k)]
    _DYNAMIC_SUBTITLES[seq_id] = {"duration": max(0.1, duration), "chunks": chunks}


def dynamic_subtitles(seq_id, t, default_sub):
    """Retourne les sous-titres dynamiques si dispo, sinon le défaut codé en dur."""
    info = _DYNAMIC_SUBTITLES.get(seq_id)
    if not info or not info["chunks"] or info["duration"] <= 0:
        return default_sub
    chunks = info["chunks"]
    idx = min(len(chunks) - 1, int(t / (info["duration"] / len(chunks))))
    words = chunks[idx].split()
    half = max(1, len(words) // 2)
    first = " ".join(words[:half])
    second = " ".join(words[half:])
    if second:
        return [(first, C_WHITE), (second, C_GOLD)]
    return [(first, C_GOLD)]


def add_floating_particles(draw, t, count=25):
    """Particules dorées flottantes générées de manière déterministe."""
    np.random.seed(42)
    xs = np.random.randint(40, WIDTH - 40, count)
    init_ys = np.random.randint(150, HEIGHT - 250, count)
    speeds = np.random.uniform(20, 50, count)
    sizes = np.random.randint(2, 5, count)
    
    for i in range(count):
        y = int((init_ys[i] - t * speeds[i]) % (HEIGHT - 400) + 200)
        x = xs[i] + int(math.sin(t * 1.5 + i) * 12)
        r = sizes[i]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=C_GOLD)

# =============================================================================
# 5. RENDU VISUEL DES 5 SÉQUENCES
# =============================================================================

def render_seq1_frame(t):
    """Séquence 1 : Hook Choc (8.60s) - Question d'ouverture & Alerte mentale."""
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    add_floating_particles(draw, t)
    draw_header(img, draw)
    
    draw.rounded_rectangle([80, 240, 480, 290], radius=16, fill=BOX_GOLD_PILL, outline=C_AMBER, width=1)
    draw.text((105, 252), "• ENTREPRENEURIAT WEB", font=get_font(FONT_INTER_PATH, 22), fill=C_GOLD)
    
    draw.text((80, 320), "Tu veux lancer ton", font=get_font(FONT_PLAYFAIR_PATH, 74), fill=C_WHITE)
    draw.text((80, 410), "business en ligne ?", font=get_font(FONT_PLAYFAIR_PATH, 74), fill=C_AMBER)
    
    floating_ideas = [
        ("Dropshipping ?", "• Saturé & marges faibles", [80, 550, 520, 660], C_RED, 0.5, 2.5),
        ("Agence SMMA ?", "• Prospection froide épuisante", [550, 590, 1000, 700], C_RED, 0.8, 2.2),
        ("Création SaaS ?", "• Trop technique tout seul", [80, 690, 520, 800], C_ORANGE, 1.1, 2.7),
        ("Infoproduit ?", "• Zéro audience pour vendre", [550, 730, 1000, 840], C_RED, 1.4, 2.4),
    ]
    for title, sub, box, col, delay, freq in floating_ideas:
        if t >= delay:
            offset_y = int(math.sin(t * freq) * 6)
            b = [box[0], box[1] + offset_y, box[2], box[3] + offset_y]
            draw.rounded_rectangle(b, radius=20, fill=BOX_NAVY, outline=BOX_BORDER_SUBTLE, width=1)
            draw.text((b[0] + 25, b[1] + 20), title, font=get_font(FONT_INTER_PATH, 28), fill=C_WHITE)
            draw.text((b[0] + 25, b[1] + 65), sub, font=get_font(FONT_INTER_PATH, 20), fill=col)
            
    if t >= 2.2:
        alert_box = [80, 890, 1000, 1260]
        pulse = 0.5 + 0.5 * math.sin(t * 6.0)
        draw.rounded_rectangle(alert_box, radius=28, fill=BOX_RED, outline=C_RED, width=int(2 + 2 * pulse))
        
        draw.rounded_rectangle([115, 925, 600, 970], radius=12, fill=BOX_RED_PILL, outline=C_RED, width=1)
        draw.text((130, 935), "• ALERTE : SURCHARGE MENTALE", font=get_font(FONT_INTER_PATH, 22), fill=C_RED)
        
        draw.text((120, 995), "100+ idées en vrac", font=get_font(FONT_PLAYFAIR_PATH, 54), fill=C_WHITE)
        draw.text((120, 1065), "0 plan d'action validé", font=get_font(FONT_PLAYFAIR_PATH, 54), fill=C_AMBER)
        
        fill_pct = min(1.0, (t - 2.2) / 2.0)
        draw.rounded_rectangle([120, 1160, 960, 1195], radius=12, fill=(25, 35, 70))
        draw.rounded_rectangle([120, 1160, 120 + int(840 * fill_pct), 1195], radius=12, fill=C_RED)
        draw.text((120, 1210), "Clarté : 0%  •  Risque d'abandon : 95%", font=get_font(FONT_INTER_PATH, 20), fill=C_MUTED)
        
    if t < 2.2:
        sub = [("Tu veux lancer ton", C_WHITE), ("business en ligne,", C_GOLD)]
    elif t < 4.4:
        sub = [("mais quelle", C_WHITE), ("niche choisir ?", C_GOLD)]
    elif t < 6.4:
        sub = [("Trop d'idées confuses,", C_AMBER), ("zéro plan,", C_RED)]
    else:
        sub = [("et une vraie", C_WHITE), ("surcharge mentale !", C_GOLD)]
    sub = dynamic_subtitles(1, t, sub)
    draw_subtitles_dynamic(draw, sub)
    return img

def render_seq2_frame(t):
    """Séquence 2 : Problème & Solution (9.20s) - Douleurs marché & Révélation NichePilot."""
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    add_floating_particles(draw, t)
    draw_header(img, draw)
    
    if t < 4.2:
        draw.text((80, 240), "LE DÉFI DE LA RECHERCHE", font=get_font(FONT_INTER_PATH, 22), fill=C_AMBER)
        draw.text((80, 285), "Analyser le marché tout seul ?", font=get_font(FONT_PLAYFAIR_PATH, 54), fill=C_WHITE)
        
        problems = [
            ("• Recherche manuelle", "40 heures perdues sur des tableaux Excel sans certitude", 0.3),
            ("• Données introuvables", "Impossible de connaître la demande réelle et les marges", 1.2),
            ("• Risque d'échec critique", "90% des entrepreneurs abandonnent avant la 1ère vente", 2.2)
        ]
        py = 420
        for p_t, p_d, delay in problems:
            if t >= delay:
                draw.rounded_rectangle([80, py, 1000, py + 130], radius=22, fill=BOX_RED, outline=C_RED, width=2)
                draw.text((115, py + 25), p_t, font=get_font(FONT_INTER_PATH, 28), fill=C_RED)
                draw.text((115, py + 75), p_d, font=get_font(FONT_INTER_PATH, 22), fill=C_MUTED)
            py += 160
            
        if t >= 2.8:
            draw.rounded_rectangle([80, 930, 1000, 1100], radius=24, fill=BOX_NAVY, outline=BOX_BORDER_SUBTLE)
            draw.text((115, 960), "Statut : Recherche bloquée depuis 6 mois...", font=get_font(FONT_INTER_PATH, 24), fill=C_WHITE)
            draw.rounded_rectangle([115, 1015, 965, 1045], radius=10, fill=(25, 35, 70))
            draw.rounded_rectangle([115, 1015, 115 + int(850 * 0.12), 1045], radius=10, fill=C_RED)
            draw.text((115, 1055), "Progression : 12% seulement", font=get_font(FONT_INTER_PATH, 20), fill=C_MUTED)
    else:
        t_rev = t - 4.2
        draw.text((80, 240), "LE TOURNANT STRATÉGIQUE", font=get_font(FONT_INTER_PATH, 22), fill=C_GOLD)
        
        scale = min(1.0, 0.7 + 0.3 * (t_rev / 0.5))
        logo_size = int(200 * scale)
        logo_res = COMPASS_ICON.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        img.paste(logo_res, ((WIDTH - logo_size) // 2, 330 + (200 - logo_size) // 2), logo_res)
        
        font_brand = get_font(FONT_PLAYFAIR_PATH, 76)
        brand_w = font_brand.getbbox("NichePilot")[2] - font_brand.getbbox("NichePilot")[0]
        draw.text(((WIDTH - brand_w) // 2 - 40, 560), "NichePilot", font=font_brand, fill=C_WHITE)
        
        ai_x = (WIDTH - brand_w) // 2 - 40 + brand_w + 15
        draw.rounded_rectangle([ai_x, 575, ai_x + 70, 625], radius=12, fill=BOX_GOLD_PILL, outline=C_ORANGE, width=2)
        draw.text((ai_x + 18, 584), "AI", font=get_font(FONT_INTER_PATH, 28), fill=C_GOLD)
        
        tagline = "Le 1er Coach IA d'Exécution Business"
        tw = get_font(FONT_INTER_PATH, 34).getbbox(tagline)[2] - get_font(FONT_INTER_PATH, 34).getbbox(tagline)[0]
        draw.text(((WIDTH - tw) // 2, 665), tagline, font=get_font(FONT_INTER_PATH, 34), fill=C_AMBER)
        
        pillars = [
            ("✓  Validation Prédictive de Niche", "Analyse en direct de 100+ signaux d'achat réels", C_EMERALD, 0.5),
            ("✓  Roadmap d'Exécution sur 16 Semaines", "Chaque étape guidée pas à pas sans improvisation", C_GOLD, 1.2),
            ("✓  Génération d'Offre Irrésistible", "Positionnement unique et pricing validé par l'IA", C_CYAN, 1.9),
        ]
        card_y = 760
        for p_t, p_d, col, delay in pillars:
            if t_rev >= delay:
                draw.rounded_rectangle([80, card_y, 1000, card_y + 130], radius=22, fill=BOX_NAVY, outline=BOX_BORDER_SUBTLE, width=1)
                draw.text((110, card_y + 25), p_t, font=get_font(FONT_INTER_PATH, 28), fill=col)
                draw.text((110, card_y + 75), p_d, font=get_font(FONT_INTER_PATH, 22), fill=C_MUTED)
            card_y += 150
            
    if t < 2.5:
        sub = [("Analyser la concurrence", C_WHITE), ("prend des semaines,", C_AMBER)]
    elif t < 4.4:
        sub = [("et le", C_WHITE), ("risque d'échec", C_RED), ("est énorme.", C_WHITE)]
    elif t < 6.8:
        sub = [("Voici", C_WHITE), ("NichePilot,", C_GOLD), ("le coach IA", C_GOLD)]
    else:
        sub = [("d'exécution business", C_GOLD), ("qui change la donne.", C_EMERALD)]
    sub = dynamic_subtitles(2, t, sub)
    draw_subtitles_dynamic(draw, sub)
    return img

def render_seq3_frame(t):
    """Séquence 3 : Démonstration SaaS (9.50s) - Cockpit live, laser de scan, score 94/100."""
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    add_floating_particles(draw, t)
    draw_header(img, draw)
    
    draw.text((80, 230), "DÉMONSTRATION EN DIRECT", font=get_font(FONT_INTER_PATH, 22), fill=C_EMERALD)
    draw.text((80, 275), "Diagnostic de Potentiel Business", font=get_font(FONT_PLAYFAIR_PATH, 54), fill=C_WHITE)
    
    cockpit_box = [80, 370, 1000, 1420]
    draw.rounded_rectangle(cockpit_box, radius=32, fill=(12, 20, 52), outline=C_AMBER, width=2)
    
    # Rayon de scan dynamique
    if t < 4.5:
        scan_y = cockpit_box[1] + int((t * 220) % (cockpit_box[3] - cockpit_box[1]))
        draw.line([cockpit_box[0] + 10, scan_y, cockpit_box[2] - 10, scan_y], fill=C_CYAN, width=2)
        
    draw.rounded_rectangle([cockpit_box[0] + 25, cockpit_box[1] + 25, cockpit_box[2] - 25, cockpit_box[1] + 100], radius=16, fill=(20, 34, 80))
    logo_tiny = COMPASS_ICON.resize((42, 42), Image.Resampling.LANCZOS)
    img.paste(logo_tiny, (cockpit_box[0] + 45, cockpit_box[1] + 42), logo_tiny)
    draw.text((cockpit_box[0] + 105, cockpit_box[1] + 48), "Analyse Niche : Micro-SaaS B2B", font=get_font(FONT_INTER_PATH, 26), fill=C_WHITE)
    
    # Badge "EN DIRECT"
    draw.rounded_rectangle([cockpit_box[2] - 200, cockpit_box[1] + 42, cockpit_box[2] - 45, cockpit_box[1] + 82], radius=10, fill=BOX_EMERALD_PILL, outline=C_EMERALD, width=1)
    draw.text((cockpit_box[2] - 185, cockpit_box[1] + 50), "EN DIRECT", font=get_font(FONT_INTER_PATH, 18), fill=C_EMERALD)
    
    score_y = cockpit_box[1] + 130
    draw.text((120, score_y + 10), "SCORE GLOBAL DE POTENTIEL", font=get_font(FONT_INTER_PATH, 22), fill=C_MUTED)
    
    if t < 0.5:
        score_val = 18
    elif t < 3.5:
        p = (t - 0.5) / 3.0
        score_val = int(18 + (94 - 18) * (1.0 - math.cos(p * math.pi)) / 2.0)
    else:
        score_val = 94
        
    draw.text((120, score_y + 50), str(score_val), font=get_font(FONT_PLAYFAIR_PATH, 120), fill=C_GOLD)
    draw.text((290, score_y + 110), "/ 100", font=get_font(FONT_PLAYFAIR_PATH, 46), fill=C_MUTED)
    
    draw.rounded_rectangle([500, score_y + 80, 940, score_y + 145], radius=16, fill=BOX_EMERALD_PILL, outline=C_EMERALD, width=2)
    draw.text((530, score_y + 98), "★ TRÈS HAUT POTENTIEL", font=get_font(FONT_INTER_PATH, 24), fill=C_EMERALD)
    
    # Métriques clés du marché
    if t >= 3.5:
        metrics = [
            ("Demande marché", "+340% (Forte)", C_EMERALD),
            ("Concurrence", "Faible à modérée", C_CYAN),
            ("Panier moyen", "89€ / mois", C_GOLD)
        ]
        mx = cockpit_box[0] + 30
        for m_label, m_val, m_col in metrics:
            m_box = [mx, score_y + 200, mx + 275, score_y + 295]
            draw.rounded_rectangle(m_box, radius=16, fill=BOX_NAVY_LIGHT, outline=BOX_BORDER_SUBTLE, width=1)
            draw.text((m_box[0] + 18, m_box[1] + 15), m_label, font=get_font(FONT_INTER_PATH, 18), fill=C_MUTED)
            draw.text((m_box[0] + 18, m_box[1] + 48), m_val, font=get_font(FONT_INTER_PATH, 22), fill=m_col)
            mx += 295
            
    # Section Roadmap 16 semaines
    road_y = score_y + 330
    draw.text((120, road_y), "ROADMAP D'EXÉCUTION (16 SEMAINES)", font=get_font(FONT_INTER_PATH, 22), fill=C_GOLD)
    
    steps = [
        ("S1-S4", "Validation de niche & Offre MVP", "Validé à 100%", C_EMERALD, 4.5),
        ("S5-S8", "Acquisition ciblée & Premiers 10 clients", "En cours", C_AMBER, 5.5),
        ("S9-S16", "Scaling automatisé & Récurrence", "Planifié", C_CYAN, 6.5),
    ]
    sy = road_y + 40
    for tag, desc, stat, col, delay in steps:
        if t >= delay:
            s_box = [cockpit_box[0] + 30, sy, cockpit_box[2] - 30, sy + 75]
            draw.rounded_rectangle(s_box, radius=14, fill=BOX_NAVY_LIGHT, outline=BOX_BORDER_SUBTLE)
            draw.rounded_rectangle([s_box[0] + 15, s_box[1] + 15, s_box[0] + 115, s_box[1] + 60], radius=8, fill=BOX_NAVY, outline=col)
            draw.text((s_box[0] + 28, s_box[1] + 22), tag, font=get_font(FONT_INTER_PATH, 20), fill=col)
            draw.text((s_box[0] + 135, s_box[1] + 24), desc, font=get_font(FONT_INTER_PATH, 22), fill=C_WHITE)
            draw.text((s_box[2] - 150, s_box[1] + 24), stat, font=get_font(FONT_INTER_PATH, 19), fill=col)
        sy += 90
        
    if t < 2.4:
        sub = [("Regarde ça :", C_WHITE), ("diagnostic en direct !", C_CYAN)]
    elif t < 4.8:
        sub = [("Score validé à", C_WHITE), ("94 sur 100,", C_EMERALD), ("haut potentiel !", C_EMERALD)]
    elif t < 7.0:
        sub = [("Opportunités", C_WHITE), ("rentables détectées,", C_GOLD)]
    else:
        sub = [("et une roadmap", C_WHITE), ("sur 16 semaines !", C_GOLD)]
    sub = dynamic_subtitles(3, t, sub)
    draw_subtitles_dynamic(draw, sub)
    return img

def render_seq4_frame(t):
    """Séquence 4 : Transformation (8.50s) - Avant vs Avec NichePilot."""
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    add_floating_particles(draw, t)
    draw_header(img, draw)
    
    draw.text((80, 230), "TRANSFORMATION IMMÉDIATE", font=get_font(FONT_INTER_PATH, 22), fill=C_EMERALD)
    draw.text((80, 275), "De la Confusion à la Clarté", font=get_font(FONT_PLAYFAIR_PATH, 58), fill=C_WHITE)
    
    draw.rounded_rectangle([80, 390, 1000, 560], radius=24, fill=BOX_RED, outline=C_RED, width=2)
    draw.rounded_rectangle([110, 415, 250, 460], radius=10, fill=BOX_RED_PILL, outline=C_RED)
    draw.text((135, 424), "• AVANT", font=get_font(FONT_INTER_PATH, 22), fill=C_RED)
    draw.text((275, 424), "6 mois d'hésitations stériles", font=get_font(FONT_INTER_PATH, 24), fill=C_WHITE)
    draw.text((110, 485), "• Idées floues  • Peur de l'échec  • Zéro client", font=get_font(FONT_INTER_PATH, 24), fill=(220, 180, 180))
    
    if t >= 1.5:
        arrow_y = 585 + int(math.sin(t * 6.0) * 5)
        draw.text((WIDTH // 2 - 20, arrow_y), "▼", font=get_font(FONT_INTER_PATH, 40), fill=C_EMERALD)
        
    if t >= 1.8:
        card_main = [80, 650, 1000, 1380]
        draw.rounded_rectangle(card_main, radius=28, fill=(14, 25, 65), outline=C_EMERALD, width=2)
        draw.rounded_rectangle([110, 680, 440, 730], radius=12, fill=BOX_EMERALD_PILL, outline=C_EMERALD)
        draw.text((135, 690), "✓ AVEC NICHE PILOT", font=get_font(FONT_INTER_PATH, 24), fill=C_EMERALD)
        
        results = [
            ("Niche Rentable Validée", "Marché prouvé par des données réelles, zéro devinette.", C_EMERALD, 2.0),
            ("Offre Irrésistible Calibrée", "Positionnement clair, pricing optimisé et promesse forte.", C_GOLD, 3.0),
            ("Roadmap Quotidienne 16 Semaines", "Tu sais exactement quoi faire chaque matin pour exécuter.", C_CYAN, 4.0),
            ("Prêt à Vendre Immédiatement", "Ton business est prêt pour générer ses premiers revenus.", C_AMBER, 5.0)
        ]
        ry = 760
        for r_title, r_desc, col, delay in results:
            if t >= delay:
                draw.rounded_rectangle([110, ry, 970, ry + 120], radius=16, fill=BOX_NAVY_LIGHT, outline=BOX_BORDER_SUBTLE)
                draw.ellipse([135, ry + 25, 175, ry + 65], fill=BOX_NAVY, outline=col, width=2)
                draw.text((146, ry + 28), "✓", font=get_font(FONT_INTER_PATH, 24), fill=col)
                draw.text((195, ry + 25), r_title, font=get_font(FONT_INTER_PATH, 26), fill=C_WHITE)
                draw.text((195, ry + 68), r_desc, font=get_font(FONT_INTER_PATH, 20), fill=C_MUTED)
            ry += 140
            
    if t < 2.0:
        sub = [("Finie", C_EMERALD), ("la confusion !", C_WHITE)]
    elif t < 4.4:
        sub = [("Du doute à la", C_WHITE), ("certitude absolue :", C_GOLD)]
    elif t < 6.4:
        sub = [("Ta niche rentable", C_WHITE), ("est validée,", C_EMERALD)]
    else:
        sub = [("et ton offre", C_WHITE), ("prête à vendre !", C_GOLD)]
    sub = dynamic_subtitles(4, t, sub)
    draw_subtitles_dynamic(draw, sub)
    return img

def render_seq5_frame(t):
    """Séquence 5 : Call to Action (8.50s) - Boussole animée, bouton CTA, offre gratuite."""
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    add_floating_particles(draw, t)
    draw_header(img, draw)
    
    logo_scale = 1.0 + 0.04 * math.sin(t * 2.5)
    logo_size = int(230 * logo_scale)
    logo_res = COMPASS_ICON.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    img.paste(logo_res, ((WIDTH - logo_size) // 2, 280 + (230 - logo_size) // 2), logo_res)
    
    font_brand = get_font(FONT_PLAYFAIR_PATH, 82)
    brand_w = font_brand.getbbox("MyNichePilot")[2] - font_brand.getbbox("MyNichePilot")[0]
    draw.text(((WIDTH - brand_w) // 2 - 40, 540), "MyNichePilot", font=font_brand, fill=C_WHITE)
    
    ai_x = (WIDTH - brand_w) // 2 - 40 + brand_w + 15
    draw.rounded_rectangle([ai_x, 560, ai_x + 75, 615], radius=14, fill=BOX_GOLD_PILL, outline=C_ORANGE, width=2)
    draw.text((ai_x + 20, 570), "AI", font=get_font(FONT_INTER_PATH, 30), fill=C_GOLD)
    
    tagline = "Le copilote IA de ton exécution business"
    tw = get_font(FONT_INTER_PATH, 32).getbbox(tagline)[2] - get_font(FONT_INTER_PATH, 32).getbbox(tagline)[0]
    draw.text(((WIDTH - tw) // 2, 650), tagline, font=get_font(FONT_INTER_PATH, 32), fill=C_AMBER)
    
    prop_box = [80, 740, 1000, 1030]
    draw.rounded_rectangle(prop_box, radius=24, fill=BOX_NAVY, outline=BOX_BORDER_SUBTLE, width=1)
    
    items = [
        "Diagnostic complet de ton potentiel en 5 minutes",
        "Analyse prédictive de niche & signaux d'achat réels",
        "Roadmap d'exécution sur 16 semaines sur-mesure",
        "100% Gratuit & Accès immédiat"
    ]
    iy = 775
    for item in items:
        draw.ellipse([115, iy + 4, 145, iy + 34], fill=BOX_EMERALD_PILL, outline=C_EMERALD, width=2)
        draw.text((122, iy + 6), "✓", font=get_font(FONT_INTER_PATH, 19), fill=C_EMERALD)
        draw.text((160, iy + 4), item, font=get_font(FONT_INTER_PATH, 25), fill=C_WHITE)
        iy += 60
        
    cta_box = [100, 1080, 980, 1220]
    btn_pulse = int(3 + 2 * math.sin(t * 5.0))
    draw.rounded_rectangle(cta_box, radius=32, fill=(235, 136, 59), outline=C_GOLD, width=btn_pulse)
    cta_text = "FAIRE LE DIAGNOSTIC GRATUIT →"
    font_cta = get_font(FONT_INTER_PATH, 36)
    cw = font_cta.getbbox(cta_text)[2] - font_cta.getbbox(cta_text)[0]
    draw.text(((WIDTH - cw) // 2, 1120), cta_text, font=font_cta, fill=(0, 11, 21))
    
    guar_text = "Sans carte bancaire  •  Résultats immédiats"
    gw = get_font(FONT_INTER_PATH, 24).getbbox(guar_text)[2] - get_font(FONT_INTER_PATH, 24).getbbox(guar_text)[0]
    draw.text(((WIDTH - gw) // 2, 1255), guar_text, font=get_font(FONT_INTER_PATH, 24), fill=C_MUTED)
    
    url_text = "mynichepilot.com"
    font_url = get_font(FONT_INTER_PATH, 54)
    uw = font_url.getbbox(url_text)[2] - font_url.getbbox(url_text)[0]
    draw.text(((WIDTH - uw) // 2, 1335), url_text, font=font_url, fill=C_GOLD)
    line_expand = min(1.0, t / 1.5)
    line_w = int(uw * line_expand)
    draw.line([(WIDTH - line_w) // 2, 1405, (WIDTH + line_w) // 2, 1405], fill=C_AMBER, width=3)
    
    if t < 2.5:
        sub = [("Ne laisse plus tes", C_WHITE), ("idées au placard.", C_GOLD)]
    elif t < 5.2:
        sub = [("Rendez-vous sur", C_WHITE), ("mynichepilot.com,", C_GOLD)]
    else:
        sub = [("Fais ton", C_WHITE), ("diagnostic gratuit", C_EMERALD), ("dès maintenant !", C_GOLD)]
    sub = dynamic_subtitles(5, t, sub)
    draw_subtitles_dynamic(draw, sub)
    return img

RENDERERS = {
    1: render_seq1_frame,
    2: render_seq2_frame,
    3: render_seq3_frame,
    4: render_seq4_frame,
    5: render_seq5_frame
}

# =============================================================================
# 6. PRODUCTION AUDIO (VOIX OFF EDGE-TTS, MUSIQUE SYNTHÉTIQUE & SFX)
# =============================================================================

async def generate_voiceover_single(seq_cfg, work_dir):
    """Génère la voix off d'une seule séquence via Edge-TTS."""
    import edge_tts
    os.makedirs(work_dir, exist_ok=True)
    mp3_path = os.path.join(work_dir, f"{seq_cfg['name']}_raw.mp3")
    wav_path = os.path.join(work_dir, f"{seq_cfg['name']}_voice.wav")
    comm = edge_tts.Communicate(seq_cfg["voice_text"], "fr-FR-HenriNeural", rate="+4%")
    await comm.save(mp3_path)
    cmd = ["ffmpeg", "-y", "-i", mp3_path, "-ar", str(SAMPLE_RATE), "-ac", "1", wav_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return wav_path

async def generate_voiceovers(work_dir):
    """Génère les voix off neuronales Edge-TTS en français (fr-FR-HenriNeural)."""
    import edge_tts
    print("\n--- Étape 2.1 : Génération des voix off neuronales Edge-TTS ---")
    for s in SEQUENCES_CONFIG:
        mp3_path = os.path.join(work_dir, f"{s['name']}_raw.mp3")
        wav_path = os.path.join(work_dir, f"{s['name']}_voice.wav")
        
        if os.path.exists(wav_path):
            print(f"  ✓ Voix off déjà prête : {s['name']}")
            continue
            
        print(f"  -> Synthèse Edge-TTS ({s['name']})...")
        comm = edge_tts.Communicate(s["voice_text"], "fr-FR-HenriNeural", rate="+4%")
        await comm.save(mp3_path)
        
        # Conversion 44.1kHz mono WAV
        cmd = ["ffmpeg", "-y", "-i", mp3_path, "-ar", str(SAMPLE_RATE), "-ac", "1", wav_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  ✓ Converti en WAV : {wav_path}")

def synthesize_tech_music(duration_sec, out_path):
    """Synthèse procédurale d'un beat électro moderne à 120 BPM."""
    if os.path.exists(out_path):
        return
        
    print(f"\n--- Étape 2.2 : Synthèse de la musique électro-tech ({duration_sec:.1f}s) ---")
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    audio = np.zeros_like(t)
    
    bpm = 120.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    total_samples = len(t)
    
    # 1. Kick Drum (descente 140Hz -> 45Hz)
    k_samples = int(SAMPLE_RATE * 0.25)
    t_k = np.linspace(0, 0.25, k_samples, endpoint=False)
    f_k = 140.0 * np.exp(-t_k * 30.0) + 45.0
    phase_k = 2 * np.pi * np.cumsum(f_k) / SAMPLE_RATE
    kick = np.sin(phase_k) * np.exp(-t_k * 14.0)
    click = np.random.uniform(-1, 1, int(SAMPLE_RATE * 0.008)) * np.exp(-np.linspace(0, 1, int(SAMPLE_RATE * 0.008)) * 10)
    kick[:len(click)] += click * 0.4
    
    # 2. Snare / Clack
    s_samples = int(SAMPLE_RATE * 0.2)
    t_s = np.linspace(0, 0.2, s_samples, endpoint=False)
    noise_s = np.random.uniform(-1, 1, s_samples) * np.exp(-t_s * 25.0)
    body_s = np.sin(2 * np.pi * 180 * t_s) * np.exp(-t_s * 30.0)
    snare = 0.6 * noise_s + 0.4 * body_s
    
    # 3. Hi-Hat
    h_samples = int(SAMPLE_RATE * 0.06)
    t_h = np.linspace(0, 0.06, h_samples, endpoint=False)
    hat = np.random.uniform(-1, 1, h_samples) * np.exp(-t_h * 80.0)
    
    num_beats = int(duration_sec / beat_dur)
    for b in range(num_beats):
        pos = int(b * beat_dur * SAMPLE_RATE)
        drum_vol = 0.35 if b < 8 else 0.55
        if pos + len(kick) < total_samples:
            audio[pos:pos + len(kick)] += kick * drum_vol
            
        if b >= 4 and (b % 4 == 1 or b % 4 == 3):
            if pos + len(snare) < total_samples:
                audio[pos:pos + len(snare)] += snare * (drum_vol * 0.5)
                
        h_pos1 = pos
        h_pos2 = pos + int(beat_dur * 0.5 * SAMPLE_RATE)
        if b >= 2:
            if h_pos1 + len(hat) < total_samples:
                audio[h_pos1:h_pos1 + len(hat)] += hat * 0.15
            if h_pos2 + len(hat) < total_samples:
                audio[h_pos2:h_pos2 + len(hat)] += hat * 0.22
                
    # 4. Bassline (Dm, Bb, F, C)
    chords_bass = [73.42, 58.27, 87.31, 65.41]
    bass_track = np.zeros_like(t)
    eighth_samples = int(SAMPLE_RATE * (beat_dur / 2.0))
    for bar_idx in range(int(duration_sec / bar_dur) + 1):
        root_f = chords_bass[bar_idx % 4]
        for step in range(8):
            step_idx = bar_idx * 8 + step
            start_pos = int(step_idx * (beat_dur / 2.0) * SAMPLE_RATE)
            if start_pos >= total_samples:
                break
            step_len = min(eighth_samples, total_samples - start_pos)
            t_step = np.linspace(0, step_len / SAMPLE_RATE, step_len, endpoint=False)
            f = root_f * 2 if step in [2, 5, 7] else root_f
            env = np.exp(-t_step * 12.0)
            bass_note = (np.sin(2 * np.pi * f * t_step) + 
                         0.5 * np.sin(2 * np.pi * 2 * f * t_step) + 
                         0.25 * np.sin(2 * np.pi * 3 * f * t_step)) * env
            bass_track[start_pos:start_pos + step_len] += bass_note * 0.35
            
    # 5. Arpège mélodique Tech
    chord_notes = [
        [293.66, 349.23, 440.00, 587.33],
        [233.08, 293.66, 349.23, 466.16],
        [174.61, 261.63, 349.23, 440.00],
        [261.63, 329.63, 392.00, 523.25]
    ]
    arp_track = np.zeros_like(t)
    sixteenth_samples = int(SAMPLE_RATE * (beat_dur / 4.0))
    for bar_idx in range(int(duration_sec / bar_dur) + 1):
        c_notes = chord_notes[bar_idx % 4]
        pattern = [0, 1, 2, 3, 2, 1, 3, 2, 1, 2, 3, 2, 0, 1, 2, 3]
        for step in range(16):
            step_idx = bar_idx * 16 + step
            start_pos = int(step_idx * (beat_dur / 4.0) * SAMPLE_RATE)
            if start_pos >= total_samples:
                break
            step_len = min(sixteenth_samples, total_samples - start_pos)
            t_step = np.linspace(0, step_len / SAMPLE_RATE, step_len, endpoint=False)
            note_freq = c_notes[pattern[step % len(pattern)] % len(c_notes)]
            env = np.exp(-t_step * 25.0)
            pluck = (np.sin(2 * np.pi * note_freq * t_step) + 
                     0.3 * np.sin(2 * np.pi * 2 * note_freq * t_step)) * env
            arp_track[start_pos:start_pos + step_len] += pluck * 0.22
            
    # 6. Pad ambiant
    pad_track = np.zeros_like(t)
    for bar_idx in range(int(duration_sec / bar_dur) + 1):
        c_notes = chord_notes[bar_idx % 4]
        bar_start = int(bar_idx * bar_dur * SAMPLE_RATE)
        bar_len = min(int(bar_dur * SAMPLE_RATE), total_samples - bar_start)
        if bar_len <= 0:
            break
        t_bar = np.linspace(0, bar_len / SAMPLE_RATE, bar_len, endpoint=False)
        win = np.sin(np.pi * t_bar / bar_dur)
        pad = sum(np.sin(2 * np.pi * (f / 2.0) * t_bar) for f in c_notes[:3]) / 3.0
        pad_track[bar_start:bar_start + bar_len] += pad * win * 0.18
        
    music = audio + bass_track + arp_track + pad_track
    fade_in = min(int(0.5 * SAMPLE_RATE), total_samples)
    music[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = min(int(2.5 * SAMPLE_RATE), total_samples)
    music[-fade_out:] *= np.linspace(1, 0, fade_out)
    
    max_val = np.max(np.abs(music))
    if max_val > 0:
        music = (music / max_val) * 0.82
        
    wav.write(out_path, SAMPLE_RATE, (music * 32767).astype(np.int16))
    print(f"  ✓ Piste musicale enregistrée : {out_path}")

def synthesize_sfx(work_dir):
    """Génère les effets sonores procéduraux (whoosh, impact, click, success)."""
    sfx_map = {}
    
    # 1. Whoosh
    w_path = os.path.join(work_dir, "sfx_whoosh.wav")
    if not os.path.exists(w_path):
        dur = 0.7
        samples = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, samples, endpoint=False)
        noise = np.random.uniform(-1, 1, samples)
        env = np.sin(np.pi * t / dur) ** 2
        sweep = np.sin(2 * np.pi * (100 + 1200 * (t / dur) ** 2) * t)
        whoosh = (0.7 * noise + 0.3 * sweep) * env
        whoosh = (whoosh / np.max(np.abs(whoosh))) * 0.75
        wav.write(w_path, SAMPLE_RATE, (whoosh * 32767).astype(np.int16))
    sfx_map["whoosh"] = w_path
    
    # 2. Impact sub-bass
    i_path = os.path.join(work_dir, "sfx_impact.wav")
    if not os.path.exists(i_path):
        dur = 1.0
        samples = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, samples, endpoint=False)
        sub = np.sin(2 * np.pi * (110 * np.exp(-t * 6.0) + 38) * t) * np.exp(-t * 4.0)
        click = np.random.uniform(-1, 1, int(SAMPLE_RATE * 0.02)) * np.exp(-np.linspace(0, 1, int(SAMPLE_RATE * 0.02)) * 8)
        impact = sub.copy()
        impact[:len(click)] += click * 0.5
        impact = (impact / np.max(np.abs(impact))) * 0.85
        wav.write(i_path, SAMPLE_RATE, (impact * 32767).astype(np.int16))
    sfx_map["impact"] = i_path
    
    # 3. Clic UI moderne
    c_path = os.path.join(work_dir, "sfx_click.wav")
    if not os.path.exists(c_path):
        dur = 0.12
        samples = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, samples, endpoint=False)
        click_tone = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 45.0) + np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 60.0) * 0.5
        click_tone = (click_tone / np.max(np.abs(click_tone))) * 0.6
        wav.write(c_path, SAMPLE_RATE, (click_tone * 32767).astype(np.int16))
    sfx_map["click"] = c_path
    
    # 4. Carillon de succès
    s_path = os.path.join(work_dir, "sfx_success.wav")
    if not os.path.exists(s_path):
        dur = 0.9
        samples = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, samples, endpoint=False)
        bell = (np.sin(2 * np.pi * 880 * t) * np.exp(-t * 5.0) + 
                0.6 * np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 6.0) + 
                0.4 * np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 7.0))
        bell = (bell / np.max(np.abs(bell))) * 0.7
        wav.write(s_path, SAMPLE_RATE, (bell * 32767).astype(np.int16))
    sfx_map["success"] = s_path
    
    return sfx_map

def load_wav_as_float(path):
    """Charge un fichier WAV sous forme de tableau float32 normalisé entre -1 et 1."""
    sr, data = wav.read(path)
    if data.ndim > 1:
        data = data[:, 0]
    if data.dtype == np.int16:
        return data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        return data.astype(np.float32) / 2147483648.0
    return data.astype(np.float32)

def mix_audio_tracks(work_dir, target_sequence_id=None):
    """Mixe la voix off, la musique avec ducking et les SFX pour chaque séquence."""
    print("\n--- Étape 2.3 : Mixage dynamique & compression sidechain ---")
    sfx_files = synthesize_sfx(work_dir)
    loaded_sfx = {k: load_wav_as_float(v) for k, v in sfx_files.items()}
    
    music_full_path = os.path.join(work_dir, "music_track.wav")
    total_duration = sum(s["duration"] for s in SEQUENCES_CONFIG) + 2.0
    synthesize_tech_music(total_duration, music_full_path)
    music_full = load_wav_as_float(music_full_path)
    
    global_time = 0.0
    audio_paths = {}
    
    for s in SEQUENCES_CONFIG:
        dur = s["duration"]
        if target_sequence_id is not None and s["id"] != target_sequence_id:
            global_time += dur
            continue
            
        num_samples = int(dur * SAMPLE_RATE)
        mix = np.zeros(num_samples, dtype=np.float32)
        
        # 1. Piste voix off
        voice_path = os.path.join(work_dir, f"{s['name']}_voice.wav")
        if not os.path.exists(voice_path):
            print(f"  -> Génération à la volée de la voix off pour {s['name']}...")
            asyncio.run(generate_voiceover_single(s, work_dir))
            
        voice = load_wav_as_float(voice_path)
        v_peak = np.max(np.abs(voice))
        if v_peak > 0:
            voice = (voice / v_peak) * 0.92
        v_len = min(len(voice), num_samples)
        mix[:v_len] += voice[:v_len]
        
        # 2. Ducking de la musique (abaissement du volume lors de la parole)
        hop = int(SAMPLE_RATE * 0.05)
        win = int(SAMPLE_RATE * 0.1)
        env = np.zeros(num_samples, dtype=np.float32)
        padded_v = np.pad(voice[:v_len], (0, max(0, num_samples - v_len)))
        for i in range(0, num_samples - win, hop):
            rms = np.sqrt(np.mean(padded_v[i:i + win] ** 2))
            env[i:i + hop] = rms
        smooth_len = int(SAMPLE_RATE * 0.2)
        env = np.convolve(env, np.ones(smooth_len) / smooth_len, mode='same')
        duck_factor = np.clip(1.0 - (env / 0.15), 0.0, 1.0)
        music_vol = 0.16 + 0.22 * duck_factor
        
        # 3. Tranche musicale correspondante
        m_start = int(global_time * SAMPLE_RATE)
        m_end = m_start + num_samples
        if m_end <= len(music_full):
            m_slice = music_full[m_start:m_end]
        else:
            m_slice = np.pad(music_full[m_start:], (0, m_end - len(music_full)))
        mix += m_slice[:num_samples] * music_vol
        
        # 4. SFX minutés
        for sfx_name, sfx_t, sfx_gain in s["sfx"]:
            sfx_samp = loaded_sfx[sfx_name]
            pos = int(sfx_t * SAMPLE_RATE)
            end_pos = min(pos + len(sfx_samp), num_samples)
            actual_len = end_pos - pos
            if actual_len > 0:
                mix[pos:end_pos] += sfx_samp[:actual_len] * sfx_gain
                
        # 5. Limiteur / Normalisation
        peak = np.max(np.abs(mix))
        if peak > 0.95:
            mix = (mix / peak) * 0.95
            
        out_wav = os.path.join(work_dir, f"{s['name']}_audio.wav")
        wav.write(out_wav, SAMPLE_RATE, (mix * 32767).astype(np.int16))
        audio_paths[s["id"]] = out_wav
        print(f"  ✓ Audio mixé : {s['name']} ({dur:.2f}s, crête={peak:.2f})")
        
        global_time += dur
        
    return audio_paths

# =============================================================================
# 7. MOTEUR D'ENCODAGE ET D'ASSEMBLAGE FFmpeg
# =============================================================================

def render_sequence_video(seq_cfg, audio_path, out_dir):
    """Rendu d'une séquence vidéo en injectant les images brutes dans FFmpeg."""
    seq_id = seq_cfg["id"]
    seq_name = seq_cfg["name"]
    duration = seq_cfg["duration"]
    num_frames = int(duration * FPS)
    out_mp4 = os.path.join(out_dir, f"{seq_name}.mp4")
    render_func = RENDERERS[seq_id]
    
    print(f"\n>>> Rendu vidéo : {seq_name} ({duration}s, {num_frames} frames)...")
    start_t = time.time()
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_mp4
    ]
    
    # stderr de FFmpeg est redirigé vers un fichier temporaire (et non un PIPE)
    # pour éviter tout deadlock pendant le streaming de frames volumineuses.
    err_buf = tempfile.TemporaryFile()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_buf)

    for f_idx in range(num_frames):
        t = f_idx / float(FPS)
        frame_img = render_func(t)
        proc.stdin.write(frame_img.tobytes())

    proc.stdin.close()
    proc.wait()
    err_buf.seek(0)
    stderr = err_buf.read()
    err_buf.close()

    elapsed = time.time() - start_t
    if proc.returncode != 0:
        print(f"Erreur lors du rendu FFmpeg pour {seq_name}:\n{stderr.decode(errors='replace')}", file=sys.stderr)
        raise RuntimeError(f"FFmpeg a échoué avec le code d'erreur {proc.returncode}")
        
    size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    fps_perf = num_frames / elapsed if elapsed > 0 else 0
    print(f"  ✓ Séquence finalisée : {out_mp4} ({elapsed:.1f}s, {fps_perf:.1f} fps, {size_mb:.2f} MB)")
    return out_mp4

def concatenate_master_video(clip_paths, out_dir):
    """Concatène les 5 séquences MP4 en un master final officiel sans ré-encodage."""
    concat_list_path = os.path.join(out_dir, "concat_manifest.txt")
    with open(concat_list_path, "w") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
            
    final_output = os.path.join(out_dir, "MyNichePilot_Publicite_Officielle_9x16.mp4")
    print(f"\n>>> Concaténation des 5 séquences dans le master final...")
    
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        final_output
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
    size_mb = os.path.getsize(final_output) / (1024 * 1024)
    print(f"  🎉 MASTER VIDÉO FINAL TERMINÉ : {final_output} ({size_mb:.2f} MB)")
    return final_output

# =============================================================================
# 8. POINT D'ENTRÉE PRINCIPAL (CLI & ORCHESTRATION)
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="MyNichePilot - Générateur Autonome de Vidéo Publicitaire 9:16")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Répertoire de sortie des vidéos générées")
    parser.add_argument("--work-dir", default="/tmp/mynichepilot_work", help="Répertoire de travail intermédiaire")
    parser.add_argument("--skip-audio", action="store_true", help="Réutiliser les fichiers audio déjà générés")
    parser.add_argument("--sequence", type=int, choices=[1, 2, 3, 4, 5], help="Générer uniquement la séquence indiquée")
    parser.add_argument("--variation", default=None, choices=["static", "llm", "saas"],
                        help="Fournisseur de contenu variable (défaut: env CONTENT_PROVIDER ou static)")
    return parser.parse_args()

def apply_content_variation(args):
    """Régénère titres, voix off et sous-titres via l'IA (LLM/SaaS) si configuré."""
    variation = (getattr(args, "variation", None) or os.environ.get("CONTENT_PROVIDER", "static")).lower()
    if variation == "static":
        return
    try:
        import content_generator as cg
    except Exception as exc:
        print(f"  ⚠ Module content_generator indisponible : {exc}")
        return
    cg.CONFIG["provider"] = variation
    seqs = [{"id": s["id"], "name": s["name"], "title": s["title"],
             "duration": s["duration"], "voice_text": s["voice_text"]} for s in SEQUENCES_CONFIG]
    campaign = cg.generate_campaign(seqs)
    if not campaign:
        print(f"  ⚠ Contenu IA ({variation}) indisponible — script par défaut conservé.")
        return
    seq_map = {}
    for x in (campaign.get("sequences") or []):
        seq_map[x.get("id")] = x
        seq_map[str(x.get("id"))] = x
    changed = 0
    for s in SEQUENCES_CONFIG:
        c = seq_map.get(s["id"])
        if not c:
            continue
        if c.get("voice_text"):
            s["voice_text"] = c["voice_text"]
            set_dynamic_subtitles(s["id"], c["voice_text"], s["duration"])
            changed += 1
        if c.get("title"):
            s["title"] = c["title"]
    cg.write_content_cache(campaign)
    print(f"  ✓ Contenu IA appliqué ({variation}) : {changed}/5 séquences variées.")


def main():
    args = parse_args()
    total_start = time.time()
    
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.work_dir, exist_ok=True)
    
    print("=======================================================================")
    print("🚀 DÉMARRAGE DU PIPELINE VIDÉO MYNICHEPILOT (1080x1920 @ 30 FPS)")
    print("=======================================================================")
    print(f"  • Répertoire de sortie : {args.output_dir}")
    print(f"  • Répertoire temporaire : {args.work_dir}")
    print(f"  • Format vidéo : 9:16 vertical (1080x1920)")
    print(f"  • Durée totale cible : 44.30 secondes (5 séquences)")
    print("=======================================================================")

    # 0. Contenu variable (IA : LLM / SaaS) — optionnel, repli silencieux
    apply_content_variation(args)

    # 1. Initialisation des polices et assets
    print("\n--- Étape 1 : Initialisation des assets et de la charte ---")
    init_assets()
    print("  ✓ Assets vectoriels et fond cosmique initialisés.")
    
    # 2. Production Audio
    if not args.skip_audio:
        asyncio.run(generate_voiceovers(args.work_dir))
    audio_paths = mix_audio_tracks(args.work_dir, target_sequence_id=args.sequence)
    
    # 3. Rendu Vidéo
    clip_paths = []
    sequences_to_run = [s for s in SEQUENCES_CONFIG if args.sequence is None or s["id"] == args.sequence]
    
    print("\n--- Étape 3 : Rendu dynamique des scènes et encodage H.264 ---")
    for s in sequences_to_run:
        clip_path = render_sequence_video(s, audio_paths[s["id"]], args.output_dir)
        clip_paths.append(clip_path)
        
    # 4. Assemblage final
    if args.sequence is None:
        final_video = concatenate_master_video(clip_paths, args.output_dir)
        total_time = time.time() - total_start
        print("\n=======================================================================")
        print(f"✅ PRODUCTION ACCOMPLIE AVEC SUCCÈS EN {total_time:.1f} SECONDES !")
        print(f"  Livrable prêt à la diffusion : {final_video}")
        print("=======================================================================")

if __name__ == "__main__":
    main()
