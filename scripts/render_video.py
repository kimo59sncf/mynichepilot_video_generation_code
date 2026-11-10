#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot - Moteur de Rendu Vidéo & Pipeline FFmpeg Stdin
=============================================================================
Module de rendu visuel par séquence et concaténation FFmpeg.
Appelle le moteur graphique de `generate_video_mynichepilot.py`.
"""

import os
import sys
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from generate_video_mynichepilot import (
    SEQUENCES_CONFIG,
    init_assets,
    render_sequence_video,
    concatenate_master_video
)

def main():
    parser = argparse.ArgumentParser(description="MyNichePilot - Rendu Vidéo Dédié")
    parser.add_argument("--sequence", type=int, choices=[1, 2, 3, 4, 5], help="Numéro de séquence (1 à 5)")
    parser.add_argument("--audio-dir", default="/tmp/mynichepilot_work", help="Dossier contenant les fichiers audio .wav")
    parser.add_argument("--output-dir", default=os.path.join(ROOT_DIR, "output"), help="Dossier de sortie")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    init_assets()

    seqs = [s for s in SEQUENCES_CONFIG if args.sequence is None or s["id"] == args.sequence]
    clip_paths = []
    for s in seqs:
        audio_path = os.path.join(args.audio_dir, f"{s['name']}_audio.wav")
        if not os.path.exists(audio_path):
            print(f"Erreur : fichier audio introuvable {audio_path}. Exécutez d'abord generate_audio.py", file=sys.stderr)
            sys.exit(1)
        clip_path = render_sequence_video(s, audio_path, args.output_dir)
        clip_paths.append(clip_path)

    if args.sequence is None:
        concatenate_master_video(clip_paths, args.output_dir)

if __name__ == "__main__":
    main()
