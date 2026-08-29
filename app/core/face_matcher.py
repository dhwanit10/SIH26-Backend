import cv2
import numpy as np
import os
import tempfile
from insightface.app import FaceAnalysis
from typing import Tuple, Optional

# Initialize InsightFace model (auto-downloads on first run)
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=-1, det_size=(640, 640))  # ctx_id=-1 for CPU, 0 for GPU

# Face matching threshold (tune based on your validation)
FACE_MATCH_THRESHOLD = 0.4


def extract_person_photo_from_bytes(image_bytes: bytes, output_path: Optional[str] = None) -> dict:
    """
    Extract face from image bytes and save cropped face.
    
    Args:
        image_bytes: Image data as bytes
        output_path: Optional output path for cropped face. If None, uses temp file.
    
    Returns:
        dict: {
            "success": bool,
            "output": str (path to cropped image),
            "face_box": [x, y, w, h],
            "reason": str (if failed)
        }
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        return {
            "success": False,
            "reason": "Could not decode image from bytes"
        }
    
    # Use InsightFace for better face detection
    faces = app.get(image)
    
    if not faces:
        return {
            "success": False,
            "reason": "No face detected"
        }
    
    # Select face with highest confidence
    best_face = max(faces, key=lambda f: f.det_score)
    
    # Get face bounding box
    bbox = best_face.bbox.astype(int)
    x, y, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    w = x2 - x
    h = y2 - y
    
    # Expand around face for better context
    px = int(w * 0.5)
    py = int(h * 0.7)
    
    x1 = max(0, x - px)
    y1 = max(0, y - py)
    x2 = min(image.shape[1], x + w + px)
    y2 = min(image.shape[0], y + h + py)
    
    crop = image[y1:y2, x1:x2]
    
    # If no output path provided, use temporary file
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        output_path = temp_file.name
        temp_file.close()
    
    cv2.imwrite(output_path, crop)
    
    return {
        "success": True,
        "output": output_path,
        "face_box": [x, y, w, h]
    }


def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    """
    Extract face embedding from image bytes.
    
    Args:
        image_bytes: Image data as bytes
    
    Returns:
        np.ndarray: Normalized face embedding (512-d)
    
    Raises:
        ValueError: If no face detected
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image from bytes")
    
    faces = app.get(img)
    
    if not faces:
        raise ValueError("No face detected in image")
    
    # Pick face with highest detection confidence
    best = max(faces, key=lambda f: f.det_score)
    return best.normed_embedding  # Already L2-normalized (512-d)


def get_face_embedding_from_file(image_path: str) -> np.ndarray:
    """
    Extract face embedding from image file path.
    
    Args:
        image_path: Path to image file
    
    Returns:
        np.ndarray: Normalized face embedding (512-d)
    
    Raises:
        FileNotFoundError: If image cannot be read
        ValueError: If no face detected
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    
    faces = app.get(img)
    if not faces:
        raise ValueError(f"No face detected in {image_path}")
    
    # Pick face with highest detection confidence
    best = max(faces, key=lambda f: f.det_score)
    return best.normed_embedding


def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        emb1, emb2: Normalized face embeddings
    
    Returns:
        float: Cosine similarity score (0 to 1)
    """
    return float(np.dot(emb1, emb2))


def match_faces(image1_bytes: bytes, image2_bytes: bytes) -> Tuple[float, bool]:
    """
    Match two face images and return similarity score and match result.
    
    Args:
        image1_bytes: First image as bytes (person image)
        image2_bytes: Second image as bytes (document photo)
    
    Returns:
        Tuple[float, bool]: (similarity_score, is_match)
    
    Raises:
        ValueError: If no face detected in either image
    """
    try:
        emb1 = get_face_embedding(image1_bytes)
        emb2 = get_face_embedding(image2_bytes)
        
        similarity = cosine_similarity(emb1, emb2)
        is_match = similarity > FACE_MATCH_THRESHOLD
        
        return similarity, is_match
    except ValueError as e:
        raise ValueError(f"Face matching failed: {str(e)}")


def match_faces_with_cropping(person_image_bytes: bytes, doc_image_bytes: bytes) -> dict:
    """
    Match faces with automatic cropping and detailed result.
    
    Args:
        person_image_bytes: Person photo as bytes
        doc_image_bytes: Document photo as bytes
    
    Returns:
        dict: {
            "success": bool,
            "score": float,
            "match": bool,
            "person_face_path": str (path to cropped person face),
            "doc_face_path": str (path to cropped document face),
            "reason": str (if failed)
        }
    """
    try:
        # Extract faces from both images
        person_result = extract_person_photo_from_bytes(person_image_bytes)
        if not person_result["success"]:
            return {
                "success": False,
                "reason": f"Person image: {person_result['reason']}"
            }
        
        doc_result = extract_person_photo_from_bytes(doc_image_bytes)
        if not doc_result["success"]:
            return {
                "success": False,
                "reason": f"Document image: {doc_result['reason']}"
            }
        
        # Get embeddings from cropped faces
        emb1 = get_face_embedding_from_file(person_result["output"])
        emb2 = get_face_embedding_from_file(doc_result["output"])
        
        # Calculate similarity
        score = cosine_similarity(emb1, emb2)
        is_match = score > FACE_MATCH_THRESHOLD
        
        return {
            "success": True,
            "score": score,
            "match": is_match,
            "person_face_path": person_result["output"],
            "doc_face_path": doc_result["output"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "reason": f"Face matching error: {str(e)}"
        }