import xml.etree.ElementTree as ET
from zipfile import ZipFile
import copy
from datetime import datetime
from typing import List, Dict, Any

def edit_dji_kml_placemarks(kml_string, waypoints, author_name="Binh Pham"):
    """
    Edit only the Placemark elements in a DJI KML file with new waypoints and actions,
    preserving all other elements and their values (including takeoff reference point)
    
    Parameters:
    -----------
    kml_string : str
        XML string content of the template KML file
    waypoints : list of dict
        List of waypoint dictionaries with format:
        [{
            'lat': 48.123, 
            'lng': 11.456, 
            'height': 20,  # optional
            'actions': []  # optional list of action dictionaries
        }, ...]
    author_name : str
        Name of the author to set in the KML file
        
    Returns:
    --------
    str
        Modified KML file content as a string
    """
    # Parse the KML XML
    root = ET.fromstring(kml_string)
    
    # Register namespaces
    ns = {'kml': 'http://www.opengis.net/kml/2.2', 
          'wpml': 'http://www.dji.com/wpmz/1.0.6'}
    for prefix, uri in ns.items():
        ET.register_namespace(prefix if prefix != 'kml' else '', uri)
    
    # Update author and timestamps
    now = int(datetime.now().timestamp() * 1000)  # Current time in milliseconds
    
    # Find the Document element - try with namespace first, then without
    document = None
    if root.tag.endswith('kml'):
        document = root.find('./kml:Document', ns)
        if document is None:
            document = root.find('./Document')
    else:
        document = root
    
    if document is None:
        raise ValueError("Invalid KML structure: Document element not found")
    
    # Update author
    author_elem = document.find('./wpml:author', ns)
    if author_elem is not None:
        author_elem.text = author_name
    
    # Update timestamps
    create_time = document.find('./wpml:createTime', ns)
    update_time = document.find('./wpml:updateTime', ns)
    if create_time is not None:
        create_time.text = str(now)
    if update_time is not None:
        update_time.text = str(now)
    
    # Find the Folder containing waypoints - try multiple approaches
    folder = None
    
    # Try with namespace first
    folder = document.find('./kml:Folder', ns)
    
    # Then try without namespace
    if folder is None:
        folder = document.find('./Folder')
    
    # If still not found, try all children to find a Folder element
    if folder is None:
        for child in document:
            if child.tag.endswith('Folder'):
                folder = child
                break
    
    if folder is None:
        raise ValueError("Invalid KML structure: Folder element not found")
    
    # Get the template placemark for cloning - try multiple approaches
    template_placemark = None
    
    # Try with namespace
    template_placemark = folder.find('./kml:Placemark', ns)
    
    # Try without namespace
    if template_placemark is None:
        template_placemark = folder.find('./Placemark')
    
    # Try direct children
    if template_placemark is None:
        for child in folder:
            if child.tag.endswith('Placemark'):
                template_placemark = child
                break
    
    if template_placemark is None:
        raise ValueError("Invalid KML structure: No Placemark found to use as template")
    
    # Get global height setting
    global_height_elem = folder.find('./wpml:globalHeight', ns)
    global_height = 20  # Default
    if global_height_elem is not None:
        try:
            global_height = float(global_height_elem.text)
        except:
            pass
    
    # Find all existing Placemarks using multiple approaches
    existing_placemarks = []
    
    # Try with namespace
    ns_placemarks = folder.findall('./kml:Placemark', ns)
    if ns_placemarks:
        existing_placemarks.extend(ns_placemarks)
    
    # Try without namespace
    non_ns_placemarks = folder.findall('./Placemark')
    if non_ns_placemarks:
        existing_placemarks.extend([p for p in non_ns_placemarks if p not in existing_placemarks])
    
    # Try direct children
    for child in folder:
        if child.tag.endswith('Placemark') and child not in existing_placemarks:
            existing_placemarks.append(child)
    
    # Remove all existing Placemarks
    for placemark in existing_placemarks:
        folder.remove(placemark)
    
    # Add new placemarks for each waypoint
    for idx, waypoint in enumerate(waypoints):
        new_placemark = copy.deepcopy(template_placemark)
        
        # Update coordinates - try multiple approaches
        point = None
        
        # Try with namespace
        point = new_placemark.find('./kml:Point/kml:coordinates', ns)
        
        # Try without namespace
        if point is None:
            point = new_placemark.find('./Point/coordinates')
        
        # Try direct path
        if point is None:
            for point_elem in new_placemark.findall('.//*'):
                if point_elem.tag.endswith('coordinates'):
                    point = point_elem
                    break
        
        if point is not None:
            point.text = f"\n            {waypoint['lng']},{waypoint['lat']}\n          "
        else:
            # If no point element found, create one
            point_elem = ET.SubElement(new_placemark, 'Point')
            coords_elem = ET.SubElement(point_elem, 'coordinates')
            coords_elem.text = f"\n            {waypoint['lng']},{waypoint['lat']}\n          "
        
        # Update index
        index_elem = new_placemark.find('./wpml:index', ns)
        if index_elem is not None:
            index_elem.text = str(idx)
        
        # Update height if provided and element exists
        height_elem = new_placemark.find('./wpml:height', ns)
        height = waypoint.get('height', global_height)
        if height_elem is not None:
            height_elem.text = str(height)
        else:
            # Create height element if it doesn't exist
            height_elem = ET.SubElement(new_placemark, 'wpml:height')
            height_elem.text = str(height)
        
        # Update ellipsoid height if exists
        ellipsoid_elem = new_placemark.find('./wpml:ellipsoidHeight', ns)
        if ellipsoid_elem is not None:
            ellipsoid_elem.text = str(waypoint.get('elevation', 0) + float(height))
        
        # Handle actions if present
        actions = waypoint.get('actions', [])
        if actions and len(actions) > 0:
            # Check if there's an existing action group we can modify
            action_group = new_placemark.find('./wpml:actionGroup', ns)
            
            # If no action group exists, create one
            if action_group is None:
                action_group = ET.SubElement(new_placemark, 'wpml:actionGroup')
                ET.SubElement(action_group, 'wpml:actionGroupId').text = '0'
                ET.SubElement(action_group, 'wpml:actionGroupStartIndex').text = '0'
                ET.SubElement(action_group, 'wpml:actionGroupEndIndex').text = str(len(actions) - 1)
                ET.SubElement(action_group, 'wpml:actionGroupMode').text = 'sequence'
                
                # Add action trigger
                action_trigger = ET.SubElement(action_group, 'wpml:actionTrigger')
                ET.SubElement(action_trigger, 'wpml:actionTriggerType').text = 'reachPoint'
            else:
                # Find and remove all existing actions
                existing_actions = []
                
                # Try with namespace
                ns_actions = action_group.findall('./wpml:action', ns)
                if ns_actions:
                    existing_actions.extend(ns_actions)
                
                # Try without namespace
                non_ns_actions = action_group.findall('./action')
                if non_ns_actions:
                    existing_actions.extend([a for a in non_ns_actions if a not in existing_actions])
                
                # Try direct children
                for child in action_group:
                    if child.tag.endswith('action') and child not in existing_actions:
                        existing_actions.append(child)
                
                # Remove all existing actions
                for action in existing_actions:
                    action_group.remove(action)
                
                # Update action count
                end_index = action_group.find('./wpml:actionGroupEndIndex', ns)
                if end_index is not None:
                    end_index.text = str(len(actions) - 1)
                else:
                    # Create end index element if it doesn't exist
                    end_index = ET.SubElement(action_group, 'wpml:actionGroupEndIndex')
                    end_index.text = str(len(actions) - 1)
            
            # Add each action to the action group
            for i, action_data in enumerate(actions):
                action_elem = create_action_element(action_data, i)
                action_group.append(action_elem)
        
        # Add the new placemark
        folder.append(new_placemark)
    
    # Convert back to string with proper XML declaration
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
    
    # Some versions of ElementTree omit the XML declaration, so add it if needed
    if not xml_content.startswith('<?xml'):
        return xml_declaration + xml_content
    return xml_content


def create_action_element(action_data, action_id=0):
    """
    Create an XML Element for a DJI action
    
    Parameters:
    -----------
    action_data : dict
        Dictionary containing action data
    action_id : int
        ID for this action
        
    Returns:
    --------
    xml.etree.ElementTree.Element
        XML element for the action
    """
    action = ET.Element('wpml:action')
    
    # Set action ID
    action_id_elem = ET.SubElement(action, 'wpml:actionId')
    action_id_elem.text = str(action_data.get('id', action_id))
    
    # Set actuator function
    actuator_func = ET.SubElement(action, 'wpml:actionActuatorFunc')
    actuator_func.text = action_data['type']
    
    # Set actuator function parameters
    actuator_params = ET.SubElement(action, 'wpml:actionActuatorFuncParam')
    
    # Add parameters based on action type
    params = action_data.get('params', {})
    
    for key, value in params.items():
        param_elem = ET.SubElement(actuator_params, f'wpml:{key}')
        param_elem.text = str(value)
    
    return action


# Action helper functions
def create_rotate_yaw_action(heading, path_mode="counterClockwise"):
    """Create a rotate yaw action"""
    return {
        'type': 'rotateYaw',
        'params': {
            'aircraftHeading': heading,
            'aircraftPathMode': path_mode
        }
    }


def create_gimbal_rotate_action(pitch_angle=None, roll_angle=None, yaw_angle=None,
                               yaw_base="north", rotate_mode="absoluteAngle",
                               payload_index=0):
    """Create a gimbal rotate action"""
    params = {
        'gimbalHeadingYawBase': yaw_base,
        'gimbalRotateMode': rotate_mode,
        'payloadPositionIndex': payload_index,
        'gimbalRotateTimeEnable': 0,
        'gimbalRotateTime': 0
    }
    
    # Add pitch parameters
    params['gimbalPitchRotateEnable'] = 1 if pitch_angle is not None else 0
    if pitch_angle is not None:
        params['gimbalPitchRotateAngle'] = pitch_angle
    
    # Add roll parameters
    params['gimbalRollRotateEnable'] = 1 if roll_angle is not None else 0
    if roll_angle is not None:
        params['gimbalRollRotateAngle'] = roll_angle
    
    # Add yaw parameters
    params['gimbalYawRotateEnable'] = 1 if yaw_angle is not None else 0
    if yaw_angle is not None:
        params['gimbalYawRotateAngle'] = yaw_angle
    
    return {
        'type': 'gimbalRotate',
        'params': params
    }


def create_zoom_action(focal_length, use_focal_factor=False, payload_index=0):
    """Create a zoom action"""
    return {
        'type': 'zoom',
        'params': {
            'focalLength': focal_length,
            'isUseFocalFactor': 1 if use_focal_factor else 0,
            'payloadPositionIndex': payload_index
        }
    }


def create_take_photo_action(payload_index=0, use_global_payload_lens_index=True):
    """Create a take photo action"""
    return {
        'type': 'takePhoto',
        'params': {
            'payloadPositionIndex': payload_index,
            'useGlobalPayloadLensIndex': 1 if use_global_payload_lens_index else 0
        }
    }


def create_start_record_action(payload_index=0):
    """Create a start record action"""
    return {
        'type': 'startRecord',
        'params': {
            'payloadPositionIndex': payload_index
        }
    }


def create_stop_record_action(payload_index=0):
    """Create a stop record action"""
    return {
        'type': 'stopRecord',
        'params': {
            'payloadPositionIndex': payload_index
        }
    }


def create_hover_action(hover_time):
    """Create a hover action"""
    return {
        'type': 'hover',
        'params': {
            'hoverTime': hover_time
        }
    }


def save_kml(kml_data, output_file_path):
    """Save KML data to a file"""
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(kml_data)
    print(f"KML file saved to {output_file_path}")


def edit_kmz_placemarks(input_kmz_path, output_kmz_path, waypoints, author_name="Binh Pham"):
    """
    Edit Placemarks in a KMZ file, preserving all other elements and files
    
    Parameters:
    -----------
    input_kmz_path : str
        Path to the input KMZ file
    output_kmz_path : str
        Path where to save the output KMZ file
    waypoints : list of dict
        List of waypoint dictionaries
    author_name : str
        Name of the author to set in the KML file
    """
    # Extract KML from KMZ
    with ZipFile(input_kmz_path, "r") as kmz:
        # Find the KML file in the archive
        kml_filename = [f for f in kmz.namelist() if f.endswith('.kml')][0]
        kml_string = kmz.read(kml_filename).decode("utf-8")
        
        # Edit only the Placemarks in the KML
        updated_kml = edit_dji_kml_placemarks(kml_string, waypoints, author_name)
        
        # Create a new KMZ with the updated KML
        with ZipFile(output_kmz_path, "w") as new_kmz:
            # Add the updated KML file
            new_kmz.writestr(kml_filename, updated_kml)
            
            # Copy all other files from the original KMZ
            for file in kmz.namelist():
                if file != kml_filename:
                    new_kmz.writestr(file, kmz.read(file))
    
    print(f"KMZ file saved to {output_kmz_path}")