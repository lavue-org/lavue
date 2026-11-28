#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2014 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
# \package test nexdatas
# \file TangoDbUtils.py
# helpers for the tango database of test servers
#
import time

try:
    import tango
except Exception:
    import PyTango as tango


#: (:obj:`int`) timeout of database commands in ms
DBTIMEOUT = 30000


def database(timeout=DBTIMEOUT):
    """ provides a tango database proxy with an increased timeout

    Database commands, e.g. DbAddDevice or DbDeleteServer, can exceed
    the default 3 s timeout on busy databases.

    :param timeout: database timeout in ms
    :type timeout: :obj:`int`
    :returns: tango database proxy
    :rtype: :class:`tango.Database`
    """
    db = tango.Database()
    db.set_timeout_millis(timeout)
    return db


def retry(command, *args, **kwargs):
    """ executes a database command and retries it if it fails

    :param command: database command, e.g. ``db.add_device``
    :type command: :obj:`callable`
    :param args: command arguments
    :type args: :obj:`list`
    :param retries: number of attempts
    :type retries: :obj:`int`
    :returns: command result
    :rtype: `any`
    """
    retries = kwargs.pop("retries", 3)
    for attempt in range(retries):
        try:
            return command(*args, **kwargs)
        except tango.DevFailed:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def add_device(info, db=None):
    """ adds a device to the tango database

    :param info: device info
    :type info: :class:`tango.DbDevInfo`
    :param db: tango database proxy, :func:`database` if None
    :type db: :class:`tango.Database`
    """
    db = db or database()
    retry(db.add_device, info)


def add_server(server, devices, db=None):
    """ adds a server with its devices to the tango database

    :param server: server name, i.e. ``executable/instance``
    :type server: :obj:`str`
    :param devices: device info or list of device infos
    :type devices: :class:`tango.DbDevInfo` \
                   or :obj:`list` <:class:`tango.DbDevInfo`>
    :param db: tango database proxy, :func:`database` if None
    :type db: :class:`tango.Database`
    """
    db = db or database()
    retry(db.add_server, server, devices)


def delete_server(server, retries=3, timeout=DBTIMEOUT):
    """ deletes a server from the tango database

    DbDeleteServer can exceed the default 3 s timeout on busy databases,
    so the timeout is increased and the command is retried.

    :param server: server name, i.e. ``executable/instance``
    :type server: :obj:`str`
    :param retries: number of attempts
    :type retries: :obj:`int`
    :param timeout: database timeout in ms
    :type timeout: :obj:`int`
    """
    retry(database(timeout).delete_server, server, retries=retries)
