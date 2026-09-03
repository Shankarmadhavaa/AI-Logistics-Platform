from pathlib import Path

from paddleocr import PaddleOCR


# --------------------------------
# Initialize OCR engine
# --------------------------------

ocr_engine = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)


# --------------------------------
# Extract text from document
# --------------------------------

def extract_text(file_path: str) -> dict:
    """
    Extract text from a document using PaddleOCR.
    """

    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "text": "",
            "reason": "File does not exist",
        }

    try:

        result = ocr_engine.predict(
            str(path)
        )

        extracted_lines = []

        for page_result in result:

            if not hasattr(page_result, "json"):
                continue

            data = page_result.json

            if callable(data):
                data = data()

            if not isinstance(data, dict):
                continue

            ocr_res = data.get("res", data)

            texts = ocr_res.get("rec_texts", [])

            for text in texts:

                if text and text.strip():
                    extracted_lines.append(
                        text.strip()
                    )

        extracted_text = "\n".join(
            extracted_lines
        )

        return {
            "success": True,
            "text": extracted_text,
            "reason": "Text extracted successfully",
        }

    except Exception as error:

        return {
            "success": False,
            "text": "",
            "reason": f"OCR failed: {str(error)}",
        }