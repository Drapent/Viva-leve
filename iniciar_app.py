import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess
import re
import shutil

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, backend_dir)

import uvicorn

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_free(port):
    for host in ('127.0.0.1', '0.0.0.0'):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except OSError:
                return False
    return True

def encontrar_porta_livre(porta_inicial=8088):
    for p in range(porta_inicial, porta_inicial + 30):
        if is_port_free(p):
            return p
    return porta_inicial

def iniciar_tunnel_publico(porta=8088):
    """Mantém o Cloudflare Quick Tunnel ativo continuamente com reconexão automática e alta resiliência para 4G/5G."""
    cloudflared_path = os.path.join(BASE_DIR, "cloudflared.exe")
    
    # Se não estiver na pasta atual, tentar copiar da loja de apps
    if not os.path.exists(cloudflared_path):
        origem = os.path.abspath(os.path.join(BASE_DIR, "..", "loja-de-apps", "cloudflared.exe"))
        if os.path.exists(origem):
            try:
                shutil.copy2(origem, cloudflared_path)
            except Exception:
                pass

    if not os.path.exists(cloudflared_path):
        return None

    logfile = os.path.join(BASE_DIR, "cloudflared.log")
    pub_txt = os.path.join(BASE_DIR, "public_url.txt")

    # Loop de Watchdog: se o túnel cair por oscilação de rede, reinicia imediatamente
    while True:
        try:
            if os.path.exists(logfile):
                try:
                    os.remove(logfile)
                except Exception:
                    pass

            proc = subprocess.Popen(
                [cloudflared_path, "tunnel", "--protocol", "http2", "--url", f"http://127.0.0.1:{porta}", "--logfile", logfile],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            pub_url = None
            for _ in range(25):
                time.sleep(1)
                if os.path.exists(logfile):
                    try:
                        with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
                        if match:
                            pub_url = match.group(0)
                            with open(pub_txt, "w", encoding="utf-8") as pf:
                                pf.write(pub_url)
                            os.environ["VIVALEVE_PUBLIC_URL"] = pub_url
                            print("\n" + "=" * 68)
                            print("  🌍 [LINK PÚBLICO HTTPS PARA QUALQUER LUGAR (4G / 5G / SEM IP LOCAL)]:")
                            print(f"  👉 {pub_url}")
                            print("  (Acesse no celular, iPhone ou tablet de qualquer lugar do mundo!)")
                            print("=" * 68 + "\n")
                            break
                    except Exception:
                        pass

            # Monitora enquanto o processo estiver vivo
            while proc.poll() is None:
                time.sleep(5)

            print("  [REDE MÓVEL]: Reconectando túnel para manter acesso 4G/5G ativo...")
            time.sleep(2)
        except Exception as e:
            time.sleep(5)

def abrir_navegador(porta):
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{porta}")

if __name__ == "__main__":
    # Impedir que o Windows entre em modo de suspensão / desligue a placa de rede enquanto o servidor estiver ativo
    if sys.platform == "win32":
        try:
            import ctypes
            # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001)
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        except Exception:
            pass

    ip_local = obter_ip_local()
    porta = encontrar_porta_livre(8088)

    # Exportar porta para as variáveis de ambiente
    os.environ["VIVALEVE_PORT"] = str(porta)

    print("=" * 68)
    print("           VIVALEVE - NUTRICAO & ESTILO DE VIDA")
    print("=" * 68)
    if porta != 8088:
        print(f"  [AVISO] A porta 8088 estava ocupada por outro programa.")
        print(f"  O VivaLeve selecionou automaticamente a porta {porta}!")
        print("-" * 68)
    print(f"  Computador (este PC):      http://localhost:{porta}")
    print(f"  No Celular (mesmo Wi-Fi):  http://{ip_local}:{porta}")
    print("-" * 68)
    print("  Iniciando conexão pública global (4G/5G sem IP local)...")
    print("  Abrindo automaticamente no seu navegador...")
    print("  Para encerrar o aplicativo, pressione Ctrl+C ou feche esta janela.")
    print("=" * 68 + "\n")

    # Iniciar túnel Cloudflare com Watchdog automático em segundo plano
    threading.Thread(target=iniciar_tunnel_publico, args=(porta,), daemon=True).start()

    # Abrir navegador automaticamente em segundo plano
    threading.Thread(target=abrir_navegador, args=(porta,), daemon=True).start()

    # Iniciar servidor FastAPI com protecao contra encerramentos inesperados
    try:
        uvicorn.run("backend.main:app", host="0.0.0.0", port=porta, reload=False)
    except (KeyboardInterrupt, SystemExit):
        print("\n[INFO] Servidor VivaLeve encerrado pelo usuario.")
    except Exception as e:
        print(f"\n[ERRO SERVIDOR]: {e}")
