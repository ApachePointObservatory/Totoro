#!/usr/bin/env python
# encoding: utf-8
"""

DatabaseConnect.py

Created by José Sánchez-Gallego on 10 Oct 2015.
Licensed under a 3-clause BSD license.

Revision history:
    10 Oct 2015 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.event import listen
from sqlalchemy.pool import Pool
from simplecrypt import decrypt
import warnings
import configparser
import StringIO
import os


__MODELS__ = ['plateDB']


def readProfile(profile, path=None):
    """Reads a profile and creates the appropriate connection string."""

    profilesPath = os.path.join(os.path.expanduser('~'), '.sdssconnect',
                                'profiles.ini') if path is None else path

    if not os.path.exists(profilesPath):
        raise RuntimeError('profile not found in {0}'.format(profilesPath))

    if 'SDSSCONNECT_PASSWORD' not in os.environ:
        raise RuntimeError('$SDSSCONNECT_PASSWORD not defined')

    passwd = os.environ['SDSSCONNECT_PASSWORD']

    config = configparser.ConfigParser()
    config.readfp(
        StringIO.StringIO(
            decrypt(passwd, open(profilesPath, 'r').read()).decode('utf8')))

    if not config.has_section(profile.lower()):
        raise ValueError('profile {0} does not exist'.format(profile.lower()))

    return dict(config.items(profile.lower()))


def clearSearchPathCallback(dbapi_con, connection_record):
    """
    When creating relationships across schema, SQLAlchemy
    has problems when you explicitly declare the schema in
    ModelClasses and it is found in search_path.

    The solution is to set the search_path to "$user" for
    the life of any connection to the database. Since there
    is no (or shouldn't be!) schema with the same name
    as the user, this effectively makes it blank.

    This callback function is called for every database connection.

    For the full details of this issue, see:
    http://groups.google.com/group/sqlalchemy/browse_thread/
    thread/88b5cc5c12246220

    dbapi_con - type: psycopg2._psycopg.connection
    connection_record - type: sqlalchemy.pool._ConnectionRecord
    """

    cursor = dbapi_con.cursor()
    cursor.execute('SET search_path TO "$user",functions')
    dbapi_con.commit()


listen(Pool, 'connect', clearSearchPathCallback)


class DatabaseConnection(object):

    _singletons = dict()
    _defaultConnectionName = 'default'

    def __new__(cls, *args, **kwargs):

        if len(args) == 1:
            kwargs['profile'] = args[0]
        elif len(args) > 1:
            raise ValueError('SDSSDatabaseConnection only '
                             'accepts one argument')

        new = kwargs.get('new', False)
        connectionName = kwargs.get('name', None)

        if len(cls._singletons.keys()) == 0:
            if connectionName is not None:
                cls._defaultConnectionName = connectionName
            cls._singletons[cls._defaultConnectionName] = \
                cls._createNewInstance(**kwargs)
        elif new:
            newConn = cls._createNewInstance(**kwargs)
            if connectionName is not None:
                if connectionName == cls._defaultConnectionName:
                    warnings.warn('overriding default connection', UserWarning)
                cls._singletons[connectionName] = newConn
            return newConn

        return cls._singletons[cls._defaultConnectionName]

    @classmethod
    def _createNewInstance(cls, profile=None, databaseConnectionString=None,
                           expireOnCommit=True, models='all', **kwargs):
        """Creates a new instance of the connection."""

        assert profile is not None or databaseConnectionString is not None, \
            ('either profile or databaseConnectionString must be defined.')

        me = object.__new__(cls)

        if profile is not None:
            profileDict = readProfile(profile)
            me.databaseConnectionString = (
                'postgresql+psycopg2://{user}:{password}@'
                '{host}:{port}/{database}'.format(**profileDict))
        else:
            me.databaseConnectionString = databaseConnectionString

        me.engine = create_engine(me.databaseConnectionString, echo=False)

        me.metadata = MetaData()
        me.metadata.bind = me.engine
        me.Base = declarative_base(bind=me.engine)
        me.Session = scoped_session(
            sessionmaker(bind=me.engine, autocommit=True,
                         expire_on_commit=expireOnCommit))

        me.addModels(models)

        return me

    @classmethod
    def getConnection(cls, connectionName):
        """Returns a named connection."""

        if connectionName not in cls._singletons:
            raise KeyError('connection named {0} does not exist'
                           .format(connectionName))

        return cls._singletons[connectionName]

    @classmethod
    def listConnections(cls):
        """Returns a list of all available connections."""

        return cls._singletons.keys()

    @classmethod
    def getDefaultConnection(cls):
        """Returns the default connection."""

        if len(cls._singletons) == 0:
            raise RuntimeError('no connections available')
        elif cls._defaultConnectionName not in cls._singletons:
            raise KeyError('default connection {0} does not exist'
                           .format(cls._defaultConnectionName))

        return cls._singletons[cls._defaultConnectionName]

    @classmethod
    def setDefaultConnection(cls, connectionName):
        """Sets the default connection."""

        if connectionName not in cls._singletons:
            raise KeyError('connection named {0} does not exist'
                           .format(connectionName))

        cls._defaultConnectionName = connectionName

    def addModels(self, models, overwrite=False):
        """Adds a list of model classes to the object."""

        assert isinstance(models, (list, tuple, basestring)), \
            ('models must be \'all\' or a list of strings.')

        if models == 'all':
            models = __MODELS__

        for model in models:
            if hasattr(self, model) and not overwrite:
                continue
            exec('from SDSSconnect.{0} import construct_{0}'.format(model))
            exec('self.{0} = construct_{0}(self.Base)'.format(model))
