# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# using SQLite database for log
engine = create_engine('sqlite:///timetracker.db')
Base = declarative_base()


class Project(Base):

    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tasks = relationship("Task")

    @staticmethod
    def create_project(name):
        entry = Project(name=name)
        session.add(entry)
        session.commit()


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project, primaryjoin=project_id == Project.id)
    time_entries = relationship("TimeEntry",  order_by='desc(TimeEntry.start_datetime)', lazy='dynamic')
    external_task_id = Column(String, nullable=True)

    @property
    def is_inprogress(self):
        return self.time_entries.filter(~TimeEntry.end_datetime).count() == 1

    @staticmethod
    def create_task(name, project_id):
        entry = Task(name=name, project_id=project_id)
        session.add(entry)
        session.commit()


class TimeEntry(Base):

    __tablename__ = 'timeentry'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    task_id = Column(Integer, ForeignKey('task.id'))
    task = relationship(Task, primaryjoin=task_id == Task.id)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)

    @staticmethod
    def start_log(task_id):
        entry = TimeEntry(task_id=task_id, start_datetime=datetime.datetime.now())
        session.add(entry)
        session.commit()

    @staticmethod
    def stop_log(task_id):
        entry = session.query(TimeEntry).filter_by(task_id=task_id).first()
        entry.end_datetime = datetime.datetime.now()
        session.commit()

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
