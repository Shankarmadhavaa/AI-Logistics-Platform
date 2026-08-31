import uuid


def generate_document_id() -> str:
    return f"DOC-{uuid.uuid4().hex}"