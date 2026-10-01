# 🍿 A Loucadoura - Servidor de Mídia Local

Um servidor de streaming caseiro (estilo Netflix) leve, construído em Python, com integração ao TMDB para enriquecimento de metadados e suporte nativo ao Google Chromecast via rede local.

## 🚀 Arquitetura e Boas Práticas Adotadas
* **Flask Server:** Utilizado para servir o frontend e atuar como servidor de arquivos estáticos (vídeos) através de requisições parciais (`conditional=True`), permitindo buffer e avanço/recuo de tempo na reprodução.
* **Isolamento de Credenciais:** Uso de arquivo `.env` para garantir que a API Key do TMDB não seja exposta caso o projeto vá para o GitHub.
* **Desempenho (Máquinas Leves):** Implementação de cache em memória no dicionário do Python para o catálogo. A leitura do disco (I/O) e as chamadas de API são feitas apenas no primeiro acesso, aliviando o processamento.
* **Execução Nativa:** Optamos por `venv` ao invés de Docker para facilitar o mDNS (descoberta do Chromecast na rede) e não sobrecarregar a CPU.

## 🛠️ Como Executar

1. Crie seu ambiente virtual: `python3 -m venv venv`
2. Ative-o: `source venv/bin/activate`
3. Instale as dependências: `pip install -r requirements.txt` *(ou pip install flask python-dotenv requests pychromecast)*
4. Renomeie o arquivo de exemplo para `.env` e insira sua chave do TMDB e o caminho da pasta de mídia.
5. Inicie o servidor: `python app.py`
6. Abra o navegador em `http://localhost:5000` (ou acesse o IP da máquina pelo celular).

## 🔮 Próximos Passos (To-Do)
- [ ] Adicionar suporte a legendas externas (.srt).
- [ ] Criar controles de play/pause/volume diretamente na interface web usando `pychromecast`.
- [ ] Implementar banco de dados SQLite para salvar progresso ("Continuar assistindo").