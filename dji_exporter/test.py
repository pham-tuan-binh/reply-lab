import xml.etree.ElementTree as ET
import difflib
import re
from pathlib import Path

# Import our KML editor functions
from lib import (
    edit_dji_kml_placemarks,
    create_rotate_yaw_action,
    create_gimbal_rotate_action,
    create_zoom_action,
    create_take_photo_action,
    save_kml
)

def extract_waypoints_from_kml(kml_string):
    """Extract waypoints and their actions from a KML string"""
    root = ET.fromstring(kml_string)
    
    # Register namespaces
    ns = {'kml': 'http://www.opengis.net/kml/2.2', 
          'wpml': 'http://www.dji.com/wpmz/1.0.6'}
    
    waypoints = []
    
    # Find the Folder containing waypoints
    document = root.find('./kml:Document', ns) if root.tag.endswith('kml') else root.find('./Document')
    folder = document.find('./kml:Folder', ns) or document.find('./Folder')
    
    # Get author name
    author_elem = document.find('./wpml:author', ns)
    author_name = author_elem.text if author_elem is not None else "Unknown"
    
    # Extract each placemark
    for placemark in folder.findall('./kml:Placemark', ns) or folder.findall('./Placemark'):
        # Get coordinates
        coords_elem = placemark.find('./kml:Point/kml:coordinates', ns) or placemark.find('./Point/coordinates')
        if coords_elem is None:
            continue
            
        coords_text = coords_elem.text.strip()
        parts = coords_text.split(',')
        if len(parts) < 2:
            continue
            
        lng = float(parts[0].strip())
        lat = float(parts[1].strip())
        
        # Get height
        height_elem = placemark.find('./wpml:height', ns)
        height = float(height_elem.text) if height_elem is not None else None
        
        # Extract actions
        actions = []
        action_group = placemark.find('./wpml:actionGroup', ns)
        if action_group is not None:
            for action_elem in action_group.findall('./wpml:action', ns):
                action_type_elem = action_elem.find('./wpml:actionActuatorFunc', ns)
                if action_type_elem is None:
                    continue
                    
                action_type = action_type_elem.text
                
                # Extract parameters
                params = {}
                params_elem = action_elem.find('./wpml:actionActuatorFuncParam', ns)
                if params_elem is not None:
                    for param in params_elem:
                        tag = param.tag.split('}')[-1]  # Remove namespace
                        params[tag] = param.text
                
                # Create action based on type
                if action_type == 'rotateYaw':
                    heading = float(params.get('aircraftHeading', 0))
                    path_mode = params.get('aircraftPathMode', 'counterClockwise')
                    actions.append(create_rotate_yaw_action(heading, path_mode))
                elif action_type == 'gimbalRotate':
                    pitch_angle = float(params.get('gimbalPitchRotateAngle')) if params.get('gimbalPitchRotateEnable') == '1' else None
                    roll_angle = float(params.get('gimbalRollRotateAngle')) if params.get('gimbalRollRotateEnable') == '1' else None
                    yaw_angle = float(params.get('gimbalYawRotateAngle')) if params.get('gimbalYawRotateEnable') == '1' else None
                    yaw_base = params.get('gimbalHeadingYawBase', 'north')
                    rotate_mode = params.get('gimbalRotateMode', 'absoluteAngle')
                    payload_index = int(params.get('payloadPositionIndex', 0))
                    actions.append(create_gimbal_rotate_action(pitch_angle, roll_angle, yaw_angle, yaw_base, rotate_mode, payload_index))
                elif action_type == 'zoom':
                    focal_length = float(params.get('focalLength', 24))
                    use_focal_factor = params.get('isUseFocalFactor') == '1'
                    payload_index = int(params.get('payloadPositionIndex', 0))
                    actions.append(create_zoom_action(focal_length, use_focal_factor, payload_index))
                elif action_type == 'takePhoto':
                    payload_index = int(params.get('payloadPositionIndex', 0))
                    use_global_index = params.get('useGlobalPayloadLensIndex') == '1'
                    actions.append(create_take_photo_action(payload_index, use_global_index))
                else:
                    # Add other action types as needed
                    pass
        
        # Create waypoint dictionary
        waypoint = {
            'lat': lat,
            'lng': lng,
            'height': height,
            'actions': actions
        }
        
        waypoints.append(waypoint)
    
    return waypoints, author_name

def normalize_xml(xml_string):
    """Normalize XML for comparison by removing timestamp differences and whitespace"""
    # Remove xml declaration line
    xml_string = re.sub(r'<\?xml[^>]+\?>\s*', '', xml_string)
    
    # Remove timestamp values
    xml_string = re.sub(r'<wpml:createTime>\d+</wpml:createTime>', '<wpml:createTime>TIMESTAMP</wpml:createTime>', xml_string)
    xml_string = re.sub(r'<wpml:updateTime>\d+</wpml:updateTime>', '<wpml:updateTime>TIMESTAMP</wpml:updateTime>', xml_string)
    
    # Normalize whitespace
    xml_string = re.sub(r'>\s+<', '><', xml_string)
    xml_string = re.sub(r'\s+', ' ', xml_string)
    
    return xml_string.strip()

def compare_kml_files(original_kml, generated_kml):
    """Compare two KML files and show differences"""
    norm_original = normalize_xml(original_kml)
    norm_generated = normalize_xml(generated_kml)
    
    if norm_original == norm_generated:
        print("KML files are structurally identical (excluding timestamps)!")
        return True
    
    # Create a diff
    diff = difflib.unified_diff(
        norm_original.splitlines(),
        norm_generated.splitlines(),
        fromfile='original',
        tofile='generated',
        lineterm=''
    )
    
    print("Differences found:")
    for line in diff:
        print(line)
    
    return False

def test_kml_recreation():
    """Test the KML recreation process"""
    # Load the original template KML
    parent_path = Path(__file__).resolve().parent
    template_kml_path = parent_path / "template.kml"
    
    with open(template_kml_path, "r", encoding="utf-8") as f:
        original_kml = f.read()
    
    # Extract waypoints from the original KML
    waypoints, author_name = extract_waypoints_from_kml(original_kml)
    
    print(f"Extracted {len(waypoints)} waypoints from original KML")
    for i, wp in enumerate(waypoints):
        print(f"Waypoint {i}:")
        print(f"  Lat: {wp['lat']}, Lng: {wp['lng']}, Height: {wp['height']}")
        print(f"  Actions: {len(wp['actions'])}")
    
    # Use our function to create a new KML with the extracted waypoints
    generated_kml = edit_dji_kml_placemarks(original_kml, waypoints, author_name)
    
    # Save for inspection
    save_kml(generated_kml, "regenerated.kml")
    
    # Compare the original and generated KML files
    print("\nComparing KML files:")
    is_identical = compare_kml_files(original_kml, generated_kml)
    
    if is_identical:
        print("Test PASSED: Generated KML matches the original!")
    else:
        print("Test WARNING: There are differences between the original and generated KML")
        print("Check 'regenerated.kml' for details")

if __name__ == "__main__":
    test_kml_recreation()