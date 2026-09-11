from pathlib import Path

import cv2
import numpy as np

from pypdf import PdfReader


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


def calculate_image_brightness(image) -> float:
    """
    Calculate the average brightness of an image.

    Returns:
        Brightness value between 0 and 255.
    """

    if image is None:
        return 0.0

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    return float(np.mean(grayscale))


def calculate_image_contrast(image) -> float:
    """
    Calculate image contrast using grayscale standard deviation.

    Higher values generally indicate stronger contrast.
    """

    if image is None:
        return 0.0

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    return float(np.std(grayscale))


def calculate_image_blur(image) -> float:
    """
    Estimate image sharpness using variance of Laplacian.

    Higher values generally indicate a sharper image.
    """

    if image is None:
        return 0.0

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    return float(
        cv2.Laplacian(
            grayscale,
            cv2.CV_64F,
        ).var()
    )


def calculate_non_blank_ratio(image) -> float:
    """
    Estimate how much meaningful visual content exists
    in an image.

    Returns:
        Value between 0 and 1.
    """

    if image is None:
        return 0.0

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    _, threshold = cv2.threshold(
        grayscale,
        245,
        255,
        cv2.THRESH_BINARY_INV,
    )

    non_blank_pixels = np.count_nonzero(
        threshold
    )

    total_pixels = threshold.size

    if total_pixels == 0:
        return 0.0

    return float(
        non_blank_pixels / total_pixels
    )


def is_image_blank(image) -> bool:
    """
    Determine whether an image is effectively blank.

    A document is considered blank when almost no
    meaningful visual content is detected.
    """

    non_blank_ratio = calculate_non_blank_ratio(
        image
    )

    return non_blank_ratio < 0.001


def analyze_image_quality(
    file_path: str,
) -> dict:
    """
    Analyze an image without rejecting it merely
    because its visual quality is poor.

    Important product rule:

    Poor quality != invalid document.

    Only a completely blank image should normally
    stop processing.
    """

    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": "File does not exist",
        }

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "UNSUPPORTED",
            "reason": (
                "Image quality analysis is currently "
                "supported for JPG, JPEG, and PNG"
            ),
        }

    image = cv2.imread(
        str(path)
    )

    if image is None:
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": "Unable to read image",
        }

    height, width = image.shape[:2]

    if height == 0 or width == 0:
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": "Image has invalid dimensions",
        }

    brightness = calculate_image_brightness(
        image
    )

    contrast = calculate_image_contrast(
        image
    )

    blur_score = calculate_image_blur(
        image
    )

    non_blank_ratio = calculate_non_blank_ratio(
        image
    )

    blank = is_image_blank(
        image
    )

    if blank:
        return {
            "success": True,
            "is_blank": True,
            "quality_score": 0,
            "quality_status": "BLANK",
            "reason": (
                "Document appears to be completely blank"
            ),
            "width": width,
            "height": height,
            "brightness": round(
                brightness,
                2,
            ),
            "contrast": round(
                contrast,
                2,
            ),
            "blur_score": round(
                blur_score,
                2,
            ),
            "non_blank_ratio": round(
                non_blank_ratio,
                6,
            ),
        }

    quality_score = 100

    if brightness < 40:
        quality_score -= 20
    elif brightness < 70:
        quality_score -= 10
    elif brightness > 235:
        quality_score -= 10

    if contrast < 15:
        quality_score -= 20
    elif contrast < 25:
        quality_score -= 10

    if blur_score < 30:
        quality_score -= 30
    elif blur_score < 80:
        quality_score -= 15

    if width < 500 or height < 500:
        quality_score -= 10

    quality_score = max(
        0,
        min(
            100,
            quality_score,
        ),
    )

    if quality_score >= 80:
        quality_status = "GOOD"
    elif quality_score >= 60:
        quality_status = "FAIR"
    else:
        quality_status = "LOW"

    return {
        "success": True,
        "is_blank": False,
        "quality_score": quality_score,
        "quality_status": quality_status,
        "reason": (
            "Document contains visual content and "
            "can proceed to OCR"
        ),
        "width": width,
        "height": height,
        "brightness": round(
            brightness,
            2,
        ),
        "contrast": round(
            contrast,
            2,
        ),
        "blur_score": round(
            blur_score,
            2,
        ),
        "non_blank_ratio": round(
            non_blank_ratio,
            6,
        ),
    }


def analyze_pdf_quality(
    file_path: str,
) -> dict:
    """
    Perform basic validation for PDF documents.

    Detailed PDF page rendering and page-level quality
    analysis will be implemented in the PDF preprocessing
    engine.
    """

    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": "File does not exist",
        }

    try:
        reader = PdfReader(
            str(path)
        )

        page_count = len(
            reader.pages
        )

        if page_count == 0:
            return {
                "success": True,
                "is_blank": True,
                "quality_score": 0,
                "quality_status": "BLANK",
                "reason": (
                    "PDF contains no pages"
                ),
                "page_count": 0,
            }

        return {
            "success": True,
            "is_blank": False,
            "quality_score": 100,
            "quality_status": "GOOD",
            "reason": (
                "PDF is structurally readable "
                "and contains pages"
            ),
            "page_count": page_count,
        }

    except Exception as error:
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": (
                f"Unable to read PDF: {error}"
            ),
        }


def check_document_quality(
    file_path: str,
) -> dict:
    """
    Main document quality entry point.

    Important:

    This function does NOT reject documents merely
    because they are blurry, dark, tilted, rotated,
    or otherwise low quality.

    Documents containing any meaningful content should
    continue to OCR.
    """

    path = Path(
        file_path
    )

    if not path.exists():
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "INVALID",
            "reason": "File does not exist",
        }

    extension = path.suffix.lower()

    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        return analyze_image_quality(
            str(path)
        )

    if extension == ".pdf":
        return analyze_pdf_quality(
            str(path)
        )

    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        return {
            "success": False,
            "is_blank": False,
            "quality_score": 0,
            "quality_status": "UNSUPPORTED",
            "reason": "Unsupported document type",
        }

    return {
        "success": False,
        "is_blank": False,
        "quality_score": 0,
        "quality_status": "INVALID",
        "reason": "Unable to analyze document",
    }