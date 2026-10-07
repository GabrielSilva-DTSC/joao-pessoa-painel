"""Importa apenas o cadastro público dos locais de João Pessoa, 1º turno/2026.

Atualizar: python scripts/import_locais_tse.py --zip /caminho/arquivo-tse.zip
Reproduzir com o recorte preservado: python scripts/import_locais_tse.py
Não importa votos, perfil de eleitores, telefones ou quantitativos de eleitorado.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import unicodedata
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'dist' / 'data'
SOURCE = 'https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip'
CATALOG = 'https://dadosabertos.tse.jus.br/dataset/eleitorado-2026'
MEMBER = 'eleitorado_local_votacao_2026_PB.csv'
FIELDS = [
    'DT_GERACAO', 'HH_GERACAO', 'AA_ELEICAO', 'DT_ELEICAO', 'NR_TURNO',
    'SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO',
    'DS_TIPO_SECAO_AGREGADA', 'NR_SECAO_PRINCIPAL', 'NR_LOCAL_VOTACAO',
    'NM_LOCAL_VOTACAO', 'DS_TIPO_LOCAL', 'DS_ENDERECO', 'NM_BAIRRO',
    'NR_CEP', 'NR_LATITUDE', 'NR_LONGITUDE', 'DS_SITU_LOCAL_VOTACAO',
    'DS_SITU_SECAO',
]
LOCAL_FIELDS = {
    'nome': 'NM_LOCAL_VOTACAO', 'endereco': 'DS_ENDERECO',
    'bairro': 'NM_BAIRRO', 'cep': 'NR_CEP', 'tipo': 'DS_TIPO_LOCAL',
    'situacao': 'DS_SITU_LOCAL_VOTACAO',
}


def in_scope(row):
    return tuple(row[k] for k in ('AA_ELEICAO', 'NR_TURNO', 'SG_UF', 'CD_MUNICIPIO')) == ('2026', '1', 'PB', '20516')


def point_in_ring(lon, lat, ring):
    inside = False
    for a, b in zip(ring, ring[1:]):
        # A point on the simplified boundary is valid, too.
        cross = (lon - a[0]) * (b[1] - a[1]) - (lat - a[1]) * (b[0] - a[0])
        if abs(cross) < 1e-12 and min(a[0], b[0]) <= lon <= max(a[0], b[0]) and min(a[1], b[1]) <= lat <= max(a[1], b[1]):
            return True
        if (a[1] > lat) != (b[1] > lat) and lon < (b[0] - a[0]) * (lat - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


def coordinates(row, geometry):
    try:
        lat = float(row['NR_LATITUDE'].replace(',', '.'))
        lon = float(row['NR_LONGITUDE'].replace(',', '.'))
    except ValueError:
        return None, None, 'ausente_ou_invalida'
    if not all(math.isfinite(x) for x in (lat, lon)) or lat in (-1, 0) or lon in (-1, 0) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None, 'ausente_ou_invalida'
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    for polygon in polygons:
        if point_in_ring(lon, lat, polygon[0]) and not any(point_in_ring(lon, lat, hole) for hole in polygon[1:]):
            return lat, lon, 'tse'
    return None, None, 'fora_do_limite_municipal'


def positive_integer(value):
    result = int(value)
    if result <= 0:
        raise ValueError('Identificador eleitoral inválido.')
    return result


def normalize(rows, geo):
    groups, seen, generated = {}, set(), set()
    geometry = geo['features'][0]['geometry']
    for row in rows:
        if not in_scope(row) or row['DT_ELEICAO'] != '04/10/2026':
            raise ValueError('O recorte deve conter somente João Pessoa/PB, 1º turno de 2026.')
        generated.add(f"{row['DT_GERACAO']} {row['HH_GERACAO']}")
        zone, local, section = (positive_integer(row[k]) for k in ('NR_ZONA', 'NR_LOCAL_VOTACAO', 'NR_SECAO'))
        if (zone, section) in seen:
            raise ValueError(f'Seção duplicada: zona {zone}, seção {section}.')
        seen.add((zone, section))
        lat, lon, quality = coordinates(row, geometry)
        attrs = {key: (row[field].strip() if row[field].strip() not in ('#NULO', '-1') else '') for key, field in LOCAL_FIELDS.items()}
        attrs.update(latitude=lat, longitude=lon, coordenada=quality)
        key = f'{zone}-{local}'
        if key not in groups:
            groups[key] = {'id': key, 'zona': zone, 'numero': local, **attrs, 'secoes': [], 'agregadas': [], 'distribuidas': []}
        site = groups[key]
        if any(site[field] != value for field, value in attrs.items()):
            raise ValueError(f'Cadastro conflitante dentro do local {key}.')
        section_type = row['DS_TIPO_SECAO_AGREGADA']
        if section_type == 'Principal':
            site['secoes'].append(section)
        elif section_type == 'Agregada':
            site['agregadas'].append({'numero': section, 'principal': positive_integer(row['NR_SECAO_PRINCIPAL'])})
        elif section_type == 'Distribuída de ofício':
            site['distribuidas'].append(section)
        else:
            raise ValueError(f'Tipo de seção não reconhecido: {section_type}.')
    if not groups or len(generated) != 1:
        raise ValueError('Base vazia ou com múltiplas datas de geração.')
    principal_sites = {(s['zona'], number): s for s in groups.values() for number in s['secoes']}
    for site in groups.values():
        site['secoes'].sort()
        site['agregadas'].sort(key=lambda s: s['numero'])
        site['distribuidas'].sort()
        for section in site['agregadas']:
            principal = principal_sites.get((site['zona'], section['principal']))
            if principal is None:
                raise ValueError(f"Seção agregada sem principal na zona {site['zona']}.")
            section['local_principal'] = principal['id']
            section['nome_local_principal'] = principal['nome']
    sites = sorted(groups.values(), key=lambda s: (unicodedata.normalize('NFKD', s['nome']), s['zona'], s['numero']))
    return {
        'municipio': {'nome': 'João Pessoa', 'uf': 'PB', 'codigo_tse': '20516', 'codigo_ibge': '2507507'},
        'ano': 2026, 'turno': 1, 'data_eleicao': '04/10/2026', 'geracao_tse': generated.pop(),
        'resumo': {
            'locais': len(sites), 'com_coordenadas': sum(s['coordenada'] == 'tse' for s in sites),
            'sem_coordenadas': sum(s['coordenada'] != 'tse' for s in sites),
            'secoes_principais': sum(len(s['secoes']) for s in sites),
            'secoes_agregadas': sum(len(s['agregadas']) for s in sites),
            'secoes_distribuidas': sum(len(s['distribuidas']) for s in sites),
        },
        'locais': sites,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, help='ZIP oficial baixado do TSE')
    parser.add_argument('--consulta-em', default='2026-10-07')
    args = parser.parse_args()
    snapshot = DATA / 'tse-locais-jp-2026.csv'
    manifest = DATA / 'tse-locais-fonte.json'
    if args.zip:
        with zipfile.ZipFile(args.zip) as archive:
            raw = archive.read(MEMBER)
        reader = csv.DictReader(io.StringIO(raw.decode('latin1')), delimiter=';')
        rows = [{k: r[k] for k in FIELDS} for r in reader if in_scope(r)]
        provenance = {
            'titulo': 'TSE · Eleitorado por local de votação · 2026',
            'url': SOURCE, 'catalogo': CATALOG, 'arquivo': MEMBER,
            'consulta_em': args.consulta_em,
            'sha256_csv_pb': hashlib.sha256(raw).hexdigest(),
            'nota': 'Recorte municipal apenas com campos do cadastro de locais e seções; sem dados de eleitores ou votação. Coordenadas do TSE, sem geocodificação complementar.',
        }
    else:
        content = snapshot.read_bytes()
        provenance = json.loads(manifest.read_text(encoding='utf-8'))
        if hashlib.sha256(content).hexdigest() != provenance['sha256_recorte']:
            raise ValueError('O recorte difere do checksum registrado na origem.')
        rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig')), delimiter=';'))
    result = normalize(rows, json.loads((DATA / 'municipio.geojson').read_text(encoding='utf-8')))
    if args.zip:
        with snapshot.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter=';', lineterminator='\n')
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda r: (int(r['NR_ZONA']), int(r['NR_SECAO']))))
        provenance['sha256_recorte'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result['fonte'] = provenance
    (DATA / 'locais-votacao.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['resumo'], ensure_ascii=False))


if __name__ == '__main__':
    main()
