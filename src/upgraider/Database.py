from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text
import json
import os

script_path = os.path.dirname(os.path.realpath(__file__))
Base = declarative_base()
engine = create_engine(
    f"sqlite:///{script_path}/resources/database/releasenotes.db",
    echo=False,
)
Session = sessionmaker(bind=engine)

class LibReleaseNote(Base):
    __tablename__ = "lib_release_notes"
    id = Column(Integer, primary_key=True)
    library = Column(String)
    version = Column(String)
    filename = Column(String)

class DeprecationComment(Base):
    __tablename__ = "deprecation_comments"
    id = Column(Integer, primary_key=True)
    lib_release_note = Column(Integer)
    content = Column(String)
    embedding = Column(Text)


def get_embedded_doc_sections() -> list[DeprecationComment]:
    session = Session()
    sections = (
        session.query(DeprecationComment)
        .filter(DeprecationComment.embedding != "NULL")
        .filter(DeprecationComment.embedding != None)
        .all()
    )

    session.close()
    return sections

def load_embeddings(
    sections: list[DeprecationComment],
) -> dict[int, list[float]]:
    """
    Read the section embeddings and their keys from the database
    """

    return {
        section.id: json.loads(section.embedding)
        for section in sections
    }