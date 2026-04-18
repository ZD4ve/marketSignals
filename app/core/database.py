from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import datetime
from typing import Optional
from app.core.config import settings

engine = create_engine(settings.database_url, echo=False)

class OpsDocumentLog(SQLModel, table=True):
    __tablename__ = "ops_document_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_url: str = Field(unique=True, index=True)
    module_name: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
