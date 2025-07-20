from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "mysql+pymysql://u759828498_waregent_admin:Waregent000#@217.21.87.103/u759828498_waregent"

engine=create_engine(DB_URL)
mysession=sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()