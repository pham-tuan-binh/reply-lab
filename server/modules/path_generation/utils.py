import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pycolmap
from pathlib import Path
from tqdm import tqdm
import cv2
import open3d as o3d
import shutil
import piexif
import random
from .dji_exporter import waypoints_to_kmz

# Get Parent Directory
BASE_PATH = Path(__file__).resolve().parent

# Inputs
IMAGE_DI = "./notebooks/sfm/data/images"
LABEL_DI = "./notebooks/sfm/data/labels"

# Output
OUTPUT_DIR = BASE_PATH / "output"
FEATURE_DIR = OUTPUT_DIR / "features"
DATABASE_PATH = OUTPUT_DIR / "database.db"
RECONSTRUCTION_PATH = OUTPUT_DIR / "reconstruction"

# ______________________ File Handling Functions
def reset_output_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def get_image_gps_from_file(image, image_dir):
    image_path = Path(image_dir) / image.name
    exif = piexif.load(str(image_path))
    gps = exif.get("GPS", {})

    def dms_to_deg(dms, ref):
        deg = dms[0][0]/dms[0][1]
        min = dms[1][0]/dms[1][1]
        sec = dms[2][0]/dms[2][1]
        sign = -1 if ref in ['S', 'W'] else 1
        return sign * (deg + min/60 + sec/3600)

    lat = dms_to_deg(gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef].decode())
    lon = dms_to_deg(gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef].decode())
    alt = gps.get(piexif.GPSIFD.GPSAltitude, (0,1))
    alt = alt[0]/alt[1]

    return lat, lon, alt

# ______________________ Mapping Helper Functions
def incremental_mapping_with_pbar(database_path, image_path, sfm_path):
    num_images = pycolmap.Database(database_path).num_images
    
    # Create a progress bar placeholder
    pbar = tqdm(total=num_images, desc="Images registered:")
    pbar.update(0)
    
    # Define callback functions that update the progress bar
    def initial_pair_callback():
        pbar.update(2)
    
    def next_image_callback():
        pbar.update(1)
    
    try:
        reconstructions = pycolmap.incremental_mapping(
            database_path,
            image_path,
            sfm_path,
            initial_image_pair_callback=initial_pair_callback,
            next_image_callback=next_image_callback,
        )
    finally:
        # Ensure the progress bar is closed even if an exception occurs
        pbar.close()
    
    return reconstructions

# ______________________ Triangulation Helper Functions

# Find rays from image
def triangulate_lines(points_2d, intrinsics, extrinsics):
    lines = []
    for pts, K, ext in zip(points_2d, intrinsics, extrinsics):
        R, t = ext[:3, :3], ext[:3, 3]
        C = -R.T @ t
        for p in pts:
            p_h = np.array([p[0], p[1], 1.0])
            ray_cam = np.linalg.inv(K) @ p_h
            ray_world = R.T @ ray_cam
            ray_world /= np.linalg.norm(ray_world)
            lines.append((C, ray_world))
    return lines

def fit_point_to_rays(rays):
    A = []
    b = []
    for C, d in rays:
        d = d / np.linalg.norm(d)
        I = np.eye(3)
        A.append(I - np.outer(d, d))
        b.append((I - np.outer(d, d)) @ C)
    A = np.sum(A, axis=0)
    b = np.sum(b, axis=0)
    return np.linalg.lstsq(A, b, rcond=None)[0]  # least-squares point

def triangulate_candidates_lstsq(lines, num_samples=10000, rays_per_sample=5, threshold=0.1):
    candidates = []
    centers = [tuple(C) for C, _ in lines]
    for _ in range(num_samples):
        sample = []
        used_centers = set()
        while len(sample) < rays_per_sample:
            C, d = random.choice(lines)
            if tuple(C) in used_centers:
                continue
            used_centers.add(tuple(C))
            sample.append((C, d))
        point = fit_point_to_rays(sample)
        # optional: reject if too far from sample rays
        if all(np.linalg.norm(np.cross(d, point - C)) < threshold for C, d in sample):
            candidates.append(point)
    return np.array(candidates)

def find_all_points(lines, threshold, min_support=5, max_mean_distance=1.0):
    points = []
    
    for i, (C0, d0) in enumerate(lines):
        candidates = []
        for j, (C1, d1) in enumerate(lines):
            if i == j:
                continue
            n = np.cross(d0, d1)
            if np.linalg.norm(n) < 1e-6:
                continue
            n /= np.linalg.norm(n)
            A = np.stack([d0, -d1, n], axis=1)
            b = C1 - C0
            x = np.linalg.lstsq(A, b, rcond=None)[0]
            p = C0 + d0 * x[0]
            candidates.append((j, p))
        
        if not candidates:
            continue
        
        idxs, pts = zip(*candidates)
        pts = np.stack(pts)
        mean = np.mean(pts, axis=0)
        dists = np.linalg.norm(pts - mean, axis=1)
        support = np.array(idxs)[dists < threshold]

        if len(support) >= min_support:
            mean_distance = np.mean(dists[dists < threshold])
            if mean_distance <= max_mean_distance:
                points.append(mean)

    return points

# Similarity Helper Functions
def estimate_similarity_transform(source, target):
    src_mean = source.mean(axis=0)
    tgt_mean = target.mean(axis=0)

    src_centered = source - src_mean
    tgt_centered = target - tgt_mean

    H = src_centered.T @ tgt_centered
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T

    scale = np.sum(tgt_centered * (src_centered @ R)) / np.sum(src_centered**2)
    t = tgt_mean - scale * (R @ src_mean)

    return scale, R, t

def ransac_similarity(source, target, num_iter=1000, threshold=3.0):
    best_inliers = []
    best_model = None

    for _ in range(num_iter):
        idx = random.sample(range(len(source)), 3)
        src_sample = source[idx]
        tgt_sample = target[idx]

        try:
            scale, R, t = estimate_similarity_transform(src_sample, tgt_sample)
        except:
            continue

        transformed = scale * (source @ R.T) + t
        errors = np.linalg.norm(transformed - target, axis=1)
        inliers = np.where(errors < threshold)[0]

        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_model = (scale, R, t)

    if best_model is None:
        raise RuntimeError("RANSAC failed to find a valid model")
    
# ______________________ Space trasformation functions
# From GPS to ECEF
def transform_gps_to_ecef(lat, lon, alt):
    # Convert GPS coordinates to ECEF
    # WGS84 constants
    a = 6378137.0  # Semi-major axis
    e_sq = 6.69437999014e-3  # Square of eccentricity

    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    N = a / np.sqrt(1 - e_sq * np.sin(lat_rad)**2)

    x = (N + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1 - e_sq) + alt) * np.sin(lat_rad)
    return np.array([x, y, z])

# From world space to ECEF
def transform_proj_to_ecef(point, scale, R, t):
    point = np.asarray(point).reshape(3,)  # from (3,1) to (3,)
    return scale * (R @ point) + t

def transform_ecef_to_gps(x, y, z):
    a = 6378137.0
    e_sq = 6.69437999014e-3

    b = np.sqrt(a**2 * (1 - e_sq))
    ep = np.sqrt((a**2 - b**2) / b**2)
    p = np.sqrt(x**2 + y**2)
    th = np.arctan2(a * z, b * p)
    lon = np.arctan2(y, x)
    lat = np.arctan2(z + ep**2 * b * np.sin(th)**3, p - e_sq * a * np.cos(th)**3)
    N = a / np.sqrt(1 - e_sq * np.sin(lat)**2)
    alt = p / np.cos(lat) - N

    lat = np.degrees(lat)
    lon = np.degrees(lon)
    return lat, lon, alt

def transform_proj_to_gps(point, scale, R, t):
    ecef = transform_proj_to_ecef(point, scale, R, t)
    return transform_ecef_to_gps(*ecef)