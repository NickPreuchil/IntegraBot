from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Tutor(Base):
    __tablename__ = 'tutors'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    name = Column(String(255))
    creation_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with students
    students = relationship("Student", back_populates="tutor")

    def __repr__(self):
        return f"<Tutor(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    name = Column(String(255))
    creation_date = Column(DateTime, default=datetime.utcnow)
    tutor_id = Column(Integer, ForeignKey('tutors.id'), nullable=False)
    
    # Relationship with tutor
    tutor = relationship("Tutor", back_populates="students")

    def __repr__(self):
        return f"<Student(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


# Database initialization function
def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
