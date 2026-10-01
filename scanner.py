import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
MEDIA_PATH = Path(os.getenv("MEDIA_PATH"))
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

def buscar_dados_tmdb(titulo, tipo="movie"):
    """
    Consulta a API do TMDB. 
    tipo: 'movie' para filmes, 'tv' para séries.
    """
    url = f"{TMDB_BASE_URL}/search/{tipo}?api_key={TMDB_API_KEY}&query={titulo}&language=pt-BR"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        if dados.get("results"):
            primeiro_resultado = dados["results"][0]
            return {
                "sinopse": primeiro_resultado.get("overview", "Sinopse não disponível."),
                "capa": f"{IMG_BASE_URL}{primeiro_resultado.get('poster_path')}" if primeiro_resultado.get('poster_path') else None,
                "titulo_oficial": primeiro_resultado.get("title" if tipo == "movie" else "name")
            }
    except Exception as e:
        print(f"Erro ao buscar {titulo} no TMDB: {e}")
    return {"sinopse": "Sem dados", "capa": None, "titulo_oficial": titulo}

def escanear_midias():
    """
    Varre a pasta configurada e cataloga filmes e séries estruturados.
    """
    catalogo = {"filmes": [], "series": {}}
    
    # Escaneia Filmes
    pasta_filmes = MEDIA_PATH / "Filmes"
    if pasta_filmes.exists():
        for pasta in pasta_filmes.iterdir():
            if pasta.is_dir():
                # Busca os arquivos de vídeo dentro da pasta do filme
                videos = [f for f in pasta.iterdir() if f.suffix in ['.mkv', '.mp4', '.avi']]
                if videos:
                    nome_filme = pasta.name # Ex: Aposta de Alto Risco 2026
                    # Removemos o ano (ex: 2026) temporariamente para melhorar a busca na API
                    nome_limpo = re.sub(r'\s\d{4}$', '', nome_filme)
                    dados = buscar_dados_tmdb(nome_limpo, tipo="movie")
                    catalogo["filmes"].append({
                        "id": pasta.name,
                        "caminho": str(videos[0]),
                        **dados
                    })

    # Escaneia Séries
    pasta_series = MEDIA_PATH / "Series"
    if pasta_series.exists():
        for pasta_serie in pasta_series.iterdir():
            if pasta_serie.is_dir():
                nome_serie_completo = pasta_serie.name # Ex: ONE PIECE - A Série 2ª Temporada
                # Limpa strings como "1ª Temporada" para buscar apenas "ONE PIECE" no TMDB
                nome_busca = re.sub(r'\s-\s.*|\s\d+ª\sTemporada', '', nome_serie_completo)
                
                if nome_busca not in catalogo["series"]:
                    catalogo["series"][nome_busca] = {
                        **buscar_dados_tmdb(nome_busca, tipo="tv"),
                        "episodios": []
                    }
                
                # Extrai temporadas e episódios (ex: S02E01.mkv)
                for ep_file in pasta_serie.iterdir():
                    if ep_file.suffix in ['.mkv', '.mp4']:
                        match = re.search(r'S(\d{2})E(\d{2})', ep_file.name)
                        if match:
                            catalogo["series"][nome_busca]["episodios"].append({
                                "temporada": match.group(1),
                                "episodio": match.group(2),
                                "arquivo": str(ep_file.name),
                                "caminho": str(ep_file)
                            })
                            
                # Ordena os episódios numericamente
                catalogo["series"][nome_busca]["episodios"].sort(key=lambda x: (x["temporada"], x["episodio"]))

    return catalogo
    