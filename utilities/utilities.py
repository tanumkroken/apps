# Utilities

import hassapi as hass
import arrow



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
