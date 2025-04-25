from .lib import *

from pathlib import Path

parent_path = Path(__file__).resolve().parent
template_kml_path = parent_path / "template.kml"

# Read in template KML
with open(template_kml_path, "r", encoding="utf-8") as f:
    kml_template = f.read()

# Define waypoints with actions
waypoints = [
    {
        'lat': 48.19014118, 
        'lng': 11.499985362, 
        'height': 20,
        'actions': [
            create_rotate_yaw_action(0),
            create_gimbal_rotate_action(pitch_angle=0),
            create_zoom_action(24),
            create_gimbal_rotate_action(pitch_angle=-58.9),
            create_rotate_yaw_action(-105.6),
            create_take_photo_action()
        ]
    },
    {
        'lat': 48.19114118, 
        'lng': 11.500985362, 
        'height': 30,
        'actions': [
            create_rotate_yaw_action(90),
            create_gimbal_rotate_action(pitch_angle=-45),
            create_take_photo_action()
        ]
    }
]

# Edit only the Placemarks in the KML
kml_data = edit_dji_kml_placemarks(kml_template, waypoints, "Binh Pham")

# Save the updated KML
save_kml(kml_data, "output.kml")

# Alternatively, edit a KMZ file
# edit_kmz_placemarks("input.kmz", "output.kmz", waypoints, "Binh Pham")