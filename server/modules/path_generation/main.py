from .utils import *

def generate_kmz(image_path, label_path, output_path):
    # Load images and lables
    print("Loading images and labels...")
    image_bbox_list = []
    for file in os.listdir(label_path):
        if file.endswith('.txt'):
            img_name = file.replace('.txt', '.jpeg')
            with open(os.path.join(label_path, file), 'r') as f:
                bboxes = []
                for line in f:
                    class_id, x, y, w_, h_ = map(float, line.strip().split())
                    bboxes.append({"class_id": int(class_id), "x_center": x, "y_center": y, "width": w_, "height": h_})
            image_bbox_list.append((img_name, bboxes))

    # # Extracting SIFT Features
    # print("Extracting SIFT features...")
    # pycolmap.set_random_seed(0)
    # pycolmap.extract_features(DATABASE_PATH, image_path)

    # # Match Sift Features
    # print("Matching SIFT features...")
    # pycolmap.match_exhaustive(DATABASE_PATH)

    # # Incremental Mapping for Sparse Reconstruction
    # print("Incremental Mapping for Sparse Reconstruction...")
    # reconstruction = incremental_mapping_with_pbar(DATABASE_PATH, image_path, RECONSTRUCTION_PATH)[0]

    # If you already have a reconstruction, you can load it
    reconstruction = pycolmap.Reconstruction(os.path.join(RECONSTRUCTION_PATH, "0"))

    # Triangulate candidate points
    print("Triangulating candidate points...")
    points_2d = [] # Storing 2D center of bounding boxes
    intrinsics = [] # Storing camera intrinsics
    extrinsics = [] # Storing camera extrinsics
    image_id_list = [] # Storing image ids for each point

    for (filename, bboxes) in image_bbox_list:
        image = reconstruction.find_image_with_name(filename)
        camera = reconstruction.cameras[image.camera_id]

        K = camera.calibration_matrix()
        ext = image.cam_from_world.matrix()

        img_points = []
        for bbox in bboxes:
            x = bbox['x_center'] * camera.width
            y = bbox['y_center'] * camera.height
            img_points.append((x, y))

        points_2d.append(img_points)
        intrinsics.append(K)
        extrinsics.append(ext)
        
        image_id_list.append([image.image_id] * len(img_points))  # One image_id per point

    # Flatten image_id_list
    image_id_list = [id for sublist in image_id_list for id in sublist]

    # Triangulate lines
    print("Triangulating lines...")
    class_to_lines = {}

    for (filename, bboxes) in image_bbox_list:
        image = reconstruction.find_image_with_name(filename)
        ext = image.cam_from_world.matrix()
        R, t = ext[:3, :3], ext[:3, 3]
        C = -R.T @ t
        camera = reconstruction.cameras[image.camera_id]
        K = camera.calibration_matrix()

        for bbox in bboxes:
            class_id = bbox['class_id']
            x = bbox['x_center'] * camera.width
            y = bbox['y_center'] * camera.height
            p_h = np.array([x, y, 1.0])
            ray_cam = np.linalg.inv(K) @ p_h
            ray_world = R.T @ ray_cam
            ray_world /= np.linalg.norm(ray_world)

            class_to_lines.setdefault(class_id, []).append((C, ray_world))

    # Solve 3D point for each class
    class_to_3d = {cls: fit_point_to_rays(lines) for cls, lines in class_to_lines.items()}

    best_points = np.array([point.reshape(3, 1) for point in class_to_3d.values()])

    # _______ Plane Fitting _______
    # Fit general plane ax + by + cz + d = 0
    A = np.hstack([best_points.reshape(-1, 3), np.ones((len(best_points), 1))])
    _, _, V = np.linalg.svd(A)
    plane = V[-1, :]  # [a, b, c, d]
    plane /= np.linalg.norm(plane[:3])

    # _______ Plane Projection
    # Project points onto the plane
    best_points_proj = []
    normal = plane[:3]
    d = plane[3]

    for pt in best_points.reshape(-1, 3):
        dist = (np.dot(normal, pt) + d) / np.linalg.norm(normal)
        pt_proj = pt - dist * (normal / np.linalg.norm(normal))
        best_points_proj.append(pt_proj)

    best_points_proj = np.array(best_points_proj).reshape(-1, 3, 1)

    # _______ Shift camera points
    # Plane normal
    plane_normal = plane[:3]
    plane_normal /= np.linalg.norm(plane_normal)

    # Shift points
    best_points_shifted = best_points_proj + 0.5 * (plane_normal.reshape(3, 1))

    # Calculate projection centers of camera and ECEF coordinates
    print("Calculating projection centers and ECEF coordinates...")
    proj_centers = []
    ecef_coords = []

    for image in reconstruction.images.values():
        if not reconstruction.is_image_registered(image.image_id):
            continue
        try:
            lat, lon, alt = get_image_gps_from_file(image, image_path)
        except:
            continue
        proj_centers.append(image.projection_center())
        ecef_coords.append(transform_gps_to_ecef(lat, lon, alt))

    proj_centers = np.array(proj_centers)
    ecef_coords = np.array(ecef_coords)
    print(f"Projection Centers: {proj_centers.shape}, ECEF Coordinates: {ecef_coords.shape}")

    # Calculate simularity transformation
    scale, R, t = estimate_similarity_transform(proj_centers, ecef_coords)
    print(f"Simularity Matrix: Scale: {scale}, Rotation:\n{R}, Translation:\n{t}")
    
    # Convert to Waypoint format
    print("Saving to KMZ...")
    input_waypoints = []

    for pt in best_points_shifted:
        lat, lon, alt = transform_proj_to_gps(pt, scale, R, t)
        input_waypoints.append({'lat': lat, 'lng': lon, 'alt': alt})
    
    waypoints_to_kmz(input_waypoints, output_path)
    print(f"KMZ file saved to {output_path}")