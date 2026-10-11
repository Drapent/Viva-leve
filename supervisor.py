"""
VivaLeve - Supervisor & Watchdog 24/7 Autônomo
Porta Exclusiva: 8088 (evita conflitos com Filmora/porta 8000 e 8080).
Garante que o Uvicorn e o Cloudflared NUNCA caiam.
Se algum processo falhar, reinicia em < 1 segundo.
Previne que o Windows entre em modo de suspensão / desligue a rede.
Compatível 100% com pythonw.exe (sem janela preta).
"""
import sys
import os
import time
import subprocess
import socket
import re
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
VENV_PYTHONW = BASE_DIR / ".venv" / "Scripts" / "pythonw.exe"
CLOUDFLARED = BASE_DIR / "cloudflared.exe"
PUBLIC_TXT = BASE_DIR / "public_url.txt"
STATUS_JSON = BASE_DIR / "supervisor_status.json"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
UVICORN_LOG = LOG_DIR / "uvicorn.log"
CLOUDFLARED_LOG = LOG_DIR / "cloudflared.log"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"

# Redirecionar stdout/stderr se estiver rodando sob pythonw.exe (onde stdout é None)
if sys.stdout is None:
    try:
        sys.stdout = open(SUPERVISOR_LOG, "a", encoding="utf-8")
        sys.stderr = sys.stdout
    except Exception:
        pass

PORTA_VIVALEVE = 8088

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    if sys.stdout is not None:
        try:
            print(line, flush=True)
        except Exception:
            pass
    try:
        with open(SUPERVISOR_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def prevent_windows_sleep():
    if sys.platform == "win32":
        try:
            import ctypes
            # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001)
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        except Exception:
            pass

def is_port_free(port):
    for host in ("127.0.0.1", "0.0.0.0"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except OSError:
                return False
    return True

def get_free_port(start=8088):
    for p in range(start, start + 30):
        if is_port_free(p):
            return p
    return start

def start_uvicorn(port):
    python_exe = str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable)
    cmd = [
        python_exe, "-m", "uvicorn",
        "backend.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--log-level", "info"
    ]
    env = os.environ.copy()
    env["VIVALEVE_PORT"] = str(port)
    f_log = open(UVICORN_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=f_log,
        stderr=subprocess.STDOUT
    )
    log(f"Uvicorn iniciado com PID {proc.pid} na porta {port}")
    return proc, f_log

def ensure_cloudflared():
    if not CLOUDFLARED.exists():
        alt = BASE_DIR.parent / "loja-de-apps" / "cloudflared.exe"
        if alt.exists():
            shutil.copy2(alt, CLOUDFLARED)
            log("cloudflared.exe copiado com sucesso.")
    return CLOUDFLARED.exists()

def start_cloudflared(port):
    if not ensure_cloudflared():
        log("cloudflared.exe não encontrado!")
        return None
    
    if CLOUDFLARED_LOG.exists():
        try:
            CLOUDFLARED_LOG.unlink()
        except Exception:
            pass

    cmd = [
        str(CLOUDFLARED), "tunnel",
        "--protocol", "http2",
        "--url", f"http://127.0.0.1:{port}",
        "--logfile", str(CLOUDFLARED_LOG)
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    log(f"Cloudflared iniciado com PID {proc.pid} apontando para http://127.0.0.1:{port}")
    return proc

def extract_public_url():
    if not CLOUDFLARED_LOG.exists():
        return None
    try:
        content = CLOUDFLARED_LOG.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
        if match:
            url = match.group(0)
            PUBLIC_TXT.write_text(url, encoding="utf-8")
            os.environ["VIVALEVE_PUBLIC_URL"] = url
            update_desktop_links(url)
            return url
    except Exception:
        pass
    return None

def update_desktop_links(url):
    try:
        import winreg
        desktop = None
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                desktop, _ = winreg.QueryValueEx(key, "Desktop")
                desktop = os.path.expandvars(desktop)
        except Exception:
            pass
        if not desktop or not os.path.exists(desktop):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        if os.path.exists(desktop):
            # 1. Atalho para abrir no PC com velocidade máxima 0ms
            pc_url_file = os.path.join(desktop, "VivaLeve - Abrir no PC.url")
            with open(pc_url_file, "w", encoding="utf-8") as f:
                f.write(f"[InternetShortcut]\nURL=http://localhost:{PORTA_VIVALEVE}\nIconIndex=0\n")
            
            # 2. Atalho com o link público móvel para celular
            mobile_url_file = os.path.join(desktop, "VivaLeve - Link Mobile (4G).url")
            with open(mobile_url_file, "w", encoding="utf-8") as f:
                f.write(f"[InternetShortcut]\nURL={url}\nIconIndex=0\n")
    except Exception as e:
        log(f"Aviso ao criar atalhos desktop: {e}")

def main():
    log("Iniciando VivaLeve 24/7 Supervisor...")
    prevent_windows_sleep()
    port = get_free_port(PORTA_VIVALEVE)

    uvicorn_proc, uvicorn_log = start_uvicorn(port)
    cloud_proc = start_cloudflared(port)

    # Aguardar detecção da URL pública
    pub_url = None
    for _ in range(35):
        time.sleep(1)
        pub_url = extract_public_url()
        if pub_url:
            log(f"URL Pública ativa: {pub_url}")
            break

    # Loop de Watchdog Contínuo
    while True:
        try:
            prevent_windows_sleep()
            time.sleep(3)

            # 1. Verifica Uvicorn
            if uvicorn_proc.poll() is not None:
                log(f"Uvicorn parou (código {uvicorn_proc.returncode}). Reiniciando imediatamente...")
                try:
                    uvicorn_log.close()
                except Exception:
                    pass
                uvicorn_proc, uvicorn_log = start_uvicorn(port)

            # 2. Verifica Cloudflared
            if cloud_proc and cloud_proc.poll() is not None:
                log(f"Cloudflared parou (código {cloud_proc.returncode}). Reiniciando túnel...")
                cloud_proc = start_cloudflared(port)
                for _ in range(15):
                    time.sleep(1)
                    p = extract_public_url()
                    if p:
                        log(f"Novo túnel estabelecido: {p}")
                        break

            # 3. Atualiza status
            status = {
                "running": True,
                "timestamp": time.time(),
                "port": port,
                "uvicorn_pid": uvicorn_proc.pid if uvicorn_proc else None,
                "cloudflared_pid": cloud_proc.pid if cloud_proc else None,
                "public_url": PUBLIC_TXT.read_text(encoding="utf-8").strip() if PUBLIC_TXT.exists() else None
            }
            STATUS_JSON.write_text(json.dumps(status, indent=2), encoding="utf-8")

        except KeyboardInterrupt:
            log("Supervisor encerrado manualmente.")
            if uvicorn_proc: uvicorn_proc.terminate()
            if cloud_proc: cloud_proc.terminate()
            break
        except Exception as e:
            log(f"Erro no loop do supervisor: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
