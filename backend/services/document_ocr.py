from pathlib import Path

from paddleocr import PaddleOCR

from backend.services.document_preprocessing import (
    preprocess_document,
)


ocr_engine = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
)


def extract_text(
    file_path: str,
) -> dict:
    """
    Extract text from a document.

    Processing pipeline:

    Original document
        ↓
    Automatic preprocessing
        ↓
    Orientation correction
        ↓
    Deskew
        ↓
    OCR enhancement
        ↓
    PaddleOCR
    """

    path = Path(
        file_path
    )

    if not path.exists():
        return {
            "success": False,
            "text": "",
            "reason": "File does not exist",
            "processed_path": None,
            "detected_orientation": None,
            "rotation_angle": 0,
            "orientation_confidence": 0,
        }

    preprocessing_result = (
        preprocess_document(
            str(path)
        )
    )

    if not preprocessing_result[
        "success"
    ]:
        return {
            "success": False,
            "text": "",
            "reason": (
                preprocessing_result[
                    "reason"
                ]
            ),
            "processed_path": None,
            "detected_orientation": (
                preprocessing_result.get(
                    "detected_orientation"
                )
            ),
            "rotation_angle": (
                preprocessing_result.get(
                    "rotation_angle",
                    0,
                )
            ),
            "orientation_confidence": (
                preprocessing_result.get(
                    "orientation_confidence",
                    0,
                )
            ),
        }

    processed_path = (
        preprocessing_result[
            "processed_path"
        ]
    )

    try:
        result = ocr_engine.predict(
            processed_path
        )

        extracted_lines = []

        for page_result in result:

            if not hasattr(
                page_result,
                "json",
            ):
                continue

            data = page_result.json

            if callable(data):
                data = data()

            if not isinstance(
                data,
                dict,
            ):
                continue

            ocr_res = data.get(
                "res",
                data,
            )

            texts = ocr_res.get(
                "rec_texts",
                [],
            )

            for text in texts:

                if (
                    text
                    and text.strip()
                ):
                    extracted_lines.append(
                        text.strip()
                    )

        extracted_text = "\n".join(
            extracted_lines
        )

        if not extracted_text.strip():
            return {
                "success": True,
                "text": "",
                "reason": (
                    "OCR completed but "
                    "no readable text was detected"
                ),
                "processed_path": (
                    processed_path
                ),
                "detected_orientation": (
                    preprocessing_result.get(
                        "detected_orientation"
                    )
                ),
                "rotation_angle": (
                    preprocessing_result.get(
                        "rotation_angle",
                        0,
                    )
                ),
                "orientation_confidence": (
                    preprocessing_result.get(
                        "orientation_confidence",
                        0,
                    )
                ),
            }

        return {
            "success": True,
            "text": extracted_text,
            "reason": (
                "Document preprocessing and "
                "OCR completed successfully"
            ),
            "processed_path": (
                processed_path
            ),
            "detected_orientation": (
                preprocessing_result.get(
                    "detected_orientation"
                )
            ),
            "rotation_angle": (
                preprocessing_result.get(
                    "rotation_angle",
                    0,
                )
            ),
            "orientation_confidence": (
                preprocessing_result.get(
                    "orientation_confidence",
                    0,
                )
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "text": "",
            "reason": (
                f"OCR failed: {error}"
            ),
            "processed_path": (
                processed_path
            ),
            "detected_orientation": (
                preprocessing_result.get(
                    "detected_orientation"
                )
            ),
            "rotation_angle": (
                preprocessing_result.get(
                    "rotation_angle",
                    0,
                )
            ),
            "orientation_confidence": (
                preprocessing_result.get(
                    "orientation_confidence",
                    0,
                )
            ),
        }