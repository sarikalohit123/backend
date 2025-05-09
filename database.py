from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "mysql+pymysql://root:@localhost:3306/waregent"

engine=create_engine(DB_URL)
mysession=sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()