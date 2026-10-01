import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_ENABLED = os.getenv("TMDB_ENABLED", "false").lower() == "true"
MEDIA_PATH = Path(os.getenv("MEDIA_PATH")) if os.getenv("MEDIA_PATH") else Path("./media")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"
VIDEO_EXTENSIONS = {".avi", ".mkv", ".mp4", ".webm", ".mov"}


def _id_da_midia(caminho):
    return caminho.relative_to(MEDIA_PATH).as_posix()


def _nome_do_episodio(nome_arquivo):
    nome = Path(nome_arquivo).stem
    nome = re.sub(r"S\d{1,2}E\d{1,2}", "", nome, flags=re.IGNORECASE)
    nome = re.sub(r"[._-]+", " ", nome).strip()
    return nome or "Episódio"


def _buscar_metadados_em_paralelo(tarefas):
    if not tarefas:
        return []

    with ThreadPoolExecutor(max_workers=min(6, len(tarefas))) as executor:
        futuros = [
            executor.submit(buscar_dados_tmdb, titulo, tipo)
            for titulo, tipo in tarefas
        ]
        return [futuro.result() for futuro in futuros]


def buscar_dados_tmdb(titulo, tipo="movie"):
    """
    Consulta a API do TMDB. 
    tipo: 'movie' para filmes, 'tv' para séries.
    """
    if not TMDB_ENABLED or not TMDB_API_KEY:
        return {"sinopse": "API Key não configurada", "capa": None, "titulo_oficial": titulo}

    url = f"{TMDB_BASE_URL}/search/{tipo}"
    try:
        resposta = requests.get(
            url,
            params={"api_key": TMDB_API_KEY, "query": titulo, "language": "pt-BR"},
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("results"):
            primeiro_resultado = dados["results"][0]
            return {
                "sinopse": primeiro_resultado.get("overview", "Sinopse não disponível."),
                "capa": f"{IMG_BASE_URL}{primeiro_resultado.get('poster_path')}" if primeiro_resultado.get('poster_path') else None,
                "titulo_oficial": primeiro_resultado.get("title" if tipo == "movie" else "name") or titulo,
            }
    except (requests.RequestException, ValueError) as e:
        print(f"Erro ao buscar {titulo} no TMDB: {e}")
    return {"sinopse": "Sem dados", "capa": None, "titulo_oficial": titulo}

def escanear_midias():
    """
    Varre a pasta configurada e cataloga filmes e séries estruturados.
    """
    catalogo = {"filmes": [], "series": {}}

    if not MEDIA_PATH.exists():
        return catalogo

    filmes_pendentes = []

    # Escaneia Filmes
    pasta_filmes = MEDIA_PATH / "Filmes"
    if pasta_filmes.exists():
        for pasta in sorted(pasta_filmes.iterdir(), key=lambda item: item.name.lower()):
            if pasta.is_dir():
                # Busca os arquivos de vídeo dentro da pasta do filme
                videos = sorted(
                    (f for f in pasta.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS),
                    key=lambda item: item.name.lower(),
                )
                if videos:
                    nome_filme = pasta.name # Ex: Aposta de Alto Risco 2026
                    # Removemos o ano (ex: 2026) temporariamente para melhorar a busca na API
                    nome_limpo = re.sub(r'\s\d{4}$', '', nome_filme)
                    filmes_pendentes.append((pasta, videos[0], nome_limpo))

    dados_filmes = _buscar_metadados_em_paralelo(
        [(nome_limpo, "movie") for _, _, nome_limpo in filmes_pendentes]
    )
    for (pasta, video, _), dados in zip(filmes_pendentes, dados_filmes):
        catalogo["filmes"].append({
            "id": pasta.name,
            "media_id": _id_da_midia(video),
            **dados
        })

    # Escaneia Séries
    series_pendentes = {}
    pasta_series = MEDIA_PATH / "Series"
    if pasta_series.exists():
        for pasta_serie in sorted(pasta_series.iterdir(), key=lambda item: item.name.lower()):
            if pasta_serie.is_dir():
                nome_serie_completo = pasta_serie.name # Ex: ONE PIECE - A Série 2ª Temporada
                # Limpa strings como "1ª Temporada" para buscar apenas "ONE PIECE" no TMDB
                nome_busca = re.sub(r'\s-\s.*|\s\d+ª\sTemporada', '', nome_serie_completo)

                if nome_busca not in catalogo["series"]:
                    catalogo["series"][nome_busca] = {"episodios": []}
                    series_pendentes[nome_busca] = (nome_busca, "tv")

                # Extrai temporadas e episódios (ex: S02E01.mkv)
                for ep_file in sorted(pasta_serie.iterdir(), key=lambda item: item.name.lower()):
                    if ep_file.is_file() and ep_file.suffix.lower() in VIDEO_EXTENSIONS:
                        match = re.search(r'S(\d{1,2})E(\d{1,2})', ep_file.name, re.IGNORECASE)
                        if match:
                            catalogo["series"][nome_busca]["episodios"].append({
                                "temporada": int(match.group(1)),
                                "episodio": int(match.group(2)),
                                "titulo": _nome_do_episodio(ep_file.name),
                                "media_id": _id_da_midia(ep_file),
                            })

                # Ordena os episódios numericamente
                catalogo["series"][nome_busca]["episodios"].sort(
                    key=lambda episodio: (episodio["temporada"], episodio["episodio"])
                )

    dados_series = _buscar_metadados_em_paralelo(list(series_pendentes.values()))
    for nome_serie, dados in zip(series_pendentes, dados_series):
        catalogo["series"][nome_serie].update(dados)

    catalogo["filmes"].sort(key=lambda filme: filme["titulo_oficial"].lower())

    return catalogo