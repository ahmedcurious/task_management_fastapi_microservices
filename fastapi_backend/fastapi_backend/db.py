from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = 'postgresql://postgres:postgres@db_postgres:5432/fastapi_db'

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)