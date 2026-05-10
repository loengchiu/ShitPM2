from pathlib import Path
import runpy

TARGET = Path(__file__).resolve().parent / 'scripts' / 'python' / 'shitpm-host.py'
runpy.run_path(str(TARGET), run_name='__main__')
