# João Pessoa · Lula & PT

Painel independente em Streamlit, restrito a João Pessoa/PB (IBGE 2507507). Identidade temática Lula/PT explícita, sem alegação de vínculo oficial. Indicadores descritivos do município inteiro, sem segmentação eleitoral por bairro ou pessoa.

## Executar

```bash
python -m pip install -r requirements.txt
streamlit run dist/app.py
```

## Publicação

`dist/` é um site estático que executa o mesmo aplicativo Python com **Stlite 0.85.1 / Streamlit 1.45.1** no navegador. Não exige servidor Python ou credenciais externas. O primeiro acesso baixa o runtime Python/WebAssembly, exigindo internet e podendo demorar. Os mapas de ruas dependem do OpenStreetMap. Fontes e dados acompanham o aplicativo; nenhum cadastro ou dado pessoal é coletado pelo painel.

O manifesto `.openai/hosting.json` identifica a publicação Sites. O site começa privado para o proprietário; compartilhamento é gerenciado no Sites.

## Dados

- Eleição municipal para prefeito: 06/10/2024 e 27/10/2024, TRE-PB.
- População residente: Censo IBGE 2022.
- Contorno municipal simplificado: API de malhas do IBGE, sem período explícito retornado pela API.
- Fontes completas e datas em `dist/data/indicadores.json` e na interface.

As tabelas XLS foram lidas diretamente para conferir os totais de João Pessoa. O código de origem TRE-PB é 20516; o IBGE usa 2507507. As ausências têm como denominador o eleitorado apto; brancos e nulos, o comparecimento. Não são somados como um indicador de preferência política. Não há dados eleitorais de 2026 nem atualização automática. A coordenada (-7.155, -34.875) veio do link fornecido, não de um local de encontro.

## Verificação

```bash
python -m unittest discover -s tests
```

Leaflet 1.9.4 (licença BSD-2-Clause) é distribuído em `dist/vendor/`. Stlite (Apache-2.0), Streamlit (Apache-2.0) e Pyodide (MPL-2.0) são carregados pelo runtime no navegador. Créditos cartográficos ficam visíveis no mapa.
