from flask import Flask, render_template, send_file, request, jsonify
import pychromecast
import socket
from scanner import escanear_midias
import os

app = Flask(__name__)

# Cache simples em memória para não consultar a API e o disco a cada F5
CATALOGO_CACHE = None

def pegar_ip_local():
    """Descobre o IP da sua máquina na rede local para enviar ao Chromecast."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não precisa alcançar a internet, apenas gera uma rota local
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/')
def index():
    global CATALOGO_CACHE
    if not CATALOGO_CACHE:
        CATALOGO_CACHE = escanear_midias()
    return render_template('index.html', catalogo=CATALOGO_CACHE)

@app.route('/stream')
def stream_video():
    """
    Servidor de vídeo. O parâmetro conditional=True é MANDATÓRIO 
    para vídeos grandes (.mkv, .mp4), pois permite que o player 
    (TV ou navegador) faça requisições de 'Range' (avance e recue o tempo).
    """
    caminho = request.args.get('path')
    if not os.path.exists(caminho):
        return "Arquivo não encontrado", 404
    return send_file(caminho, conditional=True)
@app.route('/play')

def play_video():
    """Rota para o web player nativo."""
    caminho = request.args.get('path')
    if not caminho or not os.path.exists(caminho):
        return "Arquivo não encontrado", 404
    # Envia o caminho para a nova página do player HTML
    return render_template('player.html', video_path=caminho)
@app.route('/cast', methods=['POST'])

def enviar_para_chromecast():
    dados = request.json
    caminho_video = dados.get('path')
    
    # Procura Chromecasts na rede Wi-Fi
    chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=None)
    if not chromecasts:
        return jsonify({"status": "erro", "msg": "Nenhum Chromecast encontrado."}), 404
    
    # Pega o primeiro Chromecast encontrado (ajuste se tiver mais de um)
    cast = chromecasts[0]
    cast.wait()
    
    # Constrói a URL que a TV vai acessar
    ip_local = pegar_ip_local()
    url_video = f"http://{ip_local}:5000/stream?path={caminho_video}"
    
    # Envia o comando de play para a TV
    mc = cast.media_controller
    mc.play_media(url_video, 'video/mp4') # Funciona para MKV também na maioria dos casos
    mc.block_until_active()
    
    # Para a busca do pychromecast na rede para liberar recursos
    browser.stop_discovery()
    
    return jsonify({"status": "sucesso", "msg": f"Reproduzindo em {cast.name}"})

if __name__ == '__main__':
    # host='0.0.0.0' permite que a TV e o celular acessem o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)