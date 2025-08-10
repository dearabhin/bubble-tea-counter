import cv2
import numpy as np
import os
from datetime import datetime

# --- HELPER: This function replaces Matplotlib for creating the steps image ---


def create_steps_visualization(images, labels):
    """Creates a single grid image from multiple images using only OpenCV."""
    # Ensure all images are 3-channel BGR for stacking
    processed_images = []
    for img in images:
        if len(img.shape) == 2:  # Check if it's grayscale
            processed_images.append(cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
        else:
            processed_images.append(img)

    # Add text labels to each image
    for i, img in enumerate(processed_images):
        cv2.putText(img, labels[i], (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Arrange images into a 2x2 grid
    if len(processed_images) == 4:
        top_row = np.hstack((processed_images[0], processed_images[1]))
        bottom_row = np.hstack((processed_images[2], processed_images[3]))
        grid = np.vstack((top_row, bottom_row))
    else:  # Fallback for a different number of images
        grid = np.hstack(processed_images)

    return grid

# --- The rest of your functions, now optimized ---


def create_tea_mask(image):
    _, binary = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        # Instead of crashing, let's return an empty mask
        return np.zeros_like(image)
    main_contour = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(image)
    cv2.drawContours(mask, [main_contour], -1, (255), -1)
    return mask


def enhance_image(image):
    denoised = cv2.bilateralFilter(image, 9, 75, 75)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    return enhanced


def detect_bubbles(binary, min_area=5, max_area=500):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_bubbles = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area < area < max_area:
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                if 0.3 < circularity < 1.2:
                    valid_bubbles.append(contour)
    return valid_bubbles


def count_bubbles(image_path):
    # --- OPTIMIZATION 1: RESIZE LARGE IMAGES ---
    MAX_WIDTH = 1024
    # Read with color first for final viz
    original_full = cv2.imread(image_path)
    if original_full is None:
        raise ValueError("Could not read image")

    h, w = original_full.shape[:2]
    if w > MAX_WIDTH:
        new_h = int((MAX_WIDTH / w) * h)
        original_full = cv2.resize(
            original_full, (MAX_WIDTH, new_h), interpolation=cv2.INTER_AREA)

    # Convert to grayscale for processing
    original = cv2.cvtColor(original_full, cv2.COLOR_BGR2GRAY)

    mask = create_tea_mask(original)
    masked_image = cv2.bitwise_and(original, mask)
    enhanced = enhance_image(masked_image)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
    binary = cv2.bitwise_and(binary, mask)
    valid_bubbles = detect_bubbles(binary)

    # Create the final detection image
    final_detection_image = original_full.copy()
    cv2.drawContours(final_detection_image, valid_bubbles, -1, (0, 255, 0), 2)

    # --- OPTIMIZATION 2: USE OPENCV INSTEAD OF MATPLOTLIB ---
    # Create the processing steps grid image
    steps_images = [masked_image, enhanced, binary, final_detection_image]
    steps_labels = ["1. Masked", "2. Enhanced",
                    "3. Binary", "4. Final Detection"]
    steps_grid = create_steps_visualization(steps_images, steps_labels)

    # Save the generated images
    output_dir = 'static/uploads'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    final_path = os.path.join(output_dir, f'final_detection_{timestamp}.jpg')
    # Save as JPG for smaller size
    steps_path = os.path.join(output_dir, f'processing_steps_{timestamp}.jpg')

    cv2.imwrite(final_path, final_detection_image)
    cv2.imwrite(steps_path, steps_grid)

    return len(valid_bubbles), steps_path, final_path
