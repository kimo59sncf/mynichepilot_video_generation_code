#!/usr/bin/env python3
"""
=============================================================================
MyNichePilot — Interface VIP (Dashboard de Contrôle & Studio de Production)
=============================================================================
Serveur local autonome (100% bibliothèque standard Python, aucune dépendance
supplémentaire) qui expose :

  • Le frontend « Nuit Cosmique » (web/index.html + style.css + app.js)
  • Une API REST de pilotage du pipeline vidéo existant
  • Un flux temps réel SSE (Server-Sent Events) des logs de production
  • Le streaming / prévisualisation des vidéos générées (support Range)

Lancement :
    python server.py [--host 127.0.0.1] [--port 8000]

Auteur : MyNichePilot Creative Studio
=============================================================================
"""

import os
import sys
import json
import time
import queue
import shutil
import signal
import threading
import argparse
import subprocess
import collections
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

# -----------------------------------------------------------------------------
# Chemins racine du projet
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WORK_DIR = os.path.join(BASE_DIR, ".work")
GEN_SCRIPT = os.path.join(BASE_DIR, "generate_video_mynichepilot.py")

PY_MAJOR, PY_MINOR = sys.version_info[:2]
PY_VERSION = f"{PY_MAJOR}.{PY_MINOR}.{sys.version_info.micro}"

# -----------------------------------------------------------------------------
# Import des métadonnées éditoriales depuis le générateur (sans exécuter main)
# -----------------------------------------------------------------------------
SEQUENCES = []
WIDTH = HEIGHT = FPS = 0
GEN_IMPORT_ERROR = None
try:
    sys.path.insert(0, BASE_DIR)
    from generate_video_mynichepilot import SEQUENCES_CONFIG, WIDTH, HEIGHT, FPS  # noqa
    SEQUENCES = SEQUENCES_CONFIG
except Exception as exc:  # signalé proprement via /api/health
    GEN_IMPORT_ERROR = str(exc)

PALETTE = {
    "fond_nuit": "#000b15",
    "fond_mid": "#091039",
    "frais_bas": "#000e1e",
    "navy": "#101a40",
    "navy_light": "#162455",
    "border": "#26366e",
    "gold": "#fcd34d",
    "amber": "#eca760",
    "orange": "#f59e0b",
    "emerald": "#34d399",
    "cyan": "#60a5fa",
    "red": "#ef4444",
    "muted": "#b4c8e1",
}

# -----------------------------------------------------------------------------
# Légendes & hashtags des vidéos (module optionnel, sans dépendance externe)
# -----------------------------------------------------------------------------
try:
    import captions as _captions_mod
except Exception:
    _captions_mod = None

# Chargement du .env (clés LLM/SaaS) via content_generator (déclenche _load_dotenv)
try:
    import content_generator as _content_gen  # noqa: F401
except Exception:
    _content_gen = None


def find_ffmpeg():
    """Localise FFmpeg : PATH, WinGet (Gyan), répertoires communs, recherche récursive."""
    found = shutil.which("ffmpeg")
    if found:
        return found

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        links = os.path.join(local, "Microsoft", "WinGet", "Links", "ffmpeg.exe")
        if os.path.isfile(links):
            return links
        pkgs = os.path.join(local, "Microsoft", "WinGet", "Packages")
        if os.path.isdir(pkgs):
            for pkg in sorted(os.listdir(pkgs), reverse=True):
                if "ffmpeg" not in pkg.lower():
                    continue
                base = os.path.join(pkgs, pkg)
                for sub in ("ffmpeg", "ffmpeg-full_build", ""):
                    cand = os.path.join(base, sub, "bin", "ffmpeg.exe")
                    if os.path.isfile(cand):
                        return cand
                # recherche récursive bornée (gère les noms versionnés type ffmpeg-9.0.2-full_build)
                for dirpath, dirnames, filenames in os.walk(base):
                    dirnames[:] = [d for d in dirnames if d not in (".", "..")]
                    if "ffmpeg.exe" in filenames and os.path.basename(dirpath) == "bin":
                        return os.path.join(dirpath, "ffmpeg.exe")
    for root in (r"C:\ffmpeg", r"C:\Program Files\ffmpeg"):
        cand = os.path.join(root, "bin", "ffmpeg.exe")
        if os.path.isfile(cand):
            return cand
        cand = os.path.join(root, "ffmpeg.exe")
        if os.path.isfile(cand):
            return cand
    return None


def probe_dependencies():
    """État des dépendances Python + FFmpeg (pour /api/health)."""
    deps = {}
    for name, mod in (("pillow", "PIL"), ("numpy", "numpy"), ("scipy", "scipy"), ("edge_tts", "edge_tts")):
        try:
            m = __import__(mod)
            deps[name] = {"ok": True, "version": getattr(m, "__version__", "ok")}
        except Exception as exc:
            deps[name] = {"ok": False, "error": str(exc)}

    ff = find_ffmpeg()
    ffmpeg = {"ok": bool(ff), "path": ff}
    if ff:
        try:
            out = subprocess.run([ff, "-version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 text=True, errors="replace",
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ffmpeg["version"] = out.stdout.splitlines()[0] if out.stdout else "n/a"
        except Exception:
            ffmpeg["version"] = "n/a"

    return {
        "python": PY_VERSION,
        "python_executable": sys.executable,
        "deps": deps,
        "ffmpeg": ffmpeg,
        "generator_importable": GEN_IMPORT_ERROR is None,
        "generator_error": GEN_IMPORT_ERROR,
        "output_dir": OUTPUT_DIR,
        "work_dir": WORK_DIR,
        "content_provider": os.environ.get("CONTENT_PROVIDER", "static").lower(),
        "content_llm_configured": bool(os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_BASE_URL")),
        "content_saas_url": os.environ.get("SAAS_API_URL", ""),
    }

class PipelineManager:
    """Orchestre le sous-processus de production et diffuse les logs en temps réel."""

    def __init__(self):
        self._lock = threading.RLock()
        self.running = False
        self.proc = None
        self.started_at = None
        self.finished_at = None
        self.exit_code = None
        self.last_task = None
        self._status = "idle"
        self._history = collections.deque(maxlen=2000)
        self._subs = set()

    def _emit(self, obj):
        line = json.dumps(obj, ensure_ascii=False)
        self._history.append(line)
        for q in list(self._subs):
            try:
                q.put_nowait(line)
            except Exception:
                pass

    def log(self, text):
        self._emit({"e": "log", "t": time.time(), "m": text})

    def set_state(self, status, **kw):
        with self._lock:
            self._status = status
        self._emit({"e": "state", "t": time.time(), "s": status, **kw})

    def subscribe(self, q):
        with self._lock:
            self._subs.add(q)

    def unsubscribe(self, q):
        with self._lock:
            self._subs.discard(q)

    def replay(self):
        with self._lock:
            return list(self._history)

    def snapshot(self):
        with self._lock:
            return {
                "running": self.running,
                "status": self._status,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "exit_code": self.exit_code,
                "elapsed": (time.time() - self.started_at) if self.started_at else None,
                "task": dict(self.last_task) if self.last_task else None,
            }

    def start(self, task):
        with self._lock:
            if self.running:
                return False
            self.running = True
            self.started_at = time.time()
            self.finished_at = None
            self.exit_code = None
            self.last_task = dict(task)
            self._status = "running"
        self.log("▶ Pipeline vidéo MyNichePilot démarré.")
        threading.Thread(target=self._work, args=(task,), daemon=True).start()
        return True

    def stop(self):
        p = None
        with self._lock:
            p = self.proc
        if p is not None and p.poll() is None:
            try:
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
            except Exception:
                pass
        with self._lock:
            self.running = False
            self.proc = None
        self.set_state("stopped")
        self.log("■ Pipeline interrompu par l'utilisateur.")

    def _work(self, task):
        cmd = build_command(task)
        env = os.environ.copy()
        # Sortie UTF-8 côté sous-processus (emojis) — robustesse sous Windows
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        ff = find_ffmpeg()
        if ff:
            env["PATH"] = os.path.dirname(ff) + os.pathsep + env.get("PATH", "")
            self.log(f"ℹ FFmpeg détecté : {ff}")
        else:
            self.log("⚠ FFmpeg introuvable : l'encodage vidéo échouera.")

        shown = [os.path.basename(sys.executable), os.path.basename(GEN_SCRIPT)] + cmd[2:]
        self.log("$ " + subprocess.list2cmdline(shown))
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                                 errors="replace", bufsize=1, env=env, cwd=BASE_DIR,
                                 creationflags=flags)
        except Exception as exc:
            self.log(f"✖ Impossible de lancer le processus : {exc}")
            self._finish(1)
            return

        with self._lock:
            self.proc = p

        try:
            for raw in p.stdout:
                line = raw.rstrip("\r\n")
                if line:
                    self.log(line)
        except Exception:
            pass

        code = p.wait()
        self._finish(code)

    def _finish(self, code):
        with self._lock:
            self.running = False
            self.proc = None
            self.finished_at = time.time()
            self.exit_code = code
        elapsed = time.time() - self.started_at if self.started_at else 0
        self.set_state("finished", exit_code=code)
        if code == 0:
            self.log(f"✔ Production terminée avec succès en {elapsed:.1f}s.")
        else:
            self.log(f"✖ Pipeline terminé avec le code {code}.")


def build_command(task):
    """Construit la ligne de commande du générateur à partir des options du dashboard."""
    cmd = [
        sys.executable, GEN_SCRIPT,
        "--output-dir", task.get("output_dir") or OUTPUT_DIR,
        "--work-dir", task.get("work_dir") or WORK_DIR,
    ]
    seq = task.get("sequence")
    if seq in (1, 2, 3, 4, 5):
        cmd += ["--sequence", str(seq)]
    if task.get("skip_audio"):
        cmd += ["--skip-audio"]
    if task.get("variation") in ("static", "llm", "saas"):
        cmd += ["--variation", task["variation"]]
    return cmd

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".ttf": "font/ttf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".mp4": "video/mp4",
    ".txt": "text/plain; charset=utf-8",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
}


def sanitize_path_component(name):
    """Refuse les traversées de répertoire ('..', '/', '\\')."""
    if not name:
        return None
    name = unquote(name)
    if "\x00" in name or ".." in name or "/" in name or "\\" in name:
        return None
    return name


def inff_sequence_id(filename):
    """Infère le numéro de séquence depuis un nom type sequence_3_xxx.mp4."""
    import re
    m = re.search(r"sequence_(\d)", filename)
    if m:
        return int(m.group(1))
    return None


def list_videos():
    items = []
    if not os.path.isdir(OUTPUT_DIR):
        return items
    for fn in sorted(os.listdir(OUTPUT_DIR), reverse=True):
        if fn.lower().endswith(".mp4") and os.path.isfile(os.path.join(OUTPUT_DIR, fn)):
            st = os.stat(os.path.join(OUTPUT_DIR, fn))
            cap = _captions_mod.get_caption_info(fn) if _captions_mod else None
            items.append({
                "name": fn,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "is_master": fn.startswith("MyNichePilot_Publicite"),
                "sequence_id": inff_sequence_id(fn),
                "caption_title": cap["title"] if cap else None,
                "caption": cap["caption"] if cap else None,
                "hashtags": cap["hashtags"] if cap else [],
                "hashtags_str": cap["hashtags_str"] if cap else "",
            })
    return items


def human_size(num):
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "—"
    for unit in ("o", "Ko", "Mo", "Go"):
        if num < 1024 or unit == "Go":
            return f"{int(num)} o" if unit == "o" else f"{num:.1f} {unit}"
        num /= 1024
    return "—"

class RequestHandler(BaseHTTPRequestHandler):
    server_version = "MyNichePilotVIP/1.0"
    protocol_version = "HTTP/1.1"

    def _cors(self, allow_methods=None):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if allow_methods:
            self.send_header("Access-Control-Allow-Methods", allow_methods)

    def _json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 1_000_000:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _serve_asset_file(self, abs_path):
        if not os.path.isfile(abs_path):
            self._json({"error": "Introuvable"}, 404)
            return
        ext = os.path.splitext(abs_path)[1].lower()
        ctype = MIME_TYPES.get(ext, "application/octet-stream")
        size = os.path.getsize(abs_path)

        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                start, end = self._parse_range(range_header, size)
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            with open(abs_path, "rb") as fh:
                fh.seek(start)
                remaining = length
                while remaining > 0:
                    buf = fh.read(min(65536, remaining))
                    if not buf:
                        break
                    self.wfile.write(buf)
                    remaining -= len(buf)
            return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        if ext in (".html", ".css", ".js", ".svg"):
            self.send_header("Cache-Control", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        with open(abs_path, "rb") as fh:
            shutil.copyfileobj(fh, self.wfile, 65536)

    @staticmethod
    def _parse_range(header, size):
        spec = header[len("bytes="):]
        if "," in spec:
            raise ValueError("multi-range non géré")
        a, _, b = spec.partition("-")
        if not a:
            suffix = int(b)
            if suffix == 0:
                raise ValueError("suffixe nul")
            start = max(size - suffix, 0)
            end = size - 1
        else:
            start = int(a)
            end = int(b) if b else size - 1
        if start < 0 or start >= size or end < start:
            raise ValueError("hors bornes")
        return start, min(end, size - 1)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors("GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass  # silencieux — les logs transitent via SSE

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_asset_file(os.path.join(WEB_DIR, "index.html"))
            return

        if path.startswith(("/style.css", "/app.js", "/favicon.svg", "/logo.svg")):
            name = os.path.basename(path)
            self._serve_asset_file(os.path.join(WEB_DIR, name))
            return

        if path.startswith("/assets/"):
            name = sanitize_path_component(path[len("/assets/"):])
            if name:
                self._serve_asset_file(os.path.join(ASSETS_DIR, name))
                return
        if path.startswith("/fonts/"):
            name = sanitize_path_component(path[len("/fonts/"):])
            if name:
                self._serve_asset_file(os.path.join(FONTS_DIR, name))
                return

        if path.startswith("/api/"):
            self._route_api_get(path[len("/api/"):])
            return

        self._json({"error": "Route inconnue"}, 404)

    def _route_api_get(self, route):
        if route == "health":
            info = probe_dependencies()
            info["videos_count"] = len(list_videos())
            self._json(info)
            return
        if route == "config":
            seqs = [{
                "id": s["id"], "name": s["name"], "title": s["title"],
                "duration": s["duration"], "voice_text": s["voice_text"],
                "sfx": [x[0] for x in s.get("sfx", [])],
            } for s in SEQUENCES]
            self._json({
                "width": WIDTH, "height": HEIGHT, "fps": FPS,
                "palette": PALETTE, "sequences": seqs,
                "total_duration": round(sum(s["duration"] for s in SEQUENCES), 2),
                "content_provider": os.environ.get("CONTENT_PROVIDER", "static").lower(),
            })
            return
        if route == "status":
            self._json(manager.snapshot())
            return
        if route == "videos":
            self._json({"videos": list_videos()})
            return
        if route == "events":
            self._serve_events()
            return
        if route.startswith("video/"):
            name = sanitize_path_component(route[len("video/"):])
            if name and name.lower().endswith(".mp4"):
                self._serve_asset_file(os.path.join(OUTPUT_DIR, name))
            else:
                self._json({"error": "nom de vidéo invalide"}, 400)
            return
        self._json({"error": "Endpoint API inconnu"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/run":
            body = self._read_json_body()
            seq = body.get("sequence")
            task = {
                "sequence": seq,
                "skip_audio": bool(body.get("skip_audio", False)),
                "output_dir": (body.get("output_dir") or "").strip() or OUTPUT_DIR,
                "work_dir": WORK_DIR,
                "variation": body.get("variation") or os.environ.get("CONTENT_PROVIDER", "static"),
            }
            if seq not in (None, 1, 2, 3, 4, 5):
                self._json({"ok": False, "error": "séquence invalide (1-5)", "status": manager.snapshot()["status"]}, 400)
                return
            if GEN_IMPORT_ERROR:
                self._json({"ok": False, "error": f"Dépendances manquantes : {GEN_IMPORT_ERROR}", "status": "error"}, 500)
                return
            if not manager.start(task):
                self._json({"ok": False, "error": "Un pipeline est déjà en cours", "status": "running"}, 409)
                return
            self._json({"ok": True, "task": task, "status": "running"})
            return

        if path == "/api/stop":
            manager.stop()
            self._json({"ok": True, "status": manager.snapshot()["status"]})
            return

        self._json({"error": "Endpoint POST inconnu"}, 404)

    def _serve_events(self):
        q = queue.Queue()
        manager.subscribe(q)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self._cors()
            self.end_headers()
            for line in manager.replay():
                self.wfile.write(("data: " + line + "\n\n").encode("utf-8"))
                self.wfile.flush()
            while True:
                try:
                    item = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                if item is None:
                    break
                self.wfile.write(("data: " + item + "\n\n").encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            manager.unsubscribe(q)


manager = PipelineManager()

def run_server(host, port):
    os.makedirs(WEB_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    httpd = ThreadingHTTPServer((host, port), RequestHandler)

    def _shutdown(signum=None, frame=None):
        manager.stop()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    try:
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
    except (ValueError, OSError):
        pass

    return httpd


def main():
    parser = argparse.ArgumentParser(description="MyNichePilot — Interface VIP locale")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute (défaut 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port d'écoute (défaut 8080)")
    args = parser.parse_args()

    ff = find_ffmpeg()
    print("=" * 70)
    print("  MyNichePilot — Interface VIP (Studio de Production)")
    print("=" * 70)
    print(f"  • URL de l'interface : http://{args.host}:{args.port}")
    print(f"  • Python : {PY_VERSION} ({sys.executable})")
    ffmpeg_status = ("détecté -> " + ff) if ff else "NON détecté (requis pour l'encodage)"
    print(f"  • FFmpeg : {ffmpeg_status}")
    print("=" * 70)
    print("Arrêt avec Ctrl+C.\n")

    httpd = run_server(args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
        httpd.server_close()
        print("\nServeur arrêté proprement.")


if __name__ == "__main__":
    main()
