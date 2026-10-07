"""Painel municipal descritivo. Executa com Streamlit ou Stlite no navegador."""
import csv
import io
import json
import sys
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
st.set_page_config(page_title="João Pessoa · Lula & PT", page_icon="★", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT / 'theme.css').read_text()}</style>", unsafe_allow_html=True)


@st.cache_data
def load_data():
    data = json.loads((ROOT / 'data/indicadores.json').read_text())
    assert data['municipio']['codigo_ibge'] == '2507507'
    assert data['municipio']['uf'] == 'PB'
    for row in data['eleicoes']:
        assert row['comparecimento'] + row['abstencoes'] == row['eleitorado']
        assert 0 <= row['brancos'] + row['nulos'] <= row['comparecimento']
    return data


def number(value):
    return f"{value:,}".replace(',', '.')


def percent(value, base):
    return f"{100 * value / base:.2f}".replace('.', ',') + '%'


def metric(label, value, sub, accent=False):
    st.markdown(f'<div class="card {"card-accent" if accent else ""}"><div class="card-label">{escape(label)}</div><div class="card-value">{escape(value)}</div><div class="card-sub">{escape(sub)}</div></div>', unsafe_allow_html=True)


def csv_data(data):
    out = io.StringIO()
    keys = ['ano', 'turno', 'data', 'cargo', 'eleitorado', 'comparecimento', 'abstencoes', 'brancos', 'nulos', 'fonte']
    writer = csv.DictWriter(out, fieldnames=['municipio', 'uf', 'codigo_ibge'] + keys, delimiter=';')
    writer.writeheader()
    for row in data['eleicoes']:
        writer.writerow({'municipio': 'João Pessoa', 'uf': 'PB', 'codigo_ibge': '2507507', **{k: row[k] for k in keys}})
    return ('\ufeff' + out.getvalue()).encode('utf-8')


data = load_data()
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-top"><span class="brand-star">★</span> LULA &amp; PT</div><div class="brand-place">JOÃO PESSOA / PB</div></div>', unsafe_allow_html=True)
    st.markdown('### Recorte do painel')
    st.markdown('<div class="scope"><strong>João Pessoa, Paraíba</strong><span>Município fixo · IBGE 2507507</span></div>', unsafe_allow_html=True)
    turn = st.radio('Eleições municipais de 2024', [1, 2], index=1, format_func=lambda t: f'{t}º turno · {"06" if t == 1 else "27"}/10/2024')
    st.caption('Cargo: prefeito. Base histórica de 2024; não representa a eleição de 2026.')
    st.divider()
    st.markdown('### Camadas do mapa')
    show_boundary = st.checkbox('Limite municipal', value=True)
    show_reference = st.checkbox('Referência do link enviado', value=True)
    st.divider()
    if sys.platform == 'emscripten':
        st.markdown('<a class="csv-download" href="./data/indicadores.csv" download="joao-pessoa-2024.csv">Baixar indicadores (CSV)</a>', unsafe_allow_html=True)
    else:
        st.download_button('Baixar indicadores (CSV)', csv_data(data), 'joao-pessoa-2024.csv', 'text/csv', use_container_width=True)
    st.caption('Totais municipais dos dois turnos, com os links das fontes.')
    st.markdown('<div class="small-note">Identidade temática Lula/PT.<br>Iniciativa independente, sem vínculo oficial declarado.</div>', unsafe_allow_html=True)

selected = next(x for x in data['eleicoes'] if x['turno'] == turn)
st.markdown('<div id="jp-ready" class="eyebrow">★ Lula &amp; PT · Paraíba · Dados públicos</div>', unsafe_allow_html=True)
st.title('João Pessoa em números')
st.markdown('<div class="subtitle">Território, participação eleitoral e serviços para consultar a cidade.</div>', unsafe_allow_html=True)
st.markdown(f'<span class="tag">Eleições 2024 · {turn}º turno</span><span class="tag">Prefeito</span><span class="tag">Dados municipais agregados</span>', unsafe_allow_html=True)

cols = st.columns(4)
with cols[0]: metric('Eleitorado apto', number(selected['eleitorado']), 'Eleitores em João Pessoa', True)
with cols[1]: metric('Comparecimento', percent(selected['comparecimento'], selected['eleitorado']), f"{number(selected['comparecimento'])} eleitores · base: aptos")
with cols[2]: metric('Abstenções', percent(selected['abstencoes'], selected['eleitorado']), f"{number(selected['abstencoes'])} ausências · base: aptos")
with cols[3]: metric('Votos nulos', percent(selected['nulos'], selected['comparecimento']), f"{number(selected['nulos'])} votos · base: comparecimento")

map_tab, compare_tab, source_tab = st.tabs(['Mapa e panorama', 'Comparar turnos', 'Fontes e serviços'])
with map_tab:
    main, info = st.columns([2.6, 1], gap='large')
    with main:
        st.subheader('Mapa de referência')
        template = (ROOT / 'map.html').read_text()
        replacements = {
            '__LEAFLET_CSS__': (ROOT / 'vendor/leaflet.css').read_text(),
            '__LEAFLET_JS__': (ROOT / 'vendor/leaflet.js').read_text(),
            '__GEOJSON__': (ROOT / 'data/municipio.geojson').read_text(),
            '__SHOW_BOUNDARY__': json.dumps(show_boundary),
            '__SHOW_REFERENCE__': json.dumps(show_reference),
        }
        for key, value in replacements.items(): template = template.replace(key, value)
        components.html(template, height=505, scrolling=False)
        st.markdown('<div class="key"><span class="key-line"></span>Limite municipal <span class="key-dot"></span>Referência do link enviado</div>', unsafe_allow_html=True)
        st.caption('Ruas: OpenStreetMap. Contorno simplificado: IBGE. Amplie o mapa para consultar ruas e nomes de bairros. As camadas não mostram resultados eleitorais por área.')
    with info:
        st.subheader('Retrato da cidade')
        st.markdown('<div class="city-card"><h3>João Pessoa</h3><p>População residente · Censo 2022</p><div class="big">833.932</div><p>pessoas · Fonte: IBGE</p></div>', unsafe_allow_html=True)
        st.markdown('**Informações para consulta**')
        st.link_button('Linhas e horários de ônibus', 'https://servicos.semobjp.pb.gov.br/linhas-de-onibus/', use_container_width=True)
        st.link_button('Consultar local de votação', 'https://www.tse.jus.br/servicos-eleitorais/local-de-votacao-zonas-eleitorais', use_container_width=True)
        st.link_button('Serviços eleitorais do TSE', 'https://www.tse.jus.br/servicos-eleitorais/autoatendimento-eleitoral/', use_container_width=True)
        st.caption('Os links abrem os serviços oficiais. Horários e informações atuais devem ser consultados nesses portais.')
        st.markdown(f'**Votos em branco · {turn}º turno**')
        st.markdown(f"{number(selected['brancos'])} votos · **{percent(selected['brancos'], selected['comparecimento'])}** do comparecimento")
    st.markdown('<div class="method"><strong>Como ler os números</strong><br>Abstenção é calculada sobre o eleitorado apto. Brancos e nulos usam o comparecimento como base. São indicadores distintos e não revelam preferência política nem intenção de voto.</div>', unsafe_allow_html=True)

with compare_tab:
    st.subheader('Participação nos dois turnos de 2024')
    st.caption('João Pessoa · Eleição para prefeito · A comparação descreve o município inteiro.')
    c1, c2 = st.columns(2, gap='large')
    for col, row in zip([c1, c2], data['eleicoes']):
        with col:
            st.markdown(f"### {row['turno']}º turno · {row['data']}")
            for label, key, base, color in [('Comparecimento', 'comparecimento', 'eleitorado', '#354d68'), ('Abstenções', 'abstencoes', 'eleitorado', '#cb102a'), ('Votos nulos', 'nulos', 'comparecimento', '#766485'), ('Votos em branco', 'brancos', 'comparecimento', '#738294')]:
                pct = 100 * row[key] / row[base]
                st.markdown(f'<div class="bar-row"><div class="bar-label"><span>{label}</span><strong>{percent(row[key], row[base])}</strong></div><div class="bar-track"><div class="bar-fill" style="width:{pct:.4f}%;background:{color}"></div></div><div class="small-note">{number(row[key])} · base: {"eleitorado apto" if base == "eleitorado" else "comparecimento"}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('**Totais para conferência**')
    st.table([{'Indicador': label, '1º turno': number(data['eleicoes'][0][key]), '2º turno': number(data['eleicoes'][1][key])} for label, key in [('Eleitorado apto', 'eleitorado'), ('Comparecimento', 'comparecimento'), ('Abstenções', 'abstencoes'), ('Votos em branco', 'brancos'), ('Votos nulos', 'nulos')]])

with source_tab:
    st.subheader('Fontes e metodologia')
    st.markdown('Os indicadores eleitorais foram conferidos nas tabelas municipais do **TRE-PB**. A população vem do **Censo 2022 do IBGE**. O mapa combina a malha municipal simplificada do IBGE com ruas do OpenStreetMap.')
    for source in data['fontes']:
        st.markdown(f"**[{source['titulo']}]({source['url']})**  \n{source['descricao']}")
    st.markdown('### Critérios de leitura')
    st.markdown('- Recorte fixo: João Pessoa (PB), código IBGE 2507507.\n- Eleição para prefeito, primeiro e segundo turnos de 2024.\n- Abstenções ÷ eleitorado apto; brancos e nulos ÷ comparecimento.\n- Percentuais calculados a partir dos totais, com duas casas decimais.\n- População residente e eleitorado são universos diferentes, de anos diferentes.\n- Dados agregados não identificam pessoas, preferências ou motivos da ausência.\n- O limite municipal é simplificado e serve para referência cartográfica.')
    st.info('Esta é uma fotografia histórica. Não há atualização eleitoral em tempo real nem dados da eleição de 2026.')
    st.markdown('### Sobre a referência visual')
    st.markdown('O site [Onde dá pra conversar](https://www.ondedapraconversar.com.br/) inspirou a consulta por mapa e a identidade vermelha. Os números deste painel vêm das fontes oficiais acima; não reproduzem classificações ou recomendações de locais do site de referência.')

st.markdown('<div class="footer"><strong>★ Lula &amp; PT · João Pessoa</strong><br>Iniciativa independente, sem vínculo oficial declarado com Lula, PT, Prefeitura, TSE ou IBGE. Identidade partidária explícita; indicadores públicos apresentados de forma descritiva.<br>Fontes consultadas em 07/10/2026 · Eleições 2024 · Censo 2022 · Mapa © OpenStreetMap / IBGE</div>', unsafe_allow_html=True)
