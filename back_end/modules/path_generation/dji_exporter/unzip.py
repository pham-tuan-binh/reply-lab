import zipfile
from pathlib import Path

# Get Template KML path
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "output"
KMZ_FINAL_FILE = BASE_DIR / "output" / "Group14.kmz"

with zipfile.ZipFile(KMZ_FINAL_FILE, 'r') as kmz:
    kmz.extractall(OUTPUT_PATH)