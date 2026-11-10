#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot - Générateur Audio & Sound Design Procédural
=============================================================================
Module autonome chargé de :
1. La génération des voix off Edge-TTS en français
2. La synthèse de la piste musicale électro-tech (120 BPM)
3. La synthèse des 4 bruitages SFX (whoosh, impact, click, success)
4. Le mixage dynamique avec sidechain ducking par séquence
"""

import os
import sys
import asyncio
import subprocess
import numpy as np
import scipy.io.wavfile as wav

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mynichepilot_work"

SAMPLE_RATE = 44100

SEQUENCES = [
    {
        "id": 1,
        "name": "sequence_1_hook",
        "duration": 8.60,
        "text": "Tu veux lancer ton business en ligne, mais tu ne sais pas quelle niche choisir ? Trop d'idées confuses, zéro plan clair et une vraie surcharge mentale.",
        "sfx": [("impact", 0.05, 0.45), ("click", 3.0, 0.40), ("whoosh", 7.9, 0.55)]
    },
    {
        "id": 2,
        "name": "sequence_2_probleme_solution",
        "duration": 9.20,
        "text": "Analyser la concurrence prend des semaines, et le risque d'échec est énorme. Voici NichePilot, le coach IA d'exécution business qui change la donne.",
        "sfx": [("whoosh", 0.05, 0.40), ("click", 1.8, 0.35), ("click", 3.2, 0.35), ("impact", 4.5, 0.60), ("click", 6.8, 0.40)]
    },
    {
        "id": 3,
        "name": "sequence_3_demonstration_saas",
        "duration": 9.50,
        "text": "Regarde ça : diagnostic en direct, score de potentiel validé à 94 sur 100, opportunités rentables détectées et une roadmap concrète sur 16 semaines.",
        "sfx": [("whoosh", 0.05, 0.40), ("click", 1.2, 0.35), ("success", 4.2, 0.55), ("click", 6.2, 0.35), ("click", 7.8, 0.35)]
    },
    {
        "id": 4,
        "name": "sequence_4_transformation",
        "duration": 8.50,
        "text": "Finie la confusion ! Tu passes instantanément du doute à la certitude absolue : ta niche est validée, et ton offre irrésistible est prête à vendre.",
        "sfx": [("whoosh", 0.05, 0.40), ("impact", 2.2, 0.45), ("success", 3.8, 0.50), ("click", 5.5, 0.35), ("click", 7.0, 0.35)]
    },
    {
        "id": 5,
        "name": "sequence_5_call_to_action",
        "duration": 8.50,
        "text": "Ne laisse plus tes idées au placard. Rends-toi dès aujourd'hui sur mynichepilot.com, fais ton diagnostic gratuit et lance ton business !",
        "sfx": [("whoosh", 0.05, 0.40), ("click", 2.5, 0.35), ("impact", 4.0, 0.55), ("success", 4.3, 0.50)]
    }
]

async def generate_voiceovers(out_dir):
    import edge_tts
    os.makedirs(out_dir, exist_ok=True)
    print("--- 1. Synthèse vocale Edge-TTS (fr-FR-HenriNeural) ---")
    for s in SEQUENCES:
        mp3 = os.path.join(out_dir, f"{s['name']}_raw.mp3")
        wav_file = os.path.join(out_dir, f"{s['name']}_voice.wav")
        comm = edge_tts.Communicate(s["text"], "fr-FR-HenriNeural", rate="+4%")
        await comm.save(mp3)
        cmd = ["ffmpeg", "-y", "-i", mp3, "-ar", str(SAMPLE_RATE), "-ac", "1", wav_file]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  ✓ {s['name']}_voice.wav prêt.")

def synthesize_tech_music(duration_sec, out_path):
    print(f"--- 2. Synthèse procédurale de la musique de fond ({duration_sec:.1f}s) ---")
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    audio = np.zeros_like(t)
    bpm = 120.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    total_samples = len(t)
    
    # Kick
    k_samples = int(SAMPLE_RATE * 0.25)
    t_k = np.linspace(0, 0.25, k_samples, endpoint=False)
    f_k = 140.0 * np.exp(-t_k * 30.0) + 45.0
    phase_k = 2 * np.pi * np.cumsum(f_k) / SAMPLE_RATE
    kick = np.sin(phase_k) * np.exp(-t_k * 14.0)
    click = np.random.uniform(-1, 1, int(SAMPLE_RATE * 0.008)) * np.exp(-np.linspace(0, 1, int(SAMPLE_RATE * 0.008)) * 10)
    kick[:len(click)] += click * 0.4
    
    # Snare
    s_samples = int(SAMPLE_RATE * 0.2)
    t_s = np.linspace(0, 0.2, s_samples, endpoint=False)
    noise_s = np.random.uniform(-1, 1, s_samples) * np.exp(-t_s * 25.0)
    body_s = np.sin(2 * np.pi * 180 * t_s) * np.exp(-t_s * 30.0)
    snare = 0.6 * noise_s + 0.4 * body_s
    
    # Hat
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
                
    # Bass
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
            
    # Arp
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
            
    # Pad
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
    print("  ✓ Piste musicale enregistrée.")

def synthesize_sfx(out_dir):
    print("--- 3. Synthèse des effets sonores (SFX) ---")
    sfx = {}
    
    # Whoosh
    w_p = os.path.join(out_dir, "sfx_whoosh.wav")
    t = np.linspace(0, 0.7, int(SAMPLE_RATE * 0.7), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t))
    env = np.sin(np.pi * t / 0.7) ** 2
    sweep = np.sin(2 * np.pi * (100 + 1200 * (t / 0.7) ** 2) * t)
    w = (0.7 * noise + 0.3 * sweep) * env
    w = (w / np.max(np.abs(w))) * 0.75
    wav.write(w_p, SAMPLE_RATE, (w * 32767).astype(np.int16))
    sfx["whoosh"] = w_p
    
    # Impact
    i_p = os.path.join(out_dir, "sfx_impact.wav")
    t = np.linspace(0, 1.0, int(SAMPLE_RATE * 1.0), endpoint=False)
    sub = np.sin(2 * np.pi * (110 * np.exp(-t * 6.0) + 38) * t) * np.exp(-t * 4.0)
    click = np.random.uniform(-1, 1, int(SAMPLE_RATE * 0.02)) * np.exp(-np.linspace(0, 1, int(SAMPLE_RATE * 0.02)) * 8)
    imp = sub.copy()
    imp[:len(click)] += click * 0.5
    imp = (imp / np.max(np.abs(imp))) * 0.85
    wav.write(i_p, SAMPLE_RATE, (imp * 32767).astype(np.int16))
    sfx["impact"] = i_p
    
    # Click
    c_p = os.path.join(out_dir, "sfx_click.wav")
    t = np.linspace(0, 0.12, int(SAMPLE_RATE * 0.12), endpoint=False)
    cl = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 45.0) + np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 60.0) * 0.5
    cl = (cl / np.max(np.abs(cl))) * 0.6
    wav.write(c_p, SAMPLE_RATE, (cl * 32767).astype(np.int16))
    sfx["click"] = c_p
    
    # Success
    s_p = os.path.join(out_dir, "sfx_success.wav")
    t = np.linspace(0, 0.9, int(SAMPLE_RATE * 0.9), endpoint=False)
    bell = (np.sin(2 * np.pi * 880 * t) * np.exp(-t * 5.0) + 
            0.6 * np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 6.0) + 
            0.4 * np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 7.0))
    bell = (bell / np.max(np.abs(bell))) * 0.7
    wav.write(s_p, SAMPLE_RATE, (bell * 32767).astype(np.int16))
    sfx["success"] = s_p
    
    print("  ✓ SFX générés (whoosh, impact, click, success).")
    return sfx

def load_wav(path):
    sr, data = wav.read(path)
    if data.ndim > 1:
        data = data[:, 0]
    if data.dtype == np.int16:
        return data.astype(np.float32) / 32768.0
    return data.astype(np.float32)

def mix_all(work_dir):
    asyncio.run(generate_voiceovers(work_dir))
    sfx_paths = synthesize_sfx(work_dir)
    loaded_sfx = {k: load_wav(v) for k, v in sfx_paths.items()}
    
    music_path = os.path.join(work_dir, "music_track.wav")
    total_dur = sum(s["duration"] for s in SEQUENCES) + 2.0
    synthesize_tech_music(total_dur, music_path)
    music_full = load_wav(music_path)
    
    global_time = 0.0
    for s in SEQUENCES:
        dur = s["duration"]
        num_samples = int(dur * SAMPLE_RATE)
        mix = np.zeros(num_samples, dtype=np.float32)
        
        voice = load_wav(os.path.join(work_dir, f"{s['name']}_voice.wav"))
        v_peak = np.max(np.abs(voice))
        if v_peak > 0:
            voice = (voice / v_peak) * 0.92
        v_len = min(len(voice), num_samples)
        mix[:v_len] += voice[:v_len]
        
        # Ducking
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
        
        m_start = int(global_time * SAMPLE_RATE)
        m_end = m_start + num_samples
        m_slice = music_full[m_start:m_end] if m_end <= len(music_full) else np.pad(music_full[m_start:], (0, m_end - len(music_full)))
        mix += m_slice[:num_samples] * music_vol
        
        for sfx_name, sfx_t, sfx_gain in s["sfx"]:
            sfx_samp = loaded_sfx[sfx_name]
            pos = int(sfx_t * SAMPLE_RATE)
            end_pos = min(pos + len(sfx_samp), num_samples)
            actual_len = end_pos - pos
            if actual_len > 0:
                mix[pos:end_pos] += sfx_samp[:actual_len] * sfx_gain
                
        peak = np.max(np.abs(mix))
        if peak > 0.95:
            mix = (mix / peak) * 0.95
            
        out_wav = os.path.join(work_dir, f"{s['name']}_audio.wav")
        wav.write(out_wav, SAMPLE_RATE, (mix * 32767).astype(np.int16))
        print(f"✓ Mix terminé : {out_wav} ({dur:.2f}s)")
        global_time += dur

if __name__ == "__main__":
    mix_all(WORK_DIR)
