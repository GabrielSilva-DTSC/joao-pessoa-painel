import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dist'


class DataIntegrity(unittest.TestCase):
    def test_official_totals_and_denominators(self):
        data = json.loads((ROOT / 'data/indicadores.json').read_text())
        self.assertEqual(data['municipio']['codigo_ibge'], '2507507')
        expected = [(566290, 457121, 109169, 15343, 24544), (566290, 436930, 129360, 11592, 20482)]
        for row, totals in zip(data['eleicoes'], expected):
            self.assertEqual(tuple(row[k] for k in ['eleitorado', 'comparecimento', 'abstencoes', 'brancos', 'nulos']), totals)
            self.assertEqual(row['comparecimento'] + row['abstencoes'], row['eleitorado'])
            self.assertLess(row['brancos'] + row['nulos'], row['comparecimento'])
        self.assertEqual(round(129360 / 566290 * 100, 2), 22.84)
        self.assertEqual(round(20482 / 436930 * 100, 2), 4.69)

    def test_municipal_boundary(self):
        geo = json.loads((ROOT / 'data/municipio.geojson').read_text())
        self.assertEqual(len(geo['features']), 1)
        ring = geo['features'][0]['geometry']['coordinates'][0]
        self.assertEqual(ring[0], ring[-1])
        self.assertTrue(all(-35 < lon < -34.7 and -7.4 < lat < -7 for lon, lat in ring))


if __name__ == '__main__':
    unittest.main()
