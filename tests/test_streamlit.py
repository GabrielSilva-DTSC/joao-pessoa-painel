"""Verifica a entrada que será usada pelo Streamlit Community Cloud."""
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


class StreamlitDeployment(unittest.TestCase):
    def test_entrypoint_loads_presidential_data_and_map(self):
        entrypoint = Path(__file__).resolve().parents[1] / 'streamlit_app.py'
        app = AppTest.from_file(str(entrypoint)).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.radio), 0)
        self.assertEqual(app.title[0].value, 'João Pessoa · Presidente 2026')
        markup = '\n'.join(item.value for item in app.markdown)
        for expected in ['219.023', '215.086', '95.347', '15.992']:
            self.assertIn(expected, markup)
        self.assertNotIn('2024', markup)
        self.assertNotIn('prefeito', markup.lower())
        app.checkbox[0].set_value(False).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertFalse(app.checkbox[0].value)


if __name__ == '__main__':
    unittest.main()
