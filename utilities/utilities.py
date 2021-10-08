# Utilities

import hassapi as hass
import arrow
from pymongo import MongoClient
from urllib.parse import quote_plus
import logging

TEST_ENV = False # False when the class is instantiated under appdaemon

MONGO_USER = 'oca'
MONGOPSWD  = 'PostFuru'


class Logger:
    def __init__(self, logger, log_level:str):
        self.log = logger
        self.log_level = log_level

    def info(self, msg):
        if not TEST_ENV:
            self.log(msg, level = 'INFO', ascii_encode=False)
        else:
            self.log.info(msg)
        return

    def error(self, msg):
        if not TEST_ENV:
            if self.log_level == 'ERROR':
                self.log('ERROR: ' + msg, level = 'INFO',ascii_encode=False)
        else:
            self.log.error(msg)
        return

    def debug(self, msg):
        if not TEST_ENV:
            if self.log_level == 'DEBUG':
                self.log('DEBUG: ' + msg, level = 'INFO', ascii_encode=False)
        else:
            self.log.debug(msg)
        return

    def warning(self, msg):
        if not TEST_ENV:
            if self.log_level == 'WARNING':
                self.log('WARNING: ' + msg, level = 'INFO', ascii_encode=False)
        else:
            self.log.warning(msg)
        return


class DateTimeConverter:
    def __init__(self, date_time: str =''):
        if date_time == '':
            date_time = self.now()
        self.dt_str = date_time
        self.ar = arrow.get(date_time)

    def use_timestamp(self, ts):
        self.ar = arrow.get(ts)

    def now(self):
        return arrow.now().format('YYYY-MM-DDTHH:mm:ssZZ')

    def month(self):
        return self.ar.format("MMMM")

    def day(self):
        return self.ar.format("dddd")

    def today(self):
        return arrow.now().format("dddd")

    def tomorrow(self):
        today = arrow.now()
        return today.shift(days=+1).format("dddd")

    def yesterday(self):
        today = arrow.now()
        return today.shift(days=-1).format("dddd")

    def year(self):
        return self.ar.format("YYYY")

    def hour(self):
        return self.ar.format("HH")

    def minute(self):
        return self.ar.format("m")

    def second(self):
        return self.ar.format("s")

    def timezone(self):
        return self.ar.format("ZZ")

    def day_number(self):
        return self.ar.format("d")

    def ISO_week(self):
        return self.ar.format("W")

    def day_of_month(self):
        return self.ar.format("D")

    def week_number(self):
        dt_str = self.ar.strftime('%Y-%m-%d %H:%M:%S.%f')
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
        return dt.strftime("%W")

    def day_of_year(self):
        dt_str = self.ar.strftime('%Y-%m-%d %H:%M:%S.%f')
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
        return dt.strftime("%j")

    def humanize(self):
        return self.ar.humanize()

    def date_time(self):
        return self.ar

    def date_time_string(self):
        return self.dt_str

    def delta_days(self, dt_str: str):
        ''' Number of days between now and the input date'''
        date = arrow.get(dt_str)
        return (date - arrow.utcnow()).days

    def delta_time(self, dt_str: str):
        ''' Time between now and input date'''
        date = arrow.get(dt_str)
        return date.humanize()



"""
Monitor events and output changes to the verbose_log. Nice for debugging purposes.
Arguments:
 - events: List of events to monitor
"""


class Monitor(hass.Hass):
    def initialize(self):
        events = self.args["events"]

        for event in events:
            self.changed(event, None, None, None, None)
            self.log(f'Watching event "{event}" for state changes')
            self.listen_state(self.changed, event)

    def changed(self, entity, attribute, old, new, kwargs):
        value = self.get_state(entity, "all")
        self.log(entity + ": " + str(value))


class LogMLGW(hass.Hass):
    def initialize(self):
        event = self.args["event"]
        host = self.args["mongo_host"]
        user = MONGO_USER
        pswd = MONGOPSWD
        uri = "mongodb://%s:%s@%s" % (
        quote_plus(user), quote_plus(pswd), host)
        self.client = MongoClient(uri)
        self.mongo_db = self.args["mongo_db"]
        self.log(f'Logging event "{event}" to {host} for events')
        self.listen_event(self.receive_mlgw_msg, 'mlgw.ML_telegram')

    def receive_mlgw_msg(self, event_id, payload_event, *args):
        db = self.get_db(self.mongo_db)
        if db is not None:
            mlgw = db.mlgw
            id = mlgw.insert_one(payload_event)
            self.log(f'Inserted document with id {id} in collection {mlgw}')
        else:
            self.log(f'No mongo database {db}', log_level='ERROR')

    def get_db(self, db):
        try:
            return self.client[db]
        except KeyError as err:
            self.log(f"Non-existent mongo db {db}. Error: " +err)
            return None



class LogSpotify(hass.Hass):
    def initialize(self):
        events = self.args["events"]
        host = self.args["mongo_host"]
        user = MONGO_USER
        pswd = MONGOPSWD
        uri = "mongodb://%s:%s@%s" % (
            quote_plus(user), quote_plus(pswd), host)
        self.client = MongoClient(uri)
        self.mongo_db = self.args["mongo_db"]

        for event in events:
            self.changed(event, None, None, None, None)
            self.log(f'Watching event "{event}" for state changes')
            self.listen_state(self.changed, event)

    def changed(self, entity, attribute, old, new, kwargs):
        value = self.get_state(entity, "all")
        db = self.get_db(self.mongo_db)
        if db is not None:
            spotify = db.spotify
            id = spotify.insert_one(value)
            self.log(f'Inserted document with id {id} in collection {spotify}')
        else:
            self.log(f'No mongo database {db}', log_level='ERROR')

    def get_db(self, db):
        try:
            return self.client[db]
        except KeyError as err:
            self.log(f"Non-existent mongo db {db}. Error: " +err)
            return None

class LogBertie(hass.Hass):
    def initialize(self):
        events = self.args["events"]
        host = self.args["mongo_host"]
        user = MONGO_USER
        pswd = MONGOPSWD
        uri = "mongodb://%s:%s@%s" % (
            quote_plus(user), quote_plus(pswd), host)
        self.client = MongoClient(uri)
        self.mongo_db = self.args["mongo_db"]

        for event in events:
            self.changed(event, None, None, None, None)
            self.log(f'Watching event "{event}" for state changes')
            self.listen_state(self.changed, event)

    def changed(self, entity, attribute, old, new, kwargs):
        value = self.get_state(entity, "all")
        db = self.get_db(self.mongo_db)
        if db is not None:
            bertie = db.bertie
            id = bertie.insert_one(value)
            self.log(f'Inserted document with id {id} in collection {bertie}')
        else:
            self.log(f'No mongo database {db}', log_level='ERROR')

    def get_db(self, db):
        try:
            return self.client[db]
        except KeyError as err:
            self.log(f"Non-existent mongo db {db}. Error: " +err)
            return None

