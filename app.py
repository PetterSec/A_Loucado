import mimetypes
import os
import socket
from pathlib import Path

import pychromecast
from flask import Flask, jsonify, render_template, request, send_file, url_for

from scanner import MEDIA_PATH, VIDEO_EXTENSIONS, escanear_midias

app = Flask(__name__)

# Cache simples em memória para não consultar a API e o disco a cada F5
CATALOGO_CACHE = None


def resolver_midia(media_id):
    """Resolve somente arquivos de vídeo dentro da pasta configurada."""
    if not media_id:
        return None

    try:
        raiz = MEDIA_PATH.resolve()
        caminho = (raiz / media_id).resolve()
        caminho.relative_to(raiz)
    except (OSError, ValueError):
        return None

    if not caminho.is_file() or caminho.suffix.lower() not in VIDEO_EXTENSIONS:
        return None
    return caminho

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
    if CATALOGO_CACHE is None:
        CATALOGO_CACHE = escanear_midias()
    return render_template('index.html', catalogo=CATALOGO_CACHE)


@app.post('/catalogo/atualizar')
def atualizar_catalogo():
    global CATALOGO_CACHE
    CATALOGO_CACHE = escanear_midias()
    return jsonify({"status": "sucesso", "msg": "Catálogo atualizado."})

@app.route('/stream')
def stream_video():
    """
    Servidor de vídeo. O parâmetro conditional=True é MANDATÓRIO 
    para vídeos grandes (.mkv, .mp4), pois permite que o player 
    (TV ou navegador) faça requisições de 'Range' (avance e recue o tempo).
    """
    caminho = resolver_midia(request.args.get('media_id'))
    if caminho is None:
        return "Arquivo não encontrado", 404
    tipo_mime = mimetypes.guess_type(caminho.name)[0] or 'application/octet-stream'
    return send_file(caminho, mimetype=tipo_mime, conditional=True, etag=True, max_age=0)


@app.route('/play')
def play_video():
    """Rota para o web player nativo."""
    media_id = request.args.get('media_id')
    if resolver_midia(media_id) is None:
        return "Arquivo não encontrado", 404
    # Envia o caminho para a nova página do player HTML
    return render_template('player.html', media_id=media_id)


@app.post('/cast')
def enviar_para_chromecast():
    dados = request.get_json(silent=True) or {}
    media_id = dados.get('media_id')
    caminho_video = resolver_midia(media_id)
    if caminho_video is None:
        return jsonify({"status": "erro", "msg": "Mídia inválida."}), 400

    browser = None
    try:
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=None)
        if not chromecasts:
            return jsonify({"status": "erro", "msg": "Nenhum Chromecast encontrado."}), 404

        cast = chromecasts[0]
        cast.wait()
        ip_local = pegar_ip_local()
        stream_path = url_for('stream_video', media_id=media_id)
        url_video = f"http://{ip_local}:5000{stream_path}"
        tipo_mime = mimetypes.guess_type(caminho_video.name)[0] or 'video/mp4'
        cast.media_controller.play_media(url_video, tipo_mime)
        cast.media_controller.block_until_active()
        return jsonify({"status": "sucesso", "msg": f"Reproduzindo em {cast.name}"})
    except Exception as erro:
        app.logger.exception("Erro ao transmitir para o Chromecast")
        return jsonify({"status": "erro", "msg": f"Não foi possível iniciar a reprodução: {erro}"}), 502
    finally:
        if browser is not None:
            browser.stop_discovery()

if __name__ == '__main__':
    # host='0.0.0.0' permite que a TV e o celular acessem o servidor
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', '').lower() == 'true')