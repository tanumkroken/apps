# -*- coding: utf-8 -*-
# services
import appdaemon.plugins.hass.hassapi as hass
import calendar
import datetime

class StateBase(hass.Hass):
    ''' Base class for apps that will listen to HA state changes'''

    def initialize(self):
        # Implement the callback interface that AD expects
        event = self.args['entity'] # The event to listen to
        # For state callbacks, a class defined callback function should look like this:
        # def my_callback(self, entity, attribute, old, new, kwargs)
        self.base_callback(event, None, None, None,None)
        self.listen_state(self.base_callback,event)

    def base_callback(self, entity, attribute, old, new, kwargs):
        ''' The abstract class callback for state-ful classes'''
        # Store the call-back arguments
        self.entity = entity # The name of the entity the call-back was requested for
        self.attribute = attribute # The name of the attribute the call-back was requested for
        self.old = old # The value of the state before the state change.
        self.new = new # The value of the state after the state change.
        self.user_args = kwargs # A dictionary containing any constraints and/or additional user specific keyword arguments supplied to the listen_state() call.
        # Get all arguments for the requested entity
        args = self.get_state(entity, "all")
        # Store the state
        self.state = args['state']
        # Store the attribute values
        self.attributes = args['attributes']
        if self.args['logging'] is True:
            self.log(entity + ': Old: ' + str(old))
            self.log(entity + ': New: ' + str(new))
            self.log(entity + ': Attribute: ' + str(attribute))
            self.log(entity + ': Attributes: ' + str(self.attributes))
            self.log(entity + ': Arguments: ' + str(args))
        return
    
    def get_attributes(self) -> dict:
        return self.attributes

class Weather(StateBase):

    def get_today_temperature(self):
        t = self.attrubutes['temperature']
        unit = ' ' + u'\xb0' + 'C'
        result = str(t) + unit
        #self.log(entity + 'temperature: ' + result, ascii_encode= False)
        return result


    def bearing(self, bearing: float, short_form: True) -> str:
        ''' Convert bearing in degrees to metorological wind direction
        Reference: https://orap.met.no/Kodeforklaring/Kodebok/koder/VINDRETNING.html'''
        long_form = {'N': 'North', 'NNE': 'North North-East', 'ENE': 'East North-East', 'E': 'East',
                    'ESE': 'East South-East', 'SE': 'South East', 'SSE': 'South South-East', 'S': 'South',
                    'SSW': 'South South-West', 'SW': 'South West', 'WSW': 'West South-West', 'W': 'West',
                    'WNW': 'West North-West', 'NW': 'North West', 'NNW': 'North North-West'}
    # convert bearing to decimal degrees dd
        dd = int(bearing / 10)
        wb = 'N'  # Cover dd = 0
        if dd < 5:
            wb = 'NNE'
        elif dd == 5:
            wb = 'NE'
        elif dd > 5 and dd < 9:
            wb = 'ENE'
        elif dd == 9:
            wb = 'E'
        elif dd > 9 and dd < 14:
            wb = 'ESE'
        elif dd == 14:
            wb = 'SE'
        elif dd > 14 and dd < 18:
            wb = 'SSE'
        elif dd == 18:
            wb = 'S'
        elif dd > 18 and dd < 22:
            wb = 'SSW'
        elif dd == 22:
            wb = 'SW'
        elif dd > 22 and dd < 27:
            wb = 'WSW'
        elif dd == 27:
            wb = 'W'
        elif dd > 27 and dd < 32:
            wb = 'WNW'
        elif dd == 32:
            wb = 'NW'
        elif dd > 32 and dd < 36:
            wb = 'NNW'
        elif dd == 36:
            wb = 'N'
        #
        if short_form is True:
            return wb
        else:
            return long_form[wb]

    def wind_speed(self, speed: float) -> str:
        ''' Convert wind speed in km/h to m/s'''
        ws = speed * 1000 / 3600
        wind_speed = '{:.1f}'.format(ws)
        return wind_speed

    def today(self):
        attributes = self.get_attributes()
        speed = attributes['wind_speed']
        bearing = attributes['wind_bearing']
        forecast = 'Today, the weather forecast for Tanum is {} and the high temperature is {} degrees Celcius. ' \
                'The wind speed is {} meters per second from {}.'.format(self.state,attributes['temperature'], self.wind_speed(speed),
                                                                            self.bearing(bearing,False))
        return forecast

    def tomorrow(self):
        tomorrow = self.attributes['forecast']
        if len(tomorrow) > 0:
            forecast = tomorrow[0]
            date_time_str = forecast['datetime']
            d = self.convert_utc(date_time_str)
            day = d.weekday()
            weekday = calendar.day_name[day]
            speed = forecast['wind_speed']
            bearing = forecast['wind_bearing']
            the_forecast = 'Tomorrow, {}, the weather forecast  is {} and the high temperature is {} degrees Celcius. ' \
                        'The low temperature is {} degrees Celcius.' \
                        'The wind speed is {} meters per second from {}.'.format(weekday, forecast['condition'],
                    forecast['temperature'], forecast['templow'],self.wind_speed(speed), self.bearing(bearing,False))
            return the_forecast
        else:
            return 'No weather forecast'
