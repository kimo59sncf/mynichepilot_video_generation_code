#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot — Générateur de Contenu Variable (LLM / SaaS / Statique)
=============================================================================
Rend le script publicitaire NON déterministe : à chaque lancement, les
séquences (titre, voix off, hooks) et les hashtags peuvent être régénérés
par une IA au lieu d'utiliser le texte figé de `SEQUENCES_CONFIG`.

Trois fournisseurs ("providers"), choisis via `CONTENT_PROVIDER` (ou `--variation`) :

  • "static"  (défaut) : contenu fixe actuel (aucun appel réseau).
  • "llm"     : API Chat-Completions compatible OpenAI (configurable).
               Env : OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL.
  • "saas"    : API « Social-Script-Genius » (POST /api/generate).
               Env : SAAS_API_URL / SAAS_PLATFORM / SAAS_DURATION.

Tout échec => repli silencieux sur "static" : la production n'échoue jamais.
=============================================================================
"""

import json
import os
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "output", "_content_cache.json")


def _env(name, default=""):
    return (os.environ.get(name) or default).strip()


def _load_dotenv(path=None):
    """Charge un fichier `.env` simple (KEY=VALUE) — aucune dépendance externe.

    Ne remplace jamais une variable déjà présente dans l'environnement réel.
    """
    path = path or os.path.join(BASE_DIR, ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


# Charge `.env` avant de construire la configuration (clés LLM/SaaS)
_load_dotenv()


# -----------------------------------------------------------------------------
# Configuration (variables d'environnement)
# -----------------------------------------------------------------------------
CONFIG = {
    "provider": _env("CONTENT_PROVIDER", "static").lower(),
    "topic": _env("CONTENT_TOPIC",
                  "MyNichePilot, le coach IA d'execution business pour solopreneurs et createurs"),
    "openai_api_key": _env("OPENAI_API_KEY") or _env("AI_INTEGRATIONS_OPENAI_API_KEY"),
    "openai_base_url": _env("OPENAI_BASE_URL") or _env("AI_INTEGRATIONS_OPENAI_BASE_URL"),
    "openai_model": _env("OPENAI_MODEL", "gpt-4o-mini"),
    "openai_temperature": _env("OPENAI_TEMPERATURE", ""),
    "saas_api_url": _env("SAAS_API_URL", "http://localhost:5001/api"),
    "saas_platform": _env("SAAS_PLATFORM", "tiktok"),
    "saas_duration": _env("SAAS_DURATION", "1min"),
}

_NARRATIVE = [
    ("Hook choc", "surcharge mentale, trop d'idees, trouver sa niche"),
    ("Probleme & solution", "analyse concurrence lente, risque d'echec, coach IA NichePilot"),
    ("Demonstration SaaS", "diagnostic en direct, score 94/100, roadmap 16 semaines"),
    ("Transformation", "du doute a la certitude, niche validee, offre irresistible"),
    ("Appel a l'action", "diagnostic gratuit sur mynichepilot.com, lancer son business"),
]

_SYSTEM_PROMPT = (
    "Tu es un copywriter expert en publicites video courtes (format vertical 9:16). "
    "Tu reponds UNIQUEMENT avec un objet JSON valide, sans texte autour, sans ```. "
    "Le JSON doit respecter exactement cette forme : "
    '{"sequences":[{"id":1,"title":"...","voice_text":"...","hashtags":["#..."]}, ...],'
    '"campaign_hashtags":["#..."]}. '
    "Le champ voice_text est un script de voix off naturel, fluide, pret a lire, "
    "calibre pour durer exactement {duration} secondes (environ {words} mots en francais). "
    "Chaque sequence est en francais courant."
)


def _extract_json(text):
    """Tolère le Markdown et le texte parasite autour du JSON."""
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def _post_json(url, payload, headers, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise urllib.error.URLError(f"HTTP {e.code}: {detail[:400]}") from e

def _llm_generate(sequences):
    """Fournisseur LLM : un seul appel renvoie les 5 séquences variées."""
    key = CONFIG["openai_api_key"]
    base = CONFIG["openai_base_url"].rstrip("/")
    model = CONFIG["openai_model"]
    if not key or not base:
        return None

    user_parts = [f"Sujet : {CONFIG['topic']}", "Genere 5 sequences :"]
    for s in sequences:
        dur = s.get("duration", 9)
        words = max(12, int(dur * 2.4))
        idx = s["id"] - 1 if 0 <= s["id"] - 1 < len(_NARRATIVE) else 0
        label, theme = _NARRATIVE[idx]
        user_parts.append(
            f"Sequence {s['id']} — {label} ({theme}) : duree {dur}s (~{words} mots)."
        )
    user_prompt = "\n".join(user_parts) + "\nRenvoie le JSON attendu."

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    # `temperature` est omis par défaut : les modèles de raisonnement (série o/gpt-5)
    # le rejettent (400). Activez-le via OPENAI_TEMPERATURE si votre modèle le supporte.
    if CONFIG["openai_temperature"]:
        try:
            payload["temperature"] = float(CONFIG["openai_temperature"])
        except Exception:
            pass
    url = base + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    }
    data = _post_json(url, payload, headers)
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return _extract_json(content)


def _split_script(script, n):
    """Découpe un script en n segments équilibrés (par phrases)."""
    if not script:
        return []
    import re
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", script) if p.strip()]
    if len(parts) <= 1:
        words = script.split()
        k = max(1, len(words) // max(1, n))
        return [" ".join(words[i:i + k]) for i in range(0, len(words), k)]
    if len(parts) <= n:
        return parts
    chunk_size = max(1, round(len(parts) / n))
    return [" ".join(parts[i:i + chunk_size]) for i in range(0, len(parts), chunk_size)]


def _saas_generate(sequences):
    """Fournisseur SaaS : POST /api/generate de Social-Script-Genius."""
    url = CONFIG["saas_api_url"].rstrip("/") + "/generate"
    payload = {
        "prompt": CONFIG["topic"],
        "platform": CONFIG["saas_platform"],
        "duration": CONFIG["saas_duration"],
        "language": "fr",
    }
    headers = {"Content-Type": "application/json"}
    data = _post_json(url, payload, headers)
    if not isinstance(data, dict) or "error" in data:
        return None

    script = data.get("script", "")
    hashtags = data.get("hashtags") or []
    hooks = data.get("hooks") or []
    sentences = _split_script(script, len(sequences))
    result = {"campaign_hashtags": hashtags, "sequences": []}
    for i, s in enumerate(sequences):
        voice = sentences[i] if i < len(sentences) else ""
        title = hooks[i % len(hooks)] if hooks else s.get("title", "")
        seq_hashtags = hashtags[:3] if hashtags else []
        result["sequences"].append({
            "id": s["id"],
            "title": title or s.get("title", ""),
            "voice_text": voice or s.get("voice_text", ""),
            "hashtags": seq_hashtags,
        })
    return result


def generate_campaign(sequences):
    """Retourne le contenu varié (dict) ou None (=> valeurs par défaut)."""
    if not sequences:
        return None
    provider = CONFIG["provider"]
    try:
        if provider == "llm":
            return _llm_generate(sequences)
        if provider == "saas":
            return _saas_generate(sequences)
    except Exception as exc:
        print(f"[content_generator] fournisseur '{provider}' indisponible ({exc}) — repli statique.")
        return None
    return None


def write_content_cache(campaign):
    """Persiste le contenu généré pour captions.py / l'interface."""
    if not campaign:
        return None
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8", newline="\n") as f:
            json.dump(campaign, f, ensure_ascii=False, indent=2)
        return CACHE_FILE
    except Exception:
        return None


def read_content_cache():
    """Lit le cache de contenu s'il existe, sinon None."""
    if not os.path.isfile(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


if __name__ == "__main__":
    seqs = [
        {"id": 1, "duration": 8.60, "title": "Hook", "voice_text": ""},
        {"id": 2, "duration": 9.20, "title": "Probleme", "voice_text": ""},
        {"id": 3, "duration": 9.50, "title": "Demo", "voice_text": ""},
        {"id": 4, "duration": 8.50, "title": "Transfo", "voice_text": ""},
        {"id": 5, "duration": 8.50, "title": "CTA", "voice_text": ""},
    ]
    print("provider =", CONFIG["provider"])
    res = generate_campaign(seqs)
    print("result =", json.dumps(res, ensure_ascii=False)[:400] if res else None)