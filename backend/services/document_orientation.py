from pathlib import Path

import cv2
from paddleocr import PaddleOCR


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


orientation_engine = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
    use_doc_orientation_classify=True,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)


def normalize_orientation_angle(
    angle,
) -> int | None:
    """
    Convert PaddleOCR orientation output into
    one of the supported document angles.

    Supported values:

    0
    90
    180
    270
    """

    if angle is None:
        return None

    try:
        angle_value = int(angle)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if angle_value not in {
        0,
        90,
        180,
        270,
    }:
        return None

    return angle_value


def detect_document_orientation(
    file_path: str,
) -> dict:
    """
    Detect document orientation automatically.

    PaddleOCR returns the current document orientation.

    The function converts that orientation into
    the rotation required to correct the document.

    Example:

    Document angle = 0
        -> correction = 0

    Document angle = 90
        -> correction = 270

    Document angle = 180
        -> correction = 180

    Document angle = 270
        -> correction = 90
    """

    path = Path(
        file_path
    )

    if not path.exists():
        return {
            "success": False,
            "detected_orientation": None,
            "rotation_angle": 0,
            "confidence": 0,
            "reason": "File does not exist",
        }

    if (
        path.suffix.lower()
        not in SUPPORTED_IMAGE_EXTENSIONS
    ):
        return {
            "success": False,
            "detected_orientation": None,
            "rotation_angle": 0,
            "confidence": 0,
            "reason": (
                "Automatic orientation detection "
                "currently supports JPG, JPEG, and PNG"
            ),
        }

    image = cv2.imread(
        str(path)
    )

    if image is None:
        return {
            "success": False,
            "detected_orientation": None,
            "rotation_angle": 0,
            "confidence": 0,
            "reason": "Unable to read image",
        }

    try:
        results = orientation_engine.predict(
            str(path)
        )

        detected_angle = None

        for result in results:

            if not hasattr(
                result,
                "json",
            ):
                continue

            data = result.json

            if callable(data):
                data = data()

            if not isinstance(
                data,
                dict,
            ):
                continue

            result_data = data.get(
                "res",
                data,
            )

            doc_preprocessor = (
                result_data.get(
                    "doc_preprocessor_res",
                    {},
                )
            )

            if not isinstance(
                doc_preprocessor,
                dict,
            ):
                continue

            detected_angle = (
                normalize_orientation_angle(
                    doc_preprocessor.get(
                        "angle"
                    )
                )
            )

            if detected_angle is not None:
                break

        if detected_angle is None:
            return {
                "success": False,
                "detected_orientation": None,
                "rotation_angle": 0,
                "confidence": 0,
                "reason": (
                    "Orientation model did not return "
                    "a valid orientation angle"
                ),
            }

        correction_angle = (
            (360 - detected_angle)
            % 360
        )

        return {
            "success": True,
            "detected_orientation": detected_angle,
            "rotation_angle": correction_angle,
            "confidence": 100,
            "reason": (
                "Document orientation detected "
                "successfully"
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "detected_orientation": None,
            "rotation_angle": 0,
            "confidence": 0,
            "reason": (
                f"Orientation detection failed: {error}"
            ),
        }