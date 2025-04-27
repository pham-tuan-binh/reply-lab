import zipfile
import os
from pathlib import Path
from .lib import *

# Get Template KML path
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_KML_PATH = BASE_DIR / "template"
TEMPLATE_KMZ_FILE = TEMPLATE_KML_PATH / "final.kmz"

TEMPLATE_KML_FILE = TEMPLATE_KML_PATH / "wpmz" / "template.kml"
TEMPLATE_WAYLINES_FILE = TEMPLATE_KML_PATH / "wpmz" / "waylines.wpml"

OUTPUT_PATH = BASE_DIR / "wpmz"

KMZ_FINAL_FILE = BASE_DIR / "output" / "Group14.kmz"

# Read in template KML
with open(TEMPLATE_KML_FILE, "r", encoding="utf-8") as f:
    kml_template = f.read()

with open(TEMPLATE_WAYLINES_FILE, "r", encoding="utf-8") as f:
    waylines_template = f.read()

def generate_dji_files_from_waypoints(waypoints, output_path):
    kml_data = edit_dji_kml_placemarks(kml_template, waypoints, "Binh Pham")
    waylines_data = edit_dji_kml_placemarks(waylines_template, waypoints, "Binh Pham")
    save_kml(kml_data, output_path / "template.kml")
    save_kml(waylines_data, output_path / "waylines.wpml")

def zip_to_kmz(output_path, folder_name):
    with zipfile.ZipFile(output_path / "Group14.kmz", 'w', zipfile.ZIP_DEFLATED) as kmz:
        for file_path in output_path.glob("*"):
            kmz.write(file_path, arcname=f"{folder_name}/{file_path.name}")

def waypoints_to_kmz(waypoints, output_path):
    generate_dji_files_from_waypoints(waypoints, output_path)
    zip_to_kmz(output_path, "wpmz")

    print(f"KMZ file generated at: {output_path / 'Group14.kmz'}")

# If main
if __name__ == "__main__":
    # Define waypoints with actions
    input_waypoints = [
        {
            'lat': 1, 
            'lng': 2, 
            'alt': 3,
        },
        {
            'lat':4, 
            'lng': 5, 
            'alt': 6,
        },
        {
            'lat': 7, 
            'lng': 8, 
            'alt': 9,
        }
    ]
    
    # Create output directory if it doesn't exist
    waypoints_to_kmz(input_waypoints, OUTPUT_PATH)