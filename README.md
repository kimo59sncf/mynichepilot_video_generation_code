# 🚀 MyNichePilot — Suite Complète de Génération Vidéo Publicitaire 9:16

Ce package contient l'intégralité du code source, des scripts de synthèse procédurale, des assets de marque et de la documentation permettant de reproduire fidèlement, de façon 100 % autonome et de bout en bout, la publicité vidéo officielle pour **MyNichePilot** ([https://mynichepilot.com](https://mynichepilot.com)).

---

## 📌 Présentation du Projet

- **Format cible** : Vidéo verticale smartphone **9:16 (1080 × 1920 pixels)**
- **Cadence** : **30 images par seconde (FPS)**
- **Durée totale** : **44,30 secondes** réparties en **5 séquences narratives continues**
- **Encodage** : Vidéo H.264 (CRF 18, profil High, pix_fmt yuv420p) / Audio AAC stéréo 192 kbps
- **Branding** : Charte graphique officielle MyNichePilot (univers Nuit Cosmique, or ambré, typographies Playfair Display et Inter, boussole dorée vectorielle)
- **Voix off** : Voix neuronale française masculine dynamique et crédible (`fr-FR-HenriNeural`) via Edge-TTS
- **Sound Design** : Piste musicale électro/tech procédurale à 120 BPM et 4 bruitages SFX synthétisés par code (whoosh, impact sub-bass, clics UI, carillon de succès)
- **Mixage** : Ducking automatique (sidechain) abaissant la musique de -8 dB lors des prises de parole

---

## 🏗️ Architecture du Pipeline

Le générateur fonctionne selon un pipeline direct sans fichiers intermédiaires superflus :

```
                                  ┌───────────────────────────────┐
                                  │      Edge-TTS (fr-FR-Henri)   │
                                  │   Synthèse Voix Off Séquences │
                                  └───────────────┬───────────────┘
                                                  │
┌─────────────────────────────┐   ┌───────────────▼───────────────┐   ┌─────────────────────────────┐
│  Synthèse Musique (120 BPM) │   │  Mixage Audio avec Ducking    ├──►│ Fichiers Audio Synchronisés │
│  + SFX procéduraux (SciPy)  ├──►│  & Bruitages SFX Positionnés  │   │   sequence_X_audio.wav      │
└─────────────────────────────┘   └───────────────────────────────┘   └──────────────┬──────────────┘
                                                                                     │
┌─────────────────────────────┐   ┌───────────────────────────────┐                  │
│   Moteur Graphique Pillow   │   │  Streaming Pipe Stdin RGB24   │                  │
│    Rendu des frames 30 FPS  ├──►│  FFmpeg libx264 1080x1920     │◄─────────────────┘
│  (Titres, UI, Particules,   │   └───────────────┬───────────────┘
│   Roadmap, Sous-titres)     │                   │
└─────────────────────────────┘                   ▼
                                  ┌───────────────────────────────┐
                                  │  5 Clips MP4 Haute Définition │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼ Concaténation Master
                                  ┌───────────────────────────────┐
                                  │  Master Publicitaire Officiel │
                                  │ MyNichePilot_Publicite_9x16   │
                                  └───────────────────────────────┘
```

---

## 📁 Structure du Répertoire

```
mynichepilot_video_generation_code/
│
├── generate_video_mynichepilot.py   # Script principal tout-en-un (CLI & production complète)
├── run_pipeline.sh                  # Script bash automatisé avec vérifications d'environnement
├── requirements.txt                 # Dépendances Python requises
├── README.md                        # Documentation technique détaillée
│
├── assets/                          # Actifs visuels officiels MyNichePilot
│   ├── base_bg.png                  # Fond cosmique dégradé 135° (1080x1920) avec halos
│   ├── compass_icon_512.png         # Icône boussole dorée dans squircle (512x512)
│   ├── mynichepilot-app-icon-512x512.png  # Icône d'application officielle
│   └── mynichepilot-favicon.svg     # Favicon vectoriel officiel
│
├── fonts/                           # Typographies officielles embarquées
│   ├── PlayfairDisplay-Variable.ttf # Titres éditoriaux et prestige de marque
│   ├── Inter-Variable.ttf           # Interface, labels, badges et sous-titres
│   └── Roboto-Variable.ttf          # Police complémentaire
│
└── scripts/                         # Modules indépendants
    ├── create_assets.py             # Régénération autonome du fond cosmique et du logo
    ├── generate_audio.py            # Génération isolée des voix, de la musique et des SFX
    └── render_video.py              # Rendu graphique isolé et pipeline FFmpeg
```

---

## 🎬 Découpage des 5 Séquences Vidéo

| Séquence | Durée | Rôle Narratif | Éléments Visuels Clés | Voix Off Officielle |
| :--- | :---: | :--- | :--- | :--- |
| **Seq 1 : Hook** | **8,60 s** | Choc & Surcharge mentale | 4 cartes d'idées flottantes, alerte rouge clignotante, barre de clarté 0% | *"Tu veux lancer ton business en ligne, mais tu ne sais pas quelle niche choisir ? Trop d'idées confuses, zéro plan clair et une vraie surcharge mentale."* |
| **Seq 2 : Problème** | **9,20 s** | Douleur vs Solution | Blocage 6 mois, zoom boussole dorée, badge AI, 3 piliers fondateurs | *"Analyser la concurrence prend des semaines, et le risque d'échec est énorme. Voici NichePilot, le coach IA d'exécution business qui change la donne."* |
| **Seq 3 : Démo SaaS** | **9,50 s** | Preuve & Cockpit | Laser de scan cyan, compteur dynamique 18 à 94/100, métriques réelles, roadmap 16 sem. | *"Regarde ça : diagnostic en direct, score de potentiel validé à 94 sur 100, opportunités rentables détectées et une roadmap concrète sur 16 semaines."* |
| **Seq 4 : Transformation**| **8,50 s** | Avant vs Après | Carte rouge "Avant" vs carte émeraude "Avec NichePilot", flèche animée, 4 bénéfices | *"Finie la confusion ! Tu passes instantanément du doute à la certitude absolue : ta niche est validée, et ton offre irrésistible est prête à vendre."* |
| **Seq 5 : Call to Action**| **8,50 s** | Conclusion & Conversion | Boussole pulsante, 4 garanties, bouton CTA ambré pulsant, lien URL avec soulignement | *"Ne laisse plus tes idées au placard. Rends-toi dès aujourd'hui sur mynichepilot.com, fais ton diagnostic gratuit et lance ton business !"* |

---

## ⚙️ Prérequis Système

1. **Python 3.10 ou supérieur**
2. **FFmpeg** avec le support de `libx264` et de l'audio `aac` :
   - **Ubuntu / Debian** : `sudo apt update && sudo apt install -y ffmpeg`
   - **macOS** : `brew install ffmpeg`
   - **Windows** : Télécharger FFmpeg via [ffmpeg.org](https://ffmpeg.org/download.html) ou `winget install Gyan.FFmpeg`
3. **Accès réseau** lors de la première exécution pour la synthèse vocale neuronale Microsoft Edge-TTS (les sons procéduraux et graphismes fonctionnent 100 % hors-ligne).

---

## 🚀 Guide de Démarrage Rapide

### Option A : Lancement automatique en une commande (Bash)
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

### Option B : Lancement manuel via Python
```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Exécuter le générateur complet
python3 generate_video_mynichepilot.py
```

Les fichiers finaux seront automatiquement écrits dans le répertoire `./output/` :
- `MyNichePilot_Publicite_Officielle_9x16.mp4` (Master complet assemblé)
- `sequence_1_hook.mp4`
- `sequence_2_probleme_solution.mp4`
- `sequence_3_demonstration_saas.mp4`
- `sequence_4_transformation.mp4`
- `sequence_5_call_to_action.mp4`

---

## 🎛️ Options de la Ligne de Commande (CLI)

Le script maître `generate_video_mynichepilot.py` intègre plusieurs arguments utiles :

```bash
# Spécifier un dossier de sortie personnalisé
python3 generate_video_mynichepilot.py --output-dir /chemin/vers/mes_videos

# Rendre uniquement une séquence précise (par exemple la séquence 3)
python3 generate_video_mynichepilot.py --sequence 3

# Réutiliser les fichiers audio déjà générés sans ré-interroger Edge-TTS
python3 generate_video_mynichepilot.py --skip-audio
```

---

## 🖥️ Interface VIP (Dashboard Web Local)

Le projet inclut une interface moderne de pilotage « Nuit Cosmique » (aucune dépendance supplémentaire — 100 % bibliothèque standard). Elle permet de :

- **Superviser** les 5 séquences, la charte graphique et l'état du système (Python, FFmpeg, dépendances) ;
- **Lancer / arrêter** la production (pipeline complet ou séquence ciblée, option `--skip-audio`, dossier de sortie) ;
- **Suivre en temps réel** l'exécution via une console de logs (SSE) et une barre de progression par étape ;
- **Prévisualiser et télécharger** les vidéos MP4 générées (streaming avec support des requêtes `Range`).

### Lancement (Windows)

Double-cliquez simplement sur :

```
launch_interface.bat
```

Le navigateur s'ouvre automatiquement sur `http://127.0.0.1:8000`.

### Lancement manuel

```bash
python server.py --host 127.0.0.1 --port 8000
```

Puis ouvrez [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Fichiers ajoutés

```
server.py                 # Backend HTTP local (API REST + SSE + streaming vidéo)
web/index.html            # Interface (structure)
web/style.css             # Thème « Nuit Cosmique » (or ambré, glassmorphism, animations)
web/app.js                # Logique applicative (pilotage, SSE, rendu dynamique)
launch_interface.bat      # Lanceur double-clic Windows
```

| Endpoint | Rôle |
| :--- | :--- |
| `GET /api/health` | État des dépendances + FFmpeg + générateur |
| `GET /api/config` | Séquences, palette, format (1080×1920 @ 30 FPS) |
| `GET /api/status` | État du pipeline (idle / running / finished) |
| `POST /api/run` | Lance une production (`sequence`, `skip_audio`, `output_dir`) |
| `POST /api/stop` | Interrompt la production en cours |
| `GET /api/events` | Flux SSE des logs en temps réel |
| `GET /api/videos` | Liste des MP4 générés |
| `GET /api/video/<fichier>` | Streaming / prévisualisation vidéo (Range) |

---

## 🎨 Charte Graphique & Palette Chromatique

| Rôle | Teinte Hex | RGB | Utilisation |
| :--- | :--- | :--- | :--- |
| **Fond Cosmique Nuit** | `#000b15` → `#091039` → `#000e1e` | `(0, 11, 21)` → `(9, 16, 57)` | Fond héroïque immersif |
| **Bleu Nuit Conteneurs** | `#101a40` / `#162455` | `(16, 26, 64)` / `(22, 36, 85)` | Cartes d'interface, cockpit SaaS |
| **Or Chaleureux / Ambre**| `#eca760` / `#eb883b` | `(236, 167, 96)` / `(235, 136, 59)`| Boutons d'action, accents majeurs |
| **Or Clair / Badge** | `#fcd34d` | `(252, 211, 77)` | Particules dorées, score 94/100, badge AI |
| **Vert Émeraude Succès**| `#34d399` | `(52, 211, 153)` | "Validé", badge En direct, coche verte |
| **Bleu Cyan Données** | `#60a5fa` | `(96, 165, 250)` | Rayon laser de scan, roadmap |
| **Rouge Alerte** | `#ef4444` | `(239, 68, 68)` | Cartes d'alerte surcharge mentale |

---

## 🔧 Dépannage & FAQ

### Pourquoi utiliser le streaming par Stdin plutôt que d'écrire des PNG sur disque ?
L'écriture de 1 330 images PNG individuelles sur disque génère des goulets d'étranglement d'entrées/sorties disque considérables (plusieurs gigaoctets écrits puis relus). Le streaming en mémoire via `proc.stdin.write(frame.tobytes())` transmet directement les pixels RGB24 au décodeur FFmpeg en RAM, réduisant le temps de génération d'un facteur 4 à 6.

### Que faire si les polices Playfair Display ou Inter ne sont pas trouvées ?
Le script intègre une recherche locale automatique dans le sous-dossier `./fonts/` inclus dans l'archive. Si vous exécutez le script dans un autre environnement, il se repliera automatiquement sur les polices système Truetype ou les polices par défaut de Pillow sans jamais planter.

### Comment modifier les textes des sous-titres ou de la voix off ?
Éditez simplement le dictionnaire `SEQUENCES_CONFIG` au début de `generate_video_mynichepilot.py`. La durée cible, les prompts voix off et les déclencheurs de sous-titres y sont clairement déclarés et commentés.

---

**MyNichePilot** — *Le coach IA d'exécution business pour solopreneurs et créateurs d'entreprise.*  
Site officiel : [https://mynichepilot.com](https://mynichepilot.com)
