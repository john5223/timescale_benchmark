import os
from celery import Task

import psycopg2
from psycopg2.extras import NamedTupleCursor

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

import logging
logger = logging.getLogger(__name__)

engine = None

class PostgresTask(Task):
    abstract = True
    _db = None

    @property
    def db_host(self):
        return self.app.conf.POSTGRES_HOST

    @property
    def db(self):
        if self._db is not None:
            return self._db
        self._db = psycopg2.connect(
            host=self.db_host,
            port=self.app.conf.POSTGRES_PORT,
            dbname=self.app.conf.POSTGRES_DBNAME,
            user=self.app.conf.POSTGRES_USER,
            password=self.app.conf.POSTGRES_PASSWORD,
            #cursor_factory=NamedTupleCursor,
            #connection_factory=Connection,
        )
        return self._db

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Clean up database after the task is finished.

        """
        self._db.close()
        self._db = None



class TimescaleTask(PostgresTask):

    @property
    def db_host(self):
        return self.app.conf.TIMESCALEDB_HOST


# TODO
# class SQLAlchemySingleton



class SQLAlchemyTask(Task):
    abstract = True
    _db_session = None

    @property
    def db_host(self):
        return self.app.conf.POSTGRES_HOST

    @property
    def db_session(self):
        if self._db_session is not None:
            return self._db_session

        global engine
        if not engine:
            conn_string = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
                host=self.app.conf.POSTGRES_HOST,
                port=self.app.conf.POSTGRES_PORT or '5432',
                dbname=self.app.conf.POSTGRES_DBNAME,
                user=self.app.conf.POSTGRES_USER,
                password=self.app.conf.POSTGRES_PASSWORD,
            )
            logger.info("Creating engine")
            logger.info(conn_string)
            tasks_engine = create_engine(
                conn_string, convert_unicode=True,
                pool_recycle=3600, pool_size=10)
            engine = tasks_engine
        else:
            tasks_engine = engine

        logger.info("Creating session")
        db_session = scoped_session(sessionmaker(
            autocommit=False, autoflush=False, bind=tasks_engine))
        self._db_session = db_session
        return self._db_session

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Clean up database after the task is finished.

        """
        self._db_session.remove()
        self._db_session = None


class TimescaleAlchemyTask(SQLAlchemyTask):

    @property
    def db_host(self):
        return self.app.conf.TIMESCALEDB_HOST
