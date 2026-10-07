"""Protege o recorte geográfico e a distinção entre local, seção e urna."""
import csv
import json
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.import_locais_tse import normalize

DATA = Path(__file__).resolve().parents[1] / 'dist' / 'data'


class PollingLocations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (DATA / 'tse-locais-jp-2026.csv').open(encoding='utf-8-sig', newline='') as handle:
            cls.rows = list(csv.DictReader(handle, delimiter=';'))
        cls.geo = json.loads((DATA / 'municipio.geojson').read_text())

    def test_snapshot_reproduces_sites_and_election_sections(self):
        result = normalize(self.rows, self.geo)
        published = json.loads((DATA / 'locais-votacao.json').read_text())
        self.assertEqual(result['locais'], published['locais'])
        self.assertEqual(result['resumo'], {'locais': 221, 'com_coordenadas': 220, 'sem_coordenadas': 1, 'secoes_principais': 1714, 'secoes_agregadas': 5, 'secoes_distribuidas': 0})
        # One source row per section, but one marker per zone/local combination.
        self.assertEqual(len(self.rows), 1719)
        self.assertEqual(len({s['id'] for s in result['locais']}), 221)
        self.assertEqual(sum(s['situacao'] == 'BLOQUEADO' for s in result['locais']), 11)
        missing = next(s for s in result['locais'] if s['id'] == '77-1686')
        self.assertIsNone(missing['latitude'])
        self.assertIsNone(missing['longitude'])
        aggregated = next(s for s in result['locais'] if s['id'] == '77-1635')['agregadas'][0]
        self.assertEqual((aggregated['numero'], aggregated['principal'], aggregated['local_principal']), (413, 77, '77-1139'))

    def test_wrong_scope_and_duplicate_sections_are_rejected(self):
        for key, value in [('CD_MUNICIPIO', '19810'), ('SG_UF', 'PE'), ('NR_TURNO', '2'), ('AA_ELEICAO', '2024')]:
            row = deepcopy(self.rows[0])
            row[key] = value
            with self.assertRaises(ValueError):
                normalize([row], self.geo)
        with self.assertRaises(ValueError):
            normalize([self.rows[0], self.rows[0]], self.geo)

    def test_invalid_or_outside_coordinates_never_become_map_points(self):
        for lat, lon in [('NaN', '-34.85'), ('-1', '-1'), ('-7.1', '-35.5'), ('0', '0')]:
            row = deepcopy(self.rows[0])
            row.update(NR_LATITUDE=lat, NR_LONGITUDE=lon)
            site = normalize([row], self.geo)['locais'][0]
            self.assertIsNone(site['latitude'])
            self.assertIsNone(site['longitude'])
            self.assertNotEqual(site['coordenada'], 'tse')

    def test_inconsistent_location_metadata_is_rejected(self):
        row = deepcopy(self.rows[0])
        row.update(NR_SECAO='9999', DS_ENDERECO='ENDEREÇO CONFLITANTE')
        with self.assertRaises(ValueError):
            normalize([self.rows[0], row], self.geo)


if __name__ == '__main__':
    unittest.main()
