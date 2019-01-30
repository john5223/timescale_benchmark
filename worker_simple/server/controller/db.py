import os
from celery import Task

import psycopg2
from psycopg2.extras import NamedTupleCursor


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


class SQLAlchemyTask(Task):
    abstract = True
    _db = None

    @property
    def db(self):
        if self._db is not None:
            return self._db

        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session
        from sqlalchemy.orm import sessionmaker

        conn_string = ""
        '''
        self._db = psycopg2.connect(
            host=self.app.conf.POSTGRES_HOST,
            port=self.app.conf.POSTGRES_PORT,
            dbname=self.app.conf.POSTGRES_DBNAME,
            user=self.app.conf.POSTGRES_USER,
            password=self.app.conf.POSTGRES_PASSWORD,
            cursor_factory=NamedTupleCursor,
            connection_factory=Connection,
        )
        '''
        engine = create_engine(
            conn_string, convert_unicode=True,
            pool_recycle=3600, pool_size=10)
        db_session = scoped_session(sessionmaker(
            autocommit=False, autoflush=False, bind=engine))
        self._db = db_session
        return self._db

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Clean up database after the task is finished.

        """
        self._db.close()
        self._db = None
