# A Loucadoura

Servidor de mídia local em Flask, com catálogo enriquecido pelo TMDB, reprodução no navegador e envio para Chromecast.

## Requisitos

- Python 3.11 ou mais recente
- `ffmpeg` não é necessário para o teste inicial, mas será necessário quando adicionarmos transcodificação
- A máquina do servidor e o Chromecast na mesma rede local

## Configuração

1. Crie e ative o ambiente virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Crie o arquivo `.env` a partir do exemplo:

   ```bash
   cp .env.example .env
   ```

3. Preencha `MEDIA_PATH` com a pasta raiz da sua biblioteca. Ela deve ter esta estrutura:

   ```text
   A Loucadoura/
   ├── Filmes/
   │   └── Nome do Filme 2024/
   │       └── filme.mp4
   └── Series/
       └── Nome da Série - 1ª Temporada/
           ├── S01E01 - Piloto.mp4
           └── S01E02 - Segundo episódio.mp4
   ```

4. Cole a chave nova do TMDB em `TMDB_API_KEY` e altere `TMDB_ENABLED=true` quando quiser capas e sinopses online. O TMDB fica desligado por padrão para o catálogo não travar quando a internet ou a API estiver indisponível.

## Execução

```bash
source venv/bin/activate
python app.py
```

Abra `http://localhost:5000` no computador ou use o IP da máquina em outro dispositivo da rede.

O botão **Atualizar catálogo** refaz a leitura das pastas e consulta os metadados novamente.

## Segurança

- Nunca versione `.env` ou coloque a chave da API no código.
- As rotas de reprodução aceitam apenas IDs relativos de arquivos de vídeo dentro de `MEDIA_PATH`.
- Para uso fora da rede doméstica, adicione autenticação e HTTPS antes de expor a aplicação.

## Limitações atuais

- Navegadores e Chromecast podem não reproduzir todos os codecs de `.mkv` e `.avi` diretamente.
- O Chromecast atualmente usa o primeiro dispositivo encontrado.
- Ainda não há legendas, progresso salvo ou transcodificação automática.

## Próximas melhorias

1. Transcodificação com FFmpeg quando o formato não for compatível.
2. Banco SQLite para progresso e histórico.
3. Legendas externas `.srt`.
4. Seleção e controles completos do Chromecast.
