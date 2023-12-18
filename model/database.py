from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import sessionmaker

"""the SQLALchemy relationships for our database"""

DATABASE_NAME = 'model/lunchtag.sqlite'

Base = declarative_base()

user_classroom_association = Table('user_classroom', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id')),
    Column('classroom_id', Integer, ForeignKey('classroom.classroom_id')),
    Column('user_classroom_score', Integer, default=0)
)

admin_classroom_association = Table('admin_classroom', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id')),
    Column('classroom_id', Integer, ForeignKey('classroom.classroom_id'))
)

class User(UserMixin, Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    user_email = Column(String)
    user_phone = Column(String)
    password_hash = Column(String)

    classrooms = relationship("Classroom", secondary=user_classroom_association, back_populates="users")
    admin_classrooms = relationship("Classroom", secondary=admin_classroom_association, back_populates="admins")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password): # for flask_login
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.user_id)

class Classroom(Base):
    __tablename__ = 'classroom'
    classroom_id = Column(Integer, primary_key=True)
    classroom_name = Column(String)
    classroom_bio = Column(Text)
    feed_id = Column(Integer, ForeignKey('feed.id'))
    feed = relationship("Feed", back_populates="classrooms")

    users = relationship("User", secondary=user_classroom_association, back_populates="classrooms")
    admins = relationship("User", secondary=admin_classroom_association, back_populates="admin_classrooms")
    matches = relationship("Match", back_populates="classroom")

class Feed(Base):
    __tablename__ = 'feed'
    id = Column(Integer, primary_key=True)
    classrooms = relationship("Classroom", back_populates="feed")

class Match(Base):
    __tablename__ = 'match'
    match_id = Column(Integer, primary_key=True)
    classroom_id = Column(Integer, ForeignKey('classroom.classroom_id'))
    user1_id = Column(Integer, ForeignKey('user.user_id'))
    user2_id = Column(Integer, ForeignKey('user.user_id'))
    user3_id = Column(Integer, ForeignKey('user.user_id'))
    complete = Column(Boolean, default=False)

    classroom = relationship("Classroom", back_populates="matches")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    user3 = relationship("User", foreign_keys=[user3_id])
