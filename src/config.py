from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

load_dotenv()  # Load environmental variables in .env

# Initalize db
DATABASE_URI = "sqlite:///recipes.db"
engine = create_engine(DATABASE_URI, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
