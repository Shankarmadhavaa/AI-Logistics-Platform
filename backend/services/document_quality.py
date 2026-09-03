from pathlib import Path

from PIL import Image
import pypdf


# --------------------------------
# Supported document extensions
# --------------------------------

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


# --------------------------------
# Check image readability
# --------------------------------

def check_image_readability(file_path: Path) -> tuple[bool, bool]:
    """
    Check whether an image can be opened and whether
    the image is completely blank.

    Returns:
        (readable, blank)

    Important:
    - Slight blur is allowed.
    - Dark/light images are allowed.
    - Tilted images are allowed.
    - Only completely blank images are rejected.
    """

    try:
        # First check whether the image file is valid
        with Image.open(file_path) as image:
            image.verify()

        # Re-open the image after verify()
        with Image.open(file_path) as image:

            width, height = image.size

            # Invalid image dimensions
            if width <= 0 or height <= 0:
                return False, False

            # Convert image to grayscale
            grayscale = image.convert("L")

            # Get minimum and maximum pixel values
            minimum, maximum = grayscale.getextrema()

            # --------------------------------
            # Detect completely blank image
            # --------------------------------
            #
            # JPEG compression can create small pixel
            # variations even when the page looks blank.
            #
            # A very small pixel range means the image
            # is essentially one uniform blank surface.
            #
            if maximum - minimum <= 5:
                return True, True

            # Load the image into memory
            grayscale.load()

        # Image is readable and contains pixel variation
        return True, False

    except Exception:
        return False, False


# --------------------------------
# Check PDF readability
# --------------------------------

def check_pdf_readability(file_path: Path) -> bool:
    """
    Check whether a PDF can be opened and contains
    at least one page.
    """

    try:
        reader = pypdf.PdfReader(str(file_path))

        if len(reader.pages) == 0:
            return False

        return True

    except Exception:
        return False


# --------------------------------
# Check document quality
# --------------------------------

def check_document_quality(file_path: str) -> dict:
    """
    Perform basic document quality checks.

    Decision rules:

    PROCESS:
        Document exists, is supported, and can be read.

    DO_NOT_PROCESS:
        Document is missing, empty, unsupported,
        corrupted, unreadable, or completely blank.

    MANUAL REVIEW:
        Used when the document requires human attention.
    """

    path = Path(file_path)

    # --------------------------------
    # 1. Check if file exists
    # --------------------------------

    if not path.exists():
        return {
            "quality_status": "DO_NOT_PROCESS",
            "quality_score": 0,
            "reason": "File does not exist",
            "manual_review_required": True,
        }

    # --------------------------------
    # 2. Check file size
    # --------------------------------

    file_size = path.stat().st_size

    if file_size == 0:
        return {
            "quality_status": "DO_NOT_PROCESS",
            "quality_score": 0,
            "reason": "File is empty",
            "manual_review_required": True,
        }

    # --------------------------------
    # 3. Check file extension
    # --------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return {
            "quality_status": "DO_NOT_PROCESS",
            "quality_score": 0,
            "reason": "Unsupported document type",
            "manual_review_required": True,
        }

    # --------------------------------
    # 4. Check readability
    # --------------------------------

    if extension in {".jpg", ".jpeg", ".png"}:

        readable, blank = check_image_readability(path)

        # Completely blank image
        if blank:
            return {
                "quality_status": "DO_NOT_PROCESS",
                "quality_score": 0,
                "reason": "Image is completely blank",
                "manual_review_required": True,
            }

    elif extension == ".pdf":

        readable = check_pdf_readability(path)

    else:

        readable = False

    # --------------------------------
    # 5. Stop unreadable documents
    # --------------------------------

    if not readable:
        return {
            "quality_status": "DO_NOT_PROCESS",
            "quality_score": 0,
            "reason": "Document could not be read or is corrupted",
            "manual_review_required": True,
        }

    # --------------------------------
    # 6. Basic quality passed
    # --------------------------------

    return {
        "quality_status": "PROCESS",
        "quality_score": 100,
        "reason": "Document is readable and ready for processing",
        "manual_review_required": False,
    }