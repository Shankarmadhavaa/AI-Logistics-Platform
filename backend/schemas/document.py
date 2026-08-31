from datetime import datetime

from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    content_type: str | None
    file_size_bytes: int
    file_hash: str
    uploaded_at: datetime
    status: str