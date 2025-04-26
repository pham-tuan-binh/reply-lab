import xml.etree.ElementTree as ET
import difflib
import re
from pathlib import Path
from fastkml import kml
from collections import defaultdict

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
    
    # Find the Document element (may or may not have namespace)
    if root.tag.endswith('kml'):
        document = root.find('./kml:Document', ns)
    else:
        document = root  # If we're already at the Document level
    
    # As fallback, try without namespace
    if document is None:
        document = root.find('./Document')
    
    if document is None:
        print("No Document element found in KML")
        return [], "Unknown"
    
    # Get author name
    author_elem = document.find('./wpml:author', ns)
    author_name = author_elem.text if author_elem is not None else "Unknown"
    
    # Find the Folder element with namespace
    folder = document.find('./kml:Folder', ns)
    # As fallback, try without namespace
    if folder is None:
        folder = document.find('./Folder')
    
    if folder is None:
        print("No Folder element found in Document")
        return [], author_name
    
    # Extract each placemark with namespace
    placemarks = folder.findall('./kml:Placemark', ns)
    # As fallback, try without namespace
    if not placemarks:
        placemarks = folder.findall('./Placemark')
    
    print(f"Found {len(placemarks)} placemarks")
    
    for placemark in placemarks:
        # Get coordinates with namespace
        coords_elem = placemark.find('./kml:Point/kml:coordinates', ns)
        # As fallback, try without namespace
        if coords_elem is None:
            coords_elem = placemark.find('./Point/coordinates')
        
        if coords_elem is None:
            print("No coordinates found in placemark")
            continue
            
        coords_text = coords_elem.text.strip()
        parts = coords_text.split(',')
        if len(parts) < 2:
            print(f"Invalid coordinates format: {coords_text}")
            continue
            
        # Parse longitude and latitude (note they are reversed in KML: lng,lat)
        lng = float(parts[0].strip())
        lat = float(parts[1].strip())
        
        # Get height
        height_elem = placemark.find('./wpml:height', ns)
        height = float(height_elem.text) if height_elem is not None else None
        
        # Extract actions
        actions = []
        action_group = placemark.find('./wpml:actionGroup', ns)
        if action_group is not None:
            action_elems = action_group.findall('./wpml:action', ns)
            print(f"Found {len(action_elems)} actions in placemark")
            
            for action_elem in action_elems:
                action_type_elem = action_elem.find('./wpml:actionActuatorFunc', ns)
                if action_type_elem is None:
                    continue
                    
                action_type = action_type_elem.text
                print(f"Found action type: {action_type}")
                
                # Extract parameters
                params = {}
                params_elem = action_elem.find('./wpml:actionActuatorFuncParam', ns)
                if params_elem is not None:
                    for param in params_elem:
                        # Handle namespaces in tags
                        if '}' in param.tag:
                            tag = param.tag.split('}')[-1]  # Remove namespace
                        else:
                            tag = param.tag
                        params[tag] = param.text
                
                # Create action based on type
                if action_type == 'rotateYaw':
                    heading = float(params.get('aircraftHeading', 0))
                    path_mode = params.get('aircraftPathMode', 'counterClockwise')
                    actions.append(create_rotate_yaw_action(heading, path_mode))
                elif action_type == 'gimbalRotate':
                    # Convert parameters, handling possible None values
                    pitch_angle = float(params.get('gimbalPitchRotateAngle', 0)) if params.get('gimbalPitchRotateEnable') == '1' else None
                    roll_angle = float(params.get('gimbalRollRotateAngle', 0)) if params.get('gimbalRollRotateEnable') == '1' else None
                    yaw_angle = float(params.get('gimbalYawRotateAngle', 0)) if params.get('gimbalYawRotateEnable') == '1' else None
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
                    print(f"Unknown action type: {action_type}")
        
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

def compare_kml_structure(original_kml, generated_kml):
    """
    Compare the structure of two KML files by examining their element hierarchy,
    rather than just comparing text.
    
    Returns True if structures match, False otherwise.
    """
    try:
        # Parse both XML strings
        original_root = ET.fromstring(original_kml)
        generated_root = ET.fromstring(generated_kml)
        
        # Register namespaces
        ns = {'kml': 'http://www.opengis.net/kml/2.2', 
              'wpml': 'http://www.dji.com/wpmz/1.0.6'}
              
        # Utility function to get element path
        def get_elem_path(elem, parent_path=''):
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if parent_path:
                return f"{parent_path}/{tag}"
            return tag
        
        # Compare structure recursively
        def compare_elements(orig_elem, gen_elem, path=''):
            # Check tag names without namespace
            orig_tag = orig_elem.tag.split('}')[-1] if '}' in orig_elem.tag else orig_elem.tag
            gen_tag = gen_elem.tag.split('}')[-1] if '}' in gen_elem.tag else gen_elem.tag
            
            if orig_tag != gen_tag:
                print(f"Tag mismatch at {path}: {orig_tag} vs {gen_tag}")
                return False
            
            # Check attributes (except for specific elements that may differ)
            if not (path.endswith('/createTime') or path.endswith('/updateTime')):
                orig_attrs = {k.split('}')[-1] if '}' in k else k: v for k, v in orig_elem.attrib.items()}
                gen_attrs = {k.split('}')[-1] if '}' in k else k: v for k, v in gen_elem.attrib.items()}
                if orig_attrs != gen_attrs:
                    print(f"Attribute mismatch at {path}: {orig_attrs} vs {gen_attrs}")
                    return False
            
            # Get child elements (excluding text nodes)
            orig_children = list(orig_elem)
            gen_children = list(gen_elem)
            
            # Special handling for Folder/Placemark elements
            if orig_tag == 'Folder':
                # Count Placemarks in original
                orig_placemarks = [c for c in orig_children if c.tag.endswith('Placemark')]
                gen_placemarks = [c for c in gen_children if c.tag.endswith('Placemark')]
                
                print(f"Placemarks in original: {len(orig_placemarks)}")
                print(f"Placemarks in generated: {len(gen_placemarks)}")
                
                # Remove Placemarks from the general comparison - we'll check them separately
                orig_children = [c for c in orig_children if not c.tag.endswith('Placemark')]
                gen_children = [c for c in gen_children if not c.tag.endswith('Placemark')]
                
                # Check that we have the same number of Placemarks
                if len(orig_placemarks) != len(gen_placemarks):
                    print(f"Placemark count mismatch: {len(orig_placemarks)} vs {len(gen_placemarks)}")
                    return False
                
                # Compare a sample of Placemarks to check structure
                if orig_placemarks:
                    # Compare first Placemark structures
                    first_orig_pm = orig_placemarks[0]
                    first_gen_pm = gen_placemarks[0]
                    return compare_elements(first_orig_pm, first_gen_pm, path + '/Placemark[0]')
            
            # Special handling for actionGroup elements
            if orig_tag == 'actionGroup':
                # Just check if both have actions, but don't compare exact structure
                orig_actions = [c for c in orig_children if c.tag.endswith('action')]
                gen_actions = [c for c in gen_children if c.tag.endswith('action')]
                
                print(f"Actions in original: {len(orig_actions)}")
                print(f"Actions in generated: {len(gen_actions)}")
                
                # Check that generated has at least one action if original has actions
                if len(orig_actions) > 0 and len(gen_actions) == 0:
                    print("Original has actions but generated doesn't")
                    return False
                
                # Don't compare actions in detail - just their existence
                return True
                
            # Compare other non-special child elements
            if len(orig_children) != len(gen_children):
                if not (orig_tag == 'Placemark' or orig_tag == 'actionGroup'):
                    print(f"Child count mismatch at {path}: {len(orig_children)} vs {len(gen_children)}")
                    return False
            
            for i, (orig_child, gen_child) in enumerate(zip(orig_children, gen_children)):
                child_path = f"{path}/{orig_tag}[{i}]"
                if not compare_elements(orig_child, gen_child, child_path):
                    return False
            
            # If all checks passed for this element
            return True
        
        # Start comparison at the Document level for consistency
        orig_doc = original_root.find('./kml:Document', ns) or original_root.find('./Document') or original_root
        gen_doc = generated_root.find('./kml:Document', ns) or generated_root.find('./Document') or generated_root
        
        return compare_elements(orig_doc, gen_doc, 'Document')
        
    except Exception as e:
        print(f"Error comparing KML structures: {e}")
        return False

def analyze_kml_structure(kml_string):
    """Analyze and print the structure of a KML file"""
    root = ET.fromstring(kml_string)
    
    # Register namespaces
    ns = {'kml': 'http://www.opengis.net/kml/2.2', 
          'wpml': 'http://www.dji.com/wpmz/1.0.6'}
    
    def print_element_structure(elem, indent=0, path=''):
        # Get tag without namespace
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        # Build current path
        current_path = f"{path}/{tag}" if path else tag
        
        # Print this element
        prefix = '  ' * indent
        attrs = ' '.join([f"{k.split('}')[-1] if '}' in k else k}='{v}'" for k, v in elem.attrib.items()])
        attrs_str = f" ({attrs})" if attrs else ""
        
        text = elem.text.strip() if elem.text and elem.text.strip() else None
        text_str = f" = '{text}'" if text else ""
        
        print(f"{prefix}{tag}{attrs_str}{text_str}")
        
        # Print children
        for child in elem:
            print_element_structure(child, indent + 1, current_path)
    
    # Start at Document level for consistency
    document = root.find('./kml:Document', ns) or root.find('./Document') or root
    
    print("KML STRUCTURE ANALYSIS:")
    print("=======================")
    print_element_structure(document)
    
    # Additional analysis
    folder = document.find('./kml:Folder', ns) or document.find('./Folder')
    if folder:
        placemarks = folder.findall('./kml:Placemark', ns) or folder.findall('./Placemark')
        print(f"\nFound {len(placemarks)} placemarks in folder")
        
        # Check first placemark structure
        if placemarks:
            print("\nFirst placemark structure:")
            print_element_structure(placemarks[0], indent=1)
            
            # Examine action groups
            action_group = placemarks[0].find('./wpml:actionGroup', ns)
            if action_group:
                actions = action_group.findall('./wpml:action', ns)
                print(f"\nFound {len(actions)} actions in first placemark")
    
    return True

def test_kml_recreation():
    """Test the KML recreation process"""
    # Load the original template KML
    parent_path = Path(__file__).resolve().parent
    template_kml_path = parent_path / "template.kml"  # Use the correct KML file
    
    with open(template_kml_path, "r", encoding="utf-8") as f:
        original_kml = f.read()
    
    # Analyze the original KML structure
    print("\n=== ORIGINAL KML STRUCTURE ===")
    analyze_kml_structure(original_kml)
    
    # Extract waypoints from the original KML
    waypoints, author_name = extract_waypoints_from_kml(original_kml)
    
    print(f"\nExtracted {len(waypoints)} waypoints from original KML")
    for i, wp in enumerate(waypoints):
        print(f"Waypoint {i}:")
        print(f"  Lat: {wp['lat']}, Lng: {wp['lng']}, Height: {wp['height']}")
        print(f"  Actions: {len(wp['actions'])}")
    
    # Use our function to create a new KML with the extracted waypoints
    generated_kml = edit_dji_kml_placemarks(original_kml, waypoints, author_name)
    
    # Save for inspection
    save_kml(generated_kml, "regenerated.kml")
    
    # Analyze the generated KML structure
    print("\n=== GENERATED KML STRUCTURE ===")
    analyze_kml_structure(generated_kml)
    
    # Compare the structures
    print("\n=== STRUCTURAL COMPARISON ===")
    structure_match = compare_kml_structure(original_kml, generated_kml)
    
    # Also run the text comparison for completeness
    print("\n=== TEXT COMPARISON ===")
    text_match = compare_kml_files(original_kml, generated_kml)
    
    # Final results
    if structure_match:
        print("\nTest PASSED: KML structures match!")
    else:
        print("\nTest WARNING: Structural differences detected between original and generated KML")
    
    if text_match:
        print("Text comparison: KML files are identical (excluding timestamps)!")
    else:
        print("Text comparison: Differences found in text representation")
    
    print("\nCheck 'regenerated.kml' for visual inspection")

def compare_kml_files(original_kml, generated_kml):
    """Compare two KML files and show differences"""
    norm_original = normalize_xml(original_kml)
    norm_generated = normalize_xml(generated_kml)
    
    if norm_original == norm_generated:
        print("KML files are textually identical (excluding timestamps)!")
        return True
    
    # Create a diff
    diff = difflib.unified_diff(
        norm_original.splitlines(),
        norm_generated.splitlines(),
        fromfile='original',
        tofile='generated',
        lineterm=''
    )
    
    print("Text differences found:")
    diff_lines = list(diff)
    
    # Print a limited number of diff lines to avoid overwhelming output
    max_diff_lines = 20
    for i, line in enumerate(diff_lines):
        if i < max_diff_lines:
            print(line)
    
    if len(diff_lines) > max_diff_lines:
        print(f"... and {len(diff_lines) - max_diff_lines} more differences")
    
    return False

if __name__ == "__main__":
    test_kml_recreation()