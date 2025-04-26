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
        if height_elem is not None:
            height_elem.text = str(global_height)
        
        # Set ellipsoidHeight from waypoint['alt']
        ellipsoid_elem = new_placemark.find('./wpml:ellipsoidHeight', ns)
        if ellipsoid_elem is not None:
            ellipsoid_elem.text = str(waypoint['alt'])

        # Set ellipsoidHeight from waypoint['alt']
        execute_height_elem = new_placemark.find('./wpml:executeHeight', ns)
        if execute_height_elem is not None:
            execute_height_elem.text = str(waypoint['alt'])
        
        # Add the new placemark
        folder.append(new_placemark)
    
    # Convert back to string with proper XML declaration
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
    
    # Some versions of ElementTree omit the XML declaration, so add it if needed
    if not xml_content.startswith('<?xml'):
        return xml_declaration + xml_content
    return xml_content


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