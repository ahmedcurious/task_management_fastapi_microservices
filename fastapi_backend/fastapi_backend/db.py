from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://ahmed:password@localhost:5432/fastapi_database"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)