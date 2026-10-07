"""Regera os indicadores a partir da cópia municipal oficial do TSE.

Uso: python scripts/import_tse.py
O arquivo de origem está em dist/data/tse-presidente-jp-2026.json.
O importador recusa outro município, cargo, turno ou eleição.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dist' / 'data'
SOURCE = 'https://resultados.tse.jus.br/oficial/ele2026/6257/dados/pb/pb20516-c0001-e006257-u.json'


def normalize(raw):
    if (raw['ele'], raw['t'], raw['tpabr'], raw['cdabr']) != ('6257', '1', 'mu', '20516'):
        raise ValueError('A fonte deve corresponder a João Pessoa, eleição 6257, primeiro turno.')
    if len(raw['carg']) != 1 or raw['carg'][0]['cd'] != '1' or raw['carg'][0]['nmn'] != 'Presidente':
        raise ValueError('A fonte deve ser exclusivamente para Presidente.')
    candidates = []
    for group in raw['carg'][0]['agr']:
        for party in group['par']:
            for candidate in party['cand']:
                candidates.append({'numero': candidate['n'], 'nome': candidate['nmu'], 'partido': party['sg'], 'votos': int(candidate['vap'])})
    candidates.sort(key=lambda candidate: int(candidate['numero']))
    row = {
        'ano': 2026, 'turno': 1, 'data': '04/10/2026', 'cargo': 'Presidente', 'codigo_cargo': '1',
        'eleicao_tse': raw['ele'], 'municipio_tse': raw['cdabr'],
        'eleitorado': int(raw['e']['te']), 'comparecimento': int(raw['e']['c']),
        'abstencoes': int(raw['e']['a']), 'brancos': int(raw['v']['vb']),
        'nulos': int(raw['v']['tvn']), 'nulos_urna': int(raw['v']['vn']),
        'nulos_tecnicos': int(raw['v']['vnt']), 'validos': int(raw['v']['vvc']),
        'secoes_total': int(raw['s']['ts']), 'secoes_totalizadas': int(raw['s']['st']),
        'atualizacao_tse': f"{raw['dt']} {raw['ht']}",
        'geracao_arquivo_tse': f"{raw['dg']} {raw['hg']}",
        'candidatos': candidates, 'fonte': SOURCE,
    }
    if row['comparecimento'] + row['abstencoes'] != row['eleitorado']:
        raise ValueError('Comparecimento e abstenções não reconciliam com o eleitorado.')
    if row['validos'] + row['brancos'] + row['nulos'] != row['comparecimento']:
        raise ValueError('Os votos não reconciliam com o comparecimento.')
    if row['nulos_urna'] + row['nulos_tecnicos'] != row['nulos']:
        raise ValueError('Nulos de urna e técnicos não reconciliam.')
    if sum(candidate['votos'] for candidate in candidates) != row['validos']:
        raise ValueError('Votação nominal não reconcilia com os votos válidos.')
    return row


def main():
    source_bytes = (ROOT / 'tse-presidente-jp-2026.json').read_bytes()
    row = normalize(json.loads(source_bytes))
    row['sha256'] = hashlib.sha256(source_bytes).hexdigest()
    data = json.loads((ROOT / 'indicadores.json').read_text())
    data['consulta_em'] = '2026-10-07'
    data['eleicoes'] = [row]
    data['fontes'] = [{
        'titulo': 'TSE · Presidente · João Pessoa · 1º turno de 2026 (JSON)',
        'url': SOURCE,
        'descricao': 'Eleição 6257, cargo 1, município 20516. Totalização de 05/10/2026 às 12:51:05; arquivo gerado às 12:52:21. Inclui os nulos técnicos no total de nulos.',
    }] + [s for s in data['fontes'] if not s['titulo'].startswith(('TRE-PB', 'TSE · Presidente'))]
    (ROOT / 'indicadores.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    candidates = {c['numero']: c['votos'] for c in row['candidatos']}
    fields = ['municipio', 'uf', 'codigo_ibge', 'ano', 'turno', 'data', 'cargo', 'eleitorado', 'comparecimento', 'abstencoes', 'brancos', 'nulos', 'nulos_urna', 'nulos_tecnicos', 'validos', 'lula_13', 'flavio_22', 'outros_candidatos', 'secoes_total', 'secoes_totalizadas', 'atualizacao_tse', 'fonte']
    values = {'municipio': 'João Pessoa', 'uf': 'PB', 'codigo_ibge': '2507507', **row,
              'lula_13': candidates['13'], 'flavio_22': candidates['22'],
              'outros_candidatos': row['validos'] - candidates['13'] - candidates['22']}
    with (ROOT / 'indicadores.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore', delimiter=';', lineterminator='\n')
        writer.writeheader()
        writer.writerow(values)
    print('Indicadores e CSV atualizados: João Pessoa / Presidente / 2026 / 1º turno.')


if __name__ == '__main__':
    main()
