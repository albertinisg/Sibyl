# Copyright (C) 2012-2013 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Daniel Izquierdo Cortazar <dizquierdo@bitergia.com>
#

from optparse import OptionParser
import datetime

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
import requests

from pyqaanalysis.db import Base, People
from pyqaanalysis.utils import JSONParser


def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-t", "--type",
                      action="store",
                      dest="type",
                      help="Type: askbot (ab)")
    parser.add_option("-l", "--url",
                      action="store",
                      dest="url",
                      help="URL to analyze")
    parser.add_option("-d", "--database",
                      action="store",
                      dest="dbname",
                      help="Database where information is stored")
    parser.add_option("-u", "--db-user",
                      action="store",
                      dest="dbuser",
                      default="root",
                      help="Database user")
    parser.add_option("-p", "--db-password",
                      action="store",
                      dest="dbpassword",
                      default="",
                      help="Database password")
    parser.add_option("-g", "--debug",
                      action="store_true",
                      dest="debug",
                      default=False,
                      help="Debug mode")
    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("Wrong number of arguments")

    return opts

def askbot_info(session, url):

    stream = requests.get(opts.url + "/api/v1/info/")
    parser = JSONParser(unicode(stream.text))
    parser.parse()

    return parser.data


#def askbot_questions():

def askbot_users(session, url):
    
    cont = 1
    pages = 1
    while cont <= pages:
        stream = requests.get(url + "/api/v1/users/?page=" + str(cont))
        cont = cont + 1
        parser = JSONParser(stream.text)
        parser.parse()
        data = parser.data
        pages = int(data.pages)

        for user in data.users:

            dbuser = People()
            dbuser.username = user['username']
            dbuser.reputation = user['reputation']
            dbuser.avatar = user['avatar']
            dbuser.last_seen_at = datetime.datetime.fromtimestamp(int(user['last_seen_at'])).strftime('%Y-%m-%d %H:%M:%S')
            dbuser.joined_at = datetime.datetime.fromtimestamp(int(user['joined_at'])).strftime('%Y-%m-%d %H:%M:%S')
            dbuser.user_identifier = user['id']

            session.add(dbuser)
            session.commit()


def parse_askbot(session, url):

    info = askbot_info(session, url)
    users = askbot_users(session, url)


if __name__ == '__main__':
    opts = read_options()

    options = """mysql://%s:%s@localhost/%s?charset=utf8""" % (opts.dbuser, opts.dbpassword, opts.dbname)
    engine = create_engine(options, encoding = 'utf-8')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Previously create database with 
    # CREATE DATABASE <database> CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    Base.metadata.create_all(engine)
    
    session.commit()

    if opts.type == "ab":
        # askbot backend
        parse_askbot(session, opts.url)

        
