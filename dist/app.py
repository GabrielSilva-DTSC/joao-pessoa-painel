"""Presidente, 1º turno de 2026: totais municipais de João Pessoa/PB."""
import json
import sys
from html import escape
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="João Pessoa · Presidente 2026 · Lula & PT", page_icon="★", layout="wide", initial_sidebar_state="auto")
st.markdown(f"<style>{(ROOT / 'theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data
def load_data():
    data = json.loads((ROOT / 'data/indicadores.json').read_text(encoding='utf-8'))
    assert data['municipio']['codigo_ibge'] == '2507507' and data['municipio']['uf'] == 'PB'
    assert len(data['eleicoes']) == 1
    row = data['eleicoes'][0]
    assert (row['ano'], row['turno'], row['cargo'], row['municipio_tse']) == (2026, 1, 'Presidente', '20516')
    assert row['comparecimento'] + row['abstencoes'] == row['eleitorado']
    assert row['validos'] + row['brancos'] + row['nulos'] == row['comparecimento']
    assert sum(c['votos'] for c in row['candidatos']) == row['validos']
    return data


def number(value):
    return f"{value:,}".replace(',', '.')


def percent(value, base):
    return f"{100 * value / base:.2f}".replace('.', ',') + '%'


def metric(label, value, sub, accent=False):
    st.markdown(f'<div class="card {"card-accent" if accent else ""}"><div class="card-label">{escape(label)}</div><div class="card-value">{escape(value)}</div><div class="card-sub">{escape(sub)}</div></div>', unsafe_allow_html=True)


def bar(label, value, base, base_label, color):
    width = 100 * value / base
    st.markdown(f'<div class="bar-row"><div class="bar-label"><span>{escape(label)}</span><strong>{percent(value, base)}</strong></div><div class="bar-track"><div class="bar-fill" style="width:{width:.4f}%;background:{color}"></div></div><div class="small-note">{number(value)} · base: {escape(base_label)}</div></div>', unsafe_allow_html=True)


data = load_data()
selected = data['eleicoes'][0]
candidates = {c['numero']: c for c in selected['candidatos']}
lula, flavio = candidates['13']['votos'], candidates['22']['votos']
other = selected['validos'] - lula - flavio

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-top"><span class="brand-star">★</span> LULA &amp; PT</div><div class="brand-place">JOÃO PESSOA / PB</div></div>', unsafe_allow_html=True)
    st.markdown('### Recorte do painel')
    st.markdown('<div class="scope"><strong>Presidente · 1º turno de 2026</strong><span>04 de outubro de 2026</span><br><strong>João Pessoa, Paraíba</strong><span>Município fixo · IBGE 2507507</span></div>', unsafe_allow_html=True)
    st.caption(f"TSE: {selected['atualizacao_tse']} (Brasília).")
    st.caption(f"{number(selected['secoes_totalizadas'])} de {number(selected['secoes_total'])} seções totalizadas.")
    st.divider()
    st.markdown('### Camadas do mapa')
    show_boundary = st.checkbox('Limite municipal', value=True)
    show_reference = st.checkbox('Referência do link enviado', value=True)
    st.divider()
    if sys.platform == 'emscripten':
        st.markdown('<a class="csv-download" href="./data/indicadores.csv" download="joao-pessoa-presidente-2026-t1.csv">Baixar indicadores (CSV)</a>', unsafe_allow_html=True)
    else:
        st.download_button('Baixar indicadores (CSV)', (ROOT / 'data/indicadores.csv').read_bytes(), 'joao-pessoa-presidente-2026-t1.csv', 'text/csv', use_container_width=True)
    st.caption('Totais municipais de presidente, primeiro turno de 2026, com fonte e data da apuração.')
    st.markdown('<div class="small-note">Identidade temática Lula/PT.<br>Iniciativa independente, sem vínculo oficial declarado.</div>', unsafe_allow_html=True)

st.markdown('<div id="jp-ready" class="eyebrow">★ Lula &amp; PT · Paraíba · Dados públicos</div>', unsafe_allow_html=True)
st.title('João Pessoa · Presidente 2026')
st.markdown('<div class="subtitle">Primeiro turno · Votação e participação no município.</div>', unsafe_allow_html=True)
st.markdown('<span class="tag">04/10/2026 · 1º turno</span><span class="tag">Presidente</span><span class="tag">Totais de João Pessoa</span>', unsafe_allow_html=True)
cols = st.columns(4)
with cols[0]: metric('Lula · 13', number(lula), f"{percent(lula, selected['validos'])} dos votos válidos", True)
with cols[1]: metric('Flávio Bolsonaro · 22', number(flavio), f"{percent(flavio, selected['validos'])} dos votos válidos")
with cols[2]: metric('Abstenções', number(selected['abstencoes']), f"{percent(selected['abstencoes'], selected['eleitorado'])} do eleitorado apto")
with cols[3]: metric('Votos nulos', number(selected['nulos']), f"{percent(selected['nulos'], selected['comparecimento'])} do comparecimento")
st.caption(f"Eleitorado apto: {number(selected['eleitorado'])} · Comparecimento: {number(selected['comparecimento'])} · Seções totalizadas: {number(selected['secoes_totalizadas'])}/{number(selected['secoes_total'])} · TSE: {selected['atualizacao_tse']}")

map_tab, participation_tab, source_tab = st.tabs(['Mapa e totais', 'Participação', 'Fontes e serviços'])
with map_tab:
    main, info = st.columns([2.6, 1], gap='large')
    with main:
        st.subheader('João Pessoa no mapa')
        popup = ('<strong>João Pessoa · Presidente · 1º turno de 2026</strong><br>'
            f'Lula (13): {number(lula)} · {percent(lula, selected["validos"])} dos válidos<br>'
            f'Flávio Bolsonaro (22): {number(flavio)} · {percent(flavio, selected["validos"])} dos válidos<br>'
            f'Abstenções: {number(selected["abstencoes"])} · {percent(selected["abstencoes"], selected["eleitorado"])} dos aptos<br>'
            f'Nulos: {number(selected["nulos"])} · {percent(selected["nulos"], selected["comparecimento"])} do comparecimento<br>'
            '<small>Totais do município inteiro · Fonte: TSE</small>')
        replacements = {
            '__LEAFLET_CSS__': (ROOT / 'vendor/leaflet.css').read_text(encoding='utf-8'),
            '__LEAFLET_JS__': (ROOT / 'vendor/leaflet.js').read_text(encoding='utf-8'),
            '__GEOJSON__': (ROOT / 'data/municipio.geojson').read_text(encoding='utf-8'),
            '__SHOW_BOUNDARY__': json.dumps(show_boundary), '__SHOW_REFERENCE__': json.dumps(show_reference),
            '__MUNICIPAL_POPUP__': json.dumps(popup),
        }
        template = (ROOT / 'map.html').read_text(encoding='utf-8')
        for key, value in replacements.items(): template = template.replace(key, value)
        components.html(template, height=505, scrolling=False)
        st.markdown('<div class="key"><span class="key-line"></span>Limite municipal <span class="key-dot"></span>Referência do link enviado</div>', unsafe_allow_html=True)
        st.caption('Clique no contorno para consultar os totais municipais. Ruas: OpenStreetMap. Limite simplificado: IBGE. O ponto azul é apenas a coordenada do link enviado.')
    with info:
        st.subheader('Apuração municipal')
        st.markdown(f'<div class="city-card"><h3>Presidente · 2026</h3><p>Primeiro turno · João Pessoa</p><div class="big">{percent(selected["secoes_totalizadas"], selected["secoes_total"])}</div><p>das seções totalizadas</p><p>{selected["atualizacao_tse"]} · TSE</p></div>', unsafe_allow_html=True)
        st.markdown(f"**Votos válidos:** {number(selected['validos'])}")
        st.markdown(f"**Outros candidatos:** {number(other)} · {percent(other, selected['validos'])} dos válidos")
        st.markdown(f"**Votos em branco:** {number(selected['brancos'])} · {percent(selected['brancos'], selected['comparecimento'])} do comparecimento")
        st.caption(f"Nulos: {number(selected['nulos_urna'])} na urna + {number(selected['nulos_tecnicos'])} técnicos, conforme a classificação do TSE.")
        st.link_button('Consultar a fonte do TSE', selected['fonte'], use_container_width=True)
    st.markdown('<div class="method"><strong>Bases de cálculo</strong><br>Lula e Flávio: percentual dos votos válidos. Abstenções: percentual do eleitorado apto. Brancos e nulos: percentual do comparecimento. Esses grupos não devem ser somados como medida de preferência ou intenção de voto.</div>', unsafe_allow_html=True)

with participation_tab:
    st.subheader('Votação e participação · 1º turno de 2026')
    st.caption('Presidente · João Pessoa, Paraíba · Todos os valores descrevem o município inteiro.')
    left, right = st.columns(2, gap='large')
    with left:
        st.markdown('### Distribuição dos votos válidos')
        for label, value, color in [('Lula · 13', lula, '#cb102a'), ('Flávio Bolsonaro · 22', flavio, '#354d68'), ('Outros candidatos', other, '#738294')]:
            bar(label, value, selected['validos'], 'votos válidos', color)
    with right:
        st.markdown('### Comparecimento e registros')
        for label, key, base, color in [('Comparecimento', 'comparecimento', 'eleitorado', '#354d68'), ('Abstenções', 'abstencoes', 'eleitorado', '#766485'), ('Votos nulos', 'nulos', 'comparecimento', '#738294'), ('Votos em branco', 'brancos', 'comparecimento', '#738294')]:
            bar(label, selected[key], selected[base], 'eleitorado apto' if base == 'eleitorado' else 'comparecimento', color)
    st.divider()
    st.markdown('**Totais para conferência**')
    st.table([{'Indicador': label, 'Total': number(selected[key])} for label, key in [('Eleitorado apto', 'eleitorado'), ('Comparecimento', 'comparecimento'), ('Abstenções', 'abstencoes'), ('Votos válidos', 'validos'), ('Votos em branco', 'brancos'), ('Votos nulos — total', 'nulos'), ('Nulos na urna', 'nulos_urna'), ('Nulos técnicos', 'nulos_tecnicos')]])

with source_tab:
    st.subheader('Fontes e metodologia')
    st.markdown('Os indicadores vêm do arquivo municipal oficial de **resultados do TSE**, para **Presidente, primeiro turno de 2026, em João Pessoa**. O mapa combina o contorno municipal do IBGE com as ruas do OpenStreetMap.')
    for source in data['fontes']:
        st.markdown(f"**[{source['titulo']}]({source['url']})**  \n{source['descricao']}")
    st.markdown('### Critérios de leitura')
    st.markdown('- Município: João Pessoa (PB), código TSE 20516 e IBGE 2507507.\n- Eleição TSE 6257, cargo 1 (Presidente), turno 1, em 04/10/2026.\n- Lula (13) e Flávio Bolsonaro (22): votos nominais; percentual sobre votos válidos.\n- Abstenções ÷ eleitorado apto; brancos e nulos ÷ comparecimento.\n- Nulos incluem os nulos na urna e os nulos técnicos informados pelo TSE.\n- Percentuais calculados a partir dos totais, com duas casas decimais.\n- Dados agregados não identificam pessoas nem os motivos da ausência ou do voto nulo.\n- Contorno municipal simplificado, sem detalhamento eleitoral por urna ou bairro.')
    st.info(f"Cópia consultada em 07/10/2026. Totalização do TSE: {selected['atualizacao_tse']} (Brasília). Não há atualização automática ao abrir o painel.")
    st.markdown('### Serviços para consulta')
    st.link_button('Linhas e horários de ônibus · Semob-JP', 'https://servicos.semobjp.pb.gov.br/linhas-de-onibus/')
    st.link_button('Local de votação · TSE', 'https://www.tse.jus.br/servicos-eleitorais/local-de-votacao-zonas-eleitorais')
    st.link_button('Autoatendimento eleitoral · TSE', 'https://www.tse.jus.br/servicos-eleitorais/autoatendimento-eleitoral/')
    st.markdown('### Site de referência')
    st.markdown('[Onde dá pra conversar](https://www.ondedapraconversar.com.br/#/perto/@-7.155,-34.875) é a referência visual e geográfica. Os valores deste painel foram obtidos diretamente no TSE, no recorte municipal, sem reproduzir recomendações de locais de abordagem.')

st.markdown('<div class="footer"><strong>★ Lula &amp; PT · João Pessoa</strong><br>Iniciativa independente, sem vínculo oficial declarado com Lula, PT, Prefeitura, TSE ou IBGE. Identidade partidária explícita; indicadores públicos apresentados de forma descritiva.<br>Presidente · 1º turno de 2026 · Fontes consultadas em 07/10/2026 · Mapa © OpenStreetMap / IBGE</div>', unsafe_allow_html=True)
