from sqlalchemy import UUID, Column
from sqlalchemy.orm import as_declarative


# ----------------------------------------------------------------------------
@as_declarative()
class Base:
    id = Column(UUID(as_uuid=True), primary_key=True)
