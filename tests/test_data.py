import json
import csv
from copy import deepcopy
import unittest
from pathlib import Path
from scripts.import_tse import normalize

ROOT = Path(__file__).resolve().parents[1] / 'dist'


class DataIntegrity(unittest.TestCase):
    def test_official_totals_and_denominators(self):
        data = json.loads((ROOT / 'data/indicadores.json').read_text())
        self.assertEqual(data['municipio']['codigo_ibge'], '2507507')
        self.assertEqual(len(data['eleicoes']), 1)
        row = data['eleicoes'][0]
        self.assertEqual((row['ano'], row['turno'], row['cargo'], row['municipio_tse']), (2026, 1, 'Presidente', '20516'))
        self.assertEqual(tuple(row[k] for k in ['eleitorado', 'comparecimento', 'abstencoes', 'brancos', 'nulos']), (591750, 496403, 95347, 9441, 15992))
        self.assertEqual(row['comparecimento'] + row['abstencoes'], row['eleitorado'])
        self.assertEqual(row['brancos'] + row['nulos'] + row['validos'], row['comparecimento'])
        self.assertEqual(row['nulos'], row['nulos_urna'] + row['nulos_tecnicos'])
        candidates = {c['numero']: c['votos'] for c in row['candidatos']}
        self.assertEqual((candidates['13'], candidates['22']), (219023, 215086))
        self.assertEqual(sum(candidates.values()), row['validos'])
        self.assertEqual(round(row['nulos'] / row['comparecimento'] * 100, 2), 3.22)

    def test_import_rejects_wrong_election_or_office(self):
        raw = json.loads((ROOT / 'data/tse-presidente-jp-2026.json').read_text())
        for key, invalid in [('ele', '2024'), ('t', '2'), ('cdabr', '19810')]:
            altered = deepcopy(raw)
            altered[key] = invalid
            with self.assertRaises(ValueError): normalize(altered)
        altered = deepcopy(raw)
        altered['carg'][0]['cd'] = '3'
        with self.assertRaises(ValueError): normalize(altered)

    def test_csv_matches_official_snapshot(self):
        with (ROOT / 'data/indicadores.csv').open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle, delimiter=';'))
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['ano'], rows[0]['turno'], rows[0]['cargo']), ('2026', '1', 'Presidente'))
        self.assertEqual((rows[0]['lula_13'], rows[0]['flavio_22'], rows[0]['nulos']), ('219023', '215086', '15992'))

    def test_municipal_boundary(self):
        geo = json.loads((ROOT / 'data/municipio.geojson').read_text())
        self.assertEqual(len(geo['features']), 1)
        ring = geo['features'][0]['geometry']['coordinates'][0]
        self.assertEqual(ring[0], ring[-1])
        self.assertTrue(all(-35 < lon < -34.7 and -7.4 < lat < -7 for lon, lat in ring))


if __name__ == '__main__':
    unittest.main()
