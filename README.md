# João Pessoa · Lula & PT

Painel independente em Streamlit para **Presidente, primeiro turno de 2026**, restrito a **João Pessoa/PB** (IBGE 2507507, TSE 20516). Identidade temática Lula/PT explícita, sem alegação de vínculo oficial. Mostra Lula (13), Flávio Bolsonaro (22), abstenções e votos nulos como totais descritivos do município inteiro, sem segmentação eleitoral por urna, bairro ou pessoa.

## Executar

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## GitHub privado e Streamlit Community Cloud

O aplicativo está preparado para execução nativa em Python no Streamlit Community Cloud. O arquivo de entrada é `streamlit_app.py`, na raiz, que reutiliza `dist/app.py` e seus dados. A aparência está configurada em `.streamlit/config.toml`; as dependências estão fixadas em `requirements.txt`.

Repositório privado: [GabrielSilva-DTSC/joao-pessoa-painel](https://github.com/GabrielSilva-DTSC/joao-pessoa-painel).

Para enviar atualizações já commitadas, execute na raiz deste projeto:

```bash
git push origin main
```

O remoto `origin` aponta para esse repositório privado. Não altere sua visibilidade ao publicar o app.

Depois, em [Streamlit Community Cloud](https://share.streamlit.io/), selecione **Create app** e use:

| Campo | Valor |
| --- | --- |
| Repositório | `GabrielSilva-DTSC/joao-pessoa-painel` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |
| Python, em Advanced settings | `3.12` |
| Secrets | Nenhum necessário |

O Streamlit precisa de acesso autorizado ao repositório privado. Na conta do Streamlit, confira **Settings → Linked accounts → Source control**. A privacidade do repositório e a visibilidade do aplicativo são configurações diferentes; confira o acesso do app antes de compartilhar o link.

Referências oficiais: [publicação](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) e [conexão com repositórios privados](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account).

O arquivo `.streamlit/secrets.toml` e arquivos `.env` são ignorados pelo Git. Os dados municipais, o GeoJSON e a biblioteca Leaflet acompanham o repositório. O app não depende de serviços de dados locais nem de caminhos temporários.

A logo da UFPB aparece no cabeçalho com suas cores e proporções originais. A origem do arquivo está documentada em `dist/assets/README.md`; a interface identifica o painel como independente, sem vínculo ou apoio institucional declarado.

## Publicação anterior no Sites

`dist/` é um site estático que executa o mesmo aplicativo Python com **Stlite 0.85.1 / Streamlit 1.45.1** no navegador. Não exige servidor Python ou credenciais externas. O primeiro acesso baixa o runtime Python/WebAssembly, exigindo internet e podendo demorar. Os mapas de ruas dependem do OpenStreetMap. Fontes e dados acompanham o aplicativo; nenhum cadastro ou dado pessoal é coletado pelo painel.

O manifesto `.openai/hosting.json` identifica a publicação anterior no Sites. Esses arquivos foram preservados; o Streamlit Community Cloud usa `streamlit_app.py` e não depende do manifesto ou do Stlite.

## Dados

- Eleição para presidente: 04/10/2026, primeiro turno, TSE, eleição 6257, cargo 1.
- Totalização municipal: 05/10/2026 às 12:51:05 (Brasília), 1.714 de 1.714 seções totalizadas.
- Snapshot oficial preservado em `dist/data/tse-presidente-jp-2026.json`; consulta em 07/10/2026.
- População residente: Censo IBGE 2022.
- Contorno municipal simplificado: API de malhas do IBGE, sem período explícito retornado pela API.
- Fontes completas e datas em `dist/data/indicadores.json` e na interface.

O JSON oficial do TSE foi lido diretamente. O código do município no TSE é 20516; o IBGE usa 2507507. Os votos de Lula e Flávio têm como denominador os votos válidos. As abstenções usam o eleitorado apto; brancos e nulos, o comparecimento. Os 15.992 nulos incluem 15.975 nulos na urna e 17 técnicos. As categorias não são somadas como um indicador de preferência política. Não há atualização automática. A coordenada (-7.155, -34.875) veio do link fornecido, não de um local de encontro.

Para regerar `indicadores.json` e `indicadores.csv` a partir do snapshot:

```bash
python scripts/import_tse.py
```

O importador recusa dados de outro cargo, turno, eleição ou município e verifica a reconciliação dos totais. Dados eleitorais de outros pleitos não são apresentados no painel.

## Verificação

```bash
python -m unittest discover -s tests
```

Leaflet 1.9.4 (licença BSD-2-Clause) é distribuído em `dist/vendor/`. Stlite (Apache-2.0), Streamlit (Apache-2.0) e Pyodide (MPL-2.0) são carregados pelo runtime no navegador. Créditos cartográficos ficam visíveis no mapa.
