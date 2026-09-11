from pathlib import Path

import cv2

from backend.services.document_orientation import (
    detect_document_orientation,
)

PROCESSED_DIR = Path(
    "data/processed"
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def rotate_image(
    image,
    rotation_angle: int,
):
    """
    Rotate an image by 0, 90, 180, or 270 degrees.
    """

    if rotation_angle == 0:
        return image

    if rotation_angle == 90:
        return cv2.rotate(
            image,
            cv2.ROTATE_90_CLOCKWISE,
        )

    if rotation_angle == 180:
        return cv2.rotate(
            image,
            cv2.ROTATE_180,
        )

    if rotation_angle == 270:
        return cv2.rotate(
            image,
            cv2.ROTATE_90_COUNTERCLOCKWISE,
        )

    raise ValueError(
        "Rotation angle must be 0, 90, 180, or 270"
    )


def deskew_image(
    image,
):
    """
    Correct small document tilt/skew.

    Large rotations such as 90, 180, or 270 degrees
    should be handled by the orientation detector.
    """

    if image is None:
        return None

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    threshold = cv2.threshold(
        grayscale,
        0,
        255,
        cv2.THRESH_BINARY_INV
        + cv2.THRESH_OTSU,
    )[1]

    coordinates = cv2.findNonZero(
        threshold
    )

    if coordinates is None:
        return image

    rect = cv2.minAreaRect(
        coordinates
    )

    angle = rect[-1]

    if angle < -45:
        angle = 90 + angle

    # Ignore tiny/noisy angles.
    if abs(angle) < 0.5:
        return image

    # Ignore very large angles.
    # Those are orientation problems rather than deskew problems.
    if abs(angle) > 15:
        return image

    height, width = image.shape[:2]

    center = (
        width // 2,
        height // 2,
    )

    rotation_matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0,
    )

    corrected = cv2.warpAffine(
        image,
        rotation_matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    return corrected


def enhance_image_for_ocr(
    image,
):
    """
    Create an OCR-friendly version of the image.

    The original uploaded document is never modified.
    """

    if image is None:
        return None

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # Improve local contrast without aggressively changing
    # the original document.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(
        grayscale
    )

    return enhanced


def preprocess_image(
    file_path: str,
    rotation_angle: int = 0,
):
    """
    Complete image preprocessing.

    Pipeline:

    1. Read original image.
    2. Rotate image.
    3. Deskew image.
    4. Enhance image for OCR.
    5. Save processed copy.
    6. Keep original file untouched.
    """

    path = Path(
        file_path
    )

    if not path.exists():
        return {
            "success": False,
            "processed_path": None,
            "rotation_angle": rotation_angle,
            "reason": "File does not exist",
        }

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return {
            "success": False,
            "processed_path": None,
            "rotation_angle": rotation_angle,
            "reason": (
                "Image preprocessing is not supported "
                "for this file type"
            ),
        }

    image = cv2.imread(
        str(path)
    )

    if image is None:
        return {
            "success": False,
            "processed_path": None,
            "rotation_angle": rotation_angle,
            "reason": "Unable to read image",
        }

    rotated_image = rotate_image(
        image,
        rotation_angle,
    )

    deskewed_image = deskew_image(
        rotated_image
    )

    enhanced_image = enhance_image_for_ocr(
        deskewed_image
    )

    processed_filename = (
        f"{path.stem}_processed.png"
    )

    processed_path = (
        PROCESSED_DIR
        / processed_filename
    )

    saved = cv2.imwrite(
        str(processed_path),
        enhanced_image,
    )

    if not saved:
        return {
            "success": False,
            "processed_path": None,
            "rotation_angle": rotation_angle,
            "reason": (
                "Failed to save processed image"
            ),
        }

    return {
        "success": True,
        "processed_path": str(
            processed_path
        ),
        "rotation_angle": rotation_angle,
        "reason": (
            "Image preprocessing completed successfully"
        ),
    }

def preprocess_document(
    file_path: str,
):
    """
    Automatically preprocess a document for OCR.

    Pipeline:

    1. Validate the original file.
    2. Detect document orientation.
    3. Calculate the required rotation.
    4. Rotate the document automatically.
    5. Deskew the document.
    6. Enhance the document for OCR.
    7. Save a processed copy.
    8. Keep the original document untouched.
    """

    path = Path(
        file_path
    )

    if not path.exists():
        return {
            "success": False,
            "original_path": str(path),
            "processed_path": None,
            "detected_orientation": None,
            "rotation_angle": 0,
            "orientation_confidence": 0,
            "reason": "File does not exist",
        }

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return {
            "success": False,
            "original_path": str(path),
            "processed_path": None,
            "detected_orientation": None,
            "rotation_angle": 0,
            "orientation_confidence": 0,
            "reason": (
                "Automatic image preprocessing is currently "
                "supported for JPG, JPEG, and PNG files"
            ),
        }

    orientation_result = (
        detect_document_orientation(
            str(path)
        )
    )

    if not orientation_result["success"]:
        return {
            "success": False,
            "original_path": str(path),
            "processed_path": None,
            "detected_orientation": None,
            "rotation_angle": 0,
            "orientation_confidence": 0,
            "reason": (
                "Document orientation detection failed: "
                + orientation_result["reason"]
            ),
        }

    rotation_angle = orientation_result[
        "rotation_angle"
    ]

    preprocessing_result = preprocess_image(
        file_path=str(path),
        rotation_angle=rotation_angle,
    )

    if not preprocessing_result["success"]:
        return {
            "success": False,
            "original_path": str(path),
            "processed_path": None,
            "detected_orientation": (
                orientation_result.get(
                    "detected_orientation"
                )
            ),
            "rotation_angle": rotation_angle,
            "orientation_confidence": (
                orientation_result.get(
                    "confidence",
                    0,
                )
            ),
            "reason": (
                "Document preprocessing failed: "
                + preprocessing_result["reason"]
            ),
        }

    return {
        "success": True,
        "original_path": str(path),
        "processed_path": (
            preprocessing_result[
                "processed_path"
            ]
        ),
        "detected_orientation": (
            orientation_result.get(
                "detected_orientation"
            )
        ),
        "rotation_angle": rotation_angle,
        "orientation_confidence": (
            orientation_result.get(
                "confidence",
                0,
            )
        ),
        "reason": (
            "Document orientation correction, "
            "deskew, and OCR enhancement completed "
            "successfully"
        ),
    }