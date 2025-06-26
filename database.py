from sqlalchemy import create_engine, Column, String, Float, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

# SQLALCHEMY_DATABASE_URL = 'postgresql://<username>:<password>@<ip-address/hostname>/<database-name>'
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:1234@0.0.0.0/snmp_data'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Snmp_10(Base):
    __tablename__ = 'snmps'
    id = Column(Integer, primary_key=True)
    timedata = Column(String)
    snmpdata = Column(String)

class Snmp_cur(Base):
    __tablename__ = 'snmpcur'
    id = Column(Integer, primary_key=True)
    snmpdata = Column(String)

class Snmp_30sec(Base):
    __tablename__ = 'snmp30'
    id = Column(Integer, primary_key=True)
    snmpdata = Column(String)

class SnmpMin(Base):
    __tablename__ = 'snmpmin'
    id = Column(Integer, primary_key=True)
    snmpdata = Column(String)

# Dependency
def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

