"""Entrypoint do Streamlit Community Cloud e da execução local."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "dist" / "app.py"), run_name="__main__")
