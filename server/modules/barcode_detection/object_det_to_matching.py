from ultralytics import RTDETR
import cv2
import torch
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict
import os
import shutil
import sys

# Dummy feature extractor using a simple CNN backbone (replace with ResNet if needed)
import torchvision.models as models
import torchvision.transforms as transforms

# Add the current directory to the system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define all constants here
MODEL_CKPT = './object_detection_model.pt'

def drone_object_detection(IMAGE_DIR, OUTPUT_DIR):
    # --- Set up feature extractor ---
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    feature_extractor_model = models.resnet18(pretrained=True)
    feature_extractor_model = torch.nn.Sequential(*list(feature_extractor_model.children())[:-1])  # Remove final layer
    feature_extractor_model.eval()
    feature_extractor_model.to(device)

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    # --- Set up RTDETR model ---
    def run_object_detection(image_path):
        # Load the model
        model = RTDETR(MODEL_CKPT)
        
        # Move the model to GPU if available
        model.to('cuda:0')
        
        # Predict on the unlabeled images
        detections = model.predict(source=image_path, 
                    save=False, 
                    save_txt=False, 
                    show_labels=False,
                    save_crop=False,
                    project='/home/akshay/makeathon/dataset/unlabeled_images', 
                    name='predictions_rtdetrl_matching', 
                    conf=0.25)  # Predict on the unlabeled images
        
        return detections


    # --- Set up matching function ---
    def crop_from_image(image, bbox):
        # Crop the bounding box from the image
        x1, y1, x2, y2 = map(int, bbox)
        return image[y1:y2, x1:x2]

    def extract_feature(crop):
        # Extract a feature vector from the crop
        input_tensor = transform(crop).unsqueeze(0).to(device)
        with torch.no_grad():
            feature = feature_extractor_model(input_tensor)
        feature = feature.view(-1).cpu().numpy()
        return feature

    def compute_cost_matrix(features1, features2):
        # Compute the cost matrix (euclidean distance between features)
        cost_matrix = np.zeros((len(features1), len(features2)))
        for i, f1 in enumerate(features1):
            for j, f2 in enumerate(features2):
                cost_matrix[i, j] = np.linalg.norm(f1 - f2)
        return cost_matrix


    # --- Main process ---

    image_paths = [os.path.join(IMAGE_DIR, img) for img in os.listdir(IMAGE_DIR) if img.lower().endswith(('.jpeg', '.jpg', '.png'))]

    # Store features and bounding boxes
    all_features = []
    all_bboxes = []

    # Track object IDs and which bbox belongs to which object
    bbox_to_object_id = dict()
    object_id_counter = 0

    # Final output: object_id -> list of (image_idx, bbox coordinates)
    object_tracks = defaultdict(list)

    # --- Start extracting features and running object detection ---
    for image_path in image_paths:
        # Read the image
        image = cv2.imread(image_path)
        
        # Run object detection
        detections = run_object_detection(image_path)

        features = []
        bboxes = []
        if detections is not None:
            target_class_id = 1  # example: assuming 'Label' class is class ID 1

            for det in detections:
                detected_classes = det.boxes.cls.cpu().numpy()
                for i, class_id in enumerate(detected_classes):

                    if class_id == target_class_id:
                        bbox = det.boxes.xyxy[i].cpu().numpy()
                        crop = crop_from_image(image, bbox)
                        feature_vector = extract_feature(crop)                
                
                        features.append(feature_vector)
                        bboxes.append(bbox)

        all_features.append(features)
        all_bboxes.append(bboxes)

    # Step 1: Find the image with the most bounding boxes
    num_images = len(all_features)
    if num_images == 0:
        raise ValueError("No images found in the specified directory.")
    image_with_max_bboxes = max(range(num_images), key=lambda i: len(all_bboxes[i]))

    # Step 2: Reorder the list of images so that the image with the most bounding boxes comes first
    all_bboxes = [all_bboxes[image_with_max_bboxes]] + [all_bboxes[i] for i in range(num_images) if i != image_with_max_bboxes]
    all_features = [all_features[image_with_max_bboxes]] + [all_features[i] for i in range(num_images) if i != image_with_max_bboxes]
    all_images = [image_paths[image_with_max_bboxes]] + [image_paths[i] for i in range(len(image_paths)) if i != image_with_max_bboxes]


    # Step 3: Assign initial object IDs to bboxes from first image
    for idx, bbox in enumerate(all_bboxes[0]):
        bbox_to_object_id[(0, idx)] = object_id_counter
        object_tracks[object_id_counter].append((0, bbox))
        object_id_counter += 1

    # Step 4: Iterate through the rest of the images and match bboxes
    # Now match each image with all future images
    for i in range(num_images):
        # if i != image_with_max_bboxes:  # Skip initial assignment for the image with max bbox count
            
            for j in range(i + 1, num_images):
                print(f"\nMatching Image {i} with Image {j}")

                features_image1 = all_features[i]
                features_image2 = all_features[j]

                cost_matrix = compute_cost_matrix(features_image1, features_image2)
                row_ind, col_ind = linear_sum_assignment(cost_matrix)

                for idx1, idx2 in zip(row_ind, col_ind):
                    key_i = (i, idx1)
                    key_j = (j, idx2)

                    # If bbox from image i is already assigned an object ID
                    if key_i in bbox_to_object_id:
                        object_id = bbox_to_object_id[key_i]
                    else:
                        # New object
                        object_id = object_id_counter
                        object_id_counter += 1
                        bbox_to_object_id[key_i] = object_id
                        object_tracks[object_id].append((i, all_bboxes[i][idx1]))

                    # # Assign the same object ID to the matched bbox in image j
                    if key_j not in bbox_to_object_id:
                        bbox_to_object_id[key_j] = object_id
                        object_tracks[object_id].append((j, all_bboxes[j][idx2]))

    # --- Save the results ---
    def save_yolo_format(image, object_tracks, output_dir, all_bboxes):
        """
        Save object detection results in YOLO format (both image and label files).
        
        Arguments:
        - image: The image file path.
        - object_tracks: A dictionary of object tracks with object IDs.
        - output_dir: Directory to save the images and labels.
        - all_bboxes: List of bounding boxes for each image, corresponding to the reordered images.
        """
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the image name without extension
        image_name = os.path.splitext(os.path.basename(image))[0]
        
        # Load the image to get its dimensions
        img = cv2.imread(image)  # OpenCV can be used to load images
        height, width, _ = img.shape
        
        # Get the index of the image from the reordered list
        image_idx = all_images.index(image)

        # Open the label file for this image
        label_file_path = os.path.join(output_dir, f"{image_name}.txt")
        with open(label_file_path, 'w') as label_file:
            
            # Loop over each object ID and its bounding boxes across all images
            for object_id, track in object_tracks.items():
                for img_idx, bbox in track:
                    # Only save bounding boxes that correspond to this image
                    if img_idx == image_idx:
                        # Convert bbox coordinates from (x_min, y_min, x_max, y_max) to YOLO format
                        x_min, y_min, x_max, y_max = bbox
                        
                        # Normalize the bounding box coordinates
                        x_center = (x_min + x_max) / 2 / width
                        y_center = (y_min + y_max) / 2 / height
                        w = (x_max - x_min) / width
                        h = (y_max - y_min) / height
                        
                        
                        # Write the bounding box to the label file in YOLO format
                        label_file.write(f"{object_id} {x_center} {y_center} {w} {h}\n")
        
        # Copy the image to the output directory
        image_output_path = os.path.join(output_dir, f"{image_name}.jpg")
        shutil.copy(image, image_output_path)

    for image in all_images:
        save_yolo_format(image, object_tracks, OUTPUT_DIR, all_bboxes)