# -*- coding: utf-8 -*-
# The skills classes

import appdaemon.plugins.hass.hassapi as hass
import arrow
import datetime
import logging
from collections import defaultdict
from flatten_dict import flatten

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.dsl import  DSLSchema, DSLType, dsl_gql, DSLField, DSLMutation
from graphql.error import GraphQLSyntaxError




TEST_ENV = False # False when the class is instantiated under appdaemon



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

class Logger:
    def __init__(self, logger):
        self.log = logger

    def info(self, msg):
        if not TEST_ENV:
            self.log(msg, level = 'INFO', ascii_encode=False)
        else:
            self.log.info(msg)
        return

    def error(self, msg):
        if not TEST_ENV:
            self.log(msg, level = 'ERROR', ascii_encode=False)
        else:
            self.log.error(msg)
        return

    def debug(self, msg):
        if not TEST_ENV:
            self.log(msg, level = 'DEBUG', ascii_encode=False)
        else:
            self.log.debug(msg)
        return

    def warning(self, msg):
        if not TEST_ENV:
            self.log(msg, level = 'WARNING', ascii_encode=False)
        else:
            self.log.warning(msg)
        return


class SkillBroker:
    ''' The skill register class implements a GraphQL client
        to register a skill with the natural language server '''
    def __init__(self, url: str, logger):
        self.url = url
        self.log = Logger(logger)
        self.err  = [] # List of  errors
        self.log.info('Initialize SkillBroker')
        transport = RequestsHTTPTransport(url = url)
        # Create the GraphQL client using the defined transport and fetch the schema
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.log.info(f'Registered qql client with server {self.url}')
        # Query the server for the schema:
        introspection = '''query IntrospectionQuery {
            __schema {
            types {
            kind
        name
        description
        }
        }
        }'''
        result = self.execute_query_from_str(introspection)
        # Verify that the schema was fetched
        if self.client.schema is None:
            self.log.error('The server did not provide a schema when initializing the client')

    def register_skill(self, mutation):
        '''Executes the mutation to register a skill.
            The query is verified locally before the request is sent to the server'''
        success = False
        result = {}
        try:
            payload = self.client.execute(mutation)
            if payload is not None:
                # Pack out the dict
                result = list(payload.values())[0]
                if result['success'] is True:
                    self.log.debug('Successfully registered skill')
                    success = True
                else:
                    self.log.error(f'Error registering skill.')
        except GraphQLSyntaxError as err:
            self.log.error('Syntax error in query: ' +  err.message)
        return success, result

    def execute_query_from_str(self, query_str: str)->dict:
        '''Executes a query from a query string.
            The query is verified locally before the request is sent to the server'''
        query = gql(query_str)
        payload = {}
        try:
            payload = self.client.execute(query)
            if payload is not None:
                success = True
            else:
                self.log.error(f'No response from server {self.url}')
        except GraphQLSyntaxError as err:
            self.log.error('Syntax error in query: ' + err.message)
        return payload


class QueryBuilder:
    ''' Builds a valid query using the gql DSL module'''
    def __init__(self, client: Client):
        self.client = client

    def mutation_skill(self, domain: str, call_back:str, lang: str,  matchers: list):
        ''' Args:
            ----
            call_back: the callback method registered as <domain>/<method>
            lang: The language iso code
            matchers: A list of Matcher rules on the form [{'ORTH': "vær", 'OP': "?"},
                                                           {'ORTH': "været", 'OP': "?"}]
        '''
        ds = DSLSchema(self.client.schema)
        mutation = dsl_gql(DSLMutation(
            ds.Mutation.register_skill.args(domain=domain, call_back=call_back,lang=lang,matcher=matchers).select(
                ds.MatcherResponse.success, ds.MatcherResponse.errors, ds.MatcherResponse.domain,
                ds.MatcherResponse.errors, ds.MatcherResponse.lang, ds.MatcherResponse.call_back)))
        return mutation

    def mutation_domain(self, domain:str, lang: str, phrases: list):
        ds = DSLSchema(self.client.schema)
        mutation = dsl_gql(DSLMutation(
            ds.Mutation.register_domain.args(domain=domain,lang=lang,phrases=phrases).select(
                ds.MatcherResponse.success, ds.MatcherResponse.errors, ds.MatcherResponse.domain,
                ds.MatcherResponse.errors, ds.MatcherResponse.lang)))
        return mutation


class SkillBase:
    ''' The base skill class
        Boilerplate class from which all skills must inherit
        Decorate your internal methods with a _ prefixe
        Non-decorated methods will be exposed through the get_skills() method' as a list of  methods'''
    def __init__(self, domain: str, url: str, logger):
        self.log = Logger(logger)
        self.domain = domain
        self.skill = SkillBroker(url,logger)
        self.url = url

    def _register_skill(self, call_back: str, lang: str, matchers: list):
        qb = QueryBuilder(self.skill.client)
        mutation = qb.mutation_skill(self.domain, call_back, lang, matchers)
        success, payload = self.skill.register_skill(mutation)
        if success is True:
            if 'success' in payload:
                call_back = payload['call_back']
                lang = payload['lang']
                self.log.info(f'Successfully registered callback {call_back} for language {lang}')
            else:
                self.log.error(f'Error registering {call_back} for language {lang} with phrases: {matchers}')
        else:
            self.log.error(f'No response from skill server {self.url}')
        return success

    def _register_domain(self, lang: str, phrases: list)->bool:
        qb = QueryBuilder(self.skill.client)
        mutation = qb.mutation_domain(self.domain,lang,phrases)
        success, payload = self.skill.register_skill(mutation)
        if success is True:
            if 'success' in payload:
                domain = payload['domain']
                lang = payload['lang']
                self.log.info(f'Successfully registered domain {domain} for language {lang}')
            else:
                self.log.error(f'Error registering {self.domain} for language {lang} with phrases: {phrases}')
        else:
            self.log.error(f'No response from skill server {self.url}')
        return success

    def _get_skills(self):
        ''' The return the available skills for the skill class inheriting from this the SkillBase'''
        method_list = []
        # attribute is a string representing the attribute name
        for attribute in dir(self):
            # Get the attribute value
            attribute_value = getattr(self, attribute)
            # Check that it is callable
            if callable(attribute_value):
                # Filter all dunder (__ prefix) methods
                if not attribute.startswith('__'):
                    if not attribute.startswith('_'):
                        if 'initialize' not in attribute:
                            method_list.append(attribute)
        return method_list

    def _register_all_skills(self, skills):
        for method in skills:
            call_back = self.domain +'/' + method
            matcher = getattr(self, '_matcher_' + method)
            try:
                callable(matcher)
                matchers = matcher()
                for lang in matchers:
                    self._register_skill(call_back,lang,matchers[lang])
            except TypeError as err:
                self.log.error(f'Missing Matcher for skill method {method} for domain {self.domain}. Error: {err}')
        return

    def _domain(self):
        ''' Return the skill domain. Must be unique for each skill '''
        return self.domain

    def _get_skill(self, skill: str, **kwargs)->list:
        ''' The generic getter method for calling a skill
            If a method require an input it can bee supplied in the **kwargs
            An unknown skill will return ["Unknown skill"] '''
        method = getattr(self, skill, self._unknown)
        result = []
        try:
            result = method(kwargs)
        except TypeError as err:
            print(err)
        return result

    def _unknown(self, kwargs):
        return ['Unknown skill']

class Weather(SkillBase):
    ''' The weather skills '''
    def __init__(self, gql_url:str, domain: str, logger):
        super().__init__(domain, gql_url, logger)

    def initialize(self):
        # Implement the callback interface that AD expects
        # Store the state value
        self.state = self.args['state']
        # Store the attribute values
        self.attributes = self.args['attributes']
        self.forecast = self.__to_dict()
        skills = self._get_skills()
        self._register_all_skills(skills)


    def _set_args(self, args: dict):
        self.args = args

    def __bearing(self, bearing: float, short_form: True) -> str:
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

    def __wind_speed(self, speed: float) -> str:
        ''' Convert wind speed in km/h to m/s'''
        ws = speed * 1000 / 3600
        wind_speed = '{:.1f}'.format(ws)
        return wind_speed

    def __to_dict(self):
        ''' Schema:
            dict of key: (value, unit) pairs'''

        a = self.attributes
        schema = {}
        schema['today'] = {'condition': (self.state,''), 'temperature': (a['temperature'],'degree Celsius'),
                           'humidity': (a['humidity'], 'percent'),
                           'wind speed': (self.__wind_speed(a['wind_speed']),'meter per second'),
                           'bearing': (self.__bearing(a['wind_bearing'], False),'')}
        forecast = self.attributes['forecast']
        for a in forecast:
            dt = DateTimeConverter(a['datetime'])
            schema[dt.day()] = {'condition': (a['condition'],''), 'temperature': (a['temperature'],'degree Celsius'),
                                'night temperature': (a['templow'],'degree Celsius'),
                                'precipitation': (a['precipitation'],'milli meter'),
                                'probability for rain': (a['precipitation_probability'], 'percent'),
                                'wind speed': (self.__wind_speed(a['wind_speed']),' meter per second'),
                                'bearing': (self.__bearing(a['wind_bearing'], False),'')}
        return schema

    def _matcher_forecast_today(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'LEMMA': "vær", 'OP': "+"},
            {'ORTH': "idag", 'OP': "+"}
        ]
        matcher['en'] = [
            {'ORTH': "weather", 'OP': "?"},
            {'ORTH': "forecast", 'OP': "?"},
            {'ORTH': "today", 'OP': "+"}
        ]
        return matcher

    def forecast_today(self, kwargs)->list:
        day = 'today'
        f = self.forecast[day]
        result = []
        i = 0
        for key in f:
            value, unit = f[key]
            if i == 0:
                result.append('The {} {} is {} {}'.format(key, day, value, unit))
            else:
                result.append('The {} is {} {}'.format(key, value, unit))
            i += 1
        return result

    def _matcher_forecast_tomorrow(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'LEMMA': "vær", 'OP': "+"},
            {'ORTH': "imorgen", 'OP': "+"}
        ]
        matcher['en'] = [
            {'ORTH': "weather", 'OP': "?"},
            {'ORTH': "forecast", 'OP': "?"},
            {'ORTH': "tomorrow", 'OP': "+"}
        ]
        return matcher

    def forecast_tomorrow(self, kwargs)->list:
        day = DateTimeConverter().tomorrow()
        result = []
        if day in self.forecast:
            f = self.forecast[day]
            i = 0
            for key in f:
                value, unit = f[key]
                if i == 0:
                    result.append('The {} for {} is {} {}'.format(key, day, value, unit))
                else:
                    result.append('The {} is {} {}'.format(key, value, unit))
                i += 1
        else:
            result.append('I am so sorry, there is no forecast available for {}'.format(day))
        return result

    def _matcher_chance_of_frost(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'LEMMA': "frost", 'OP': "?"},
            {'LEMMA': "nattefrost", 'OP': "?"}
        ]
        matcher['en'] = [
            {'LEMMA': "freeze", 'OP': "?"},
            {'ORTH': "frost", 'OP': "?"}
        ]
        return matcher

    def chance_of_frost(self, kwargs)->list:
        temps = []
        for day in self.forecast:
            temps.append((day, self.forecast[day]['temperature'][0]))
        min_t = min(temps, key = lambda t: t[1])
        if min_t[1] <= 0:
            result = '{} there is a chance of frost with a low temperature of {} degree Celsius'
        else:
            result = 'There is no chance of frost the coming days'
        return [result]

    def _matcher_chance_of_high_wind(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'LEMMA': "blåse", 'OP': "?"},
            {'LEMMA': "vind", 'OP': "?"},
        ]
        matcher['en'] = [
            {'ORTH': "windy", 'OP': "?"},
            {'ORTH': "wind", 'OP': "?"},
        ]
        return matcher

    def chance_of_high_wind(self, kwargs):
        wind = []
        for day in self.forecast:
            if day != 'today':
                wind.append((day, self.forecast[day]['wind speed'][0]))
        w = min(wind, key = lambda t: t[1])
        result = 'On {} the high wind is {} meter per second from {}'.format(w[0],w[1], self.forecast[w[0]]['bearing'][0])
        return [result]

    def _matcher_forecast_on_day(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'LEMMA': "vær", 'OP': "?"},
            {'ORTH': "mandag", 'OP': "?"},
            {'ORTH': "tirsdag", 'OP': "?"},
            {'ORTH': "onsdag", 'OP': "?"},
            {'ORTH': "torsdag", 'OP': "?"},
            {'ORTH': "fredag", 'OP': "?"},
            {'ORTH': "lørdag", 'OP': "?"},
            {'ORTH': "søndag", 'OP': "?"},
        ]
        matcher['en'] = [
            {'ORTH': "forecast", 'OP': "?"},
            {'ORTH': "weather", 'OP': "?"},
            {'ORTH': "Monday", 'OP': "?"},
            {'ORTH': "Tuesday", 'OP': "?"},
            {'ORTH': "Wednesday", 'OP': "?"},
            {'ORTH': "Thursday", 'OP': "?"},
            {'ORTH': "Friday", 'OP': "?"},
            {'ORTH': "Saturday", 'OP': "?"},
            {'ORTH': "Sunday", 'OP': "?"},
        ]
        return matcher
    def forecast_on_day(self, kwargs):
        try:
            day = kwargs['day']
        except KeyError as err:
            day = '<Day missing>'
            print(err)
        result = []
        if day in self.forecast:
            f = self.forecast[day]
            i = 0
            for key in f:
                value, unit = f[key]
                if i == 0:
                    result.append('The {} for {} is {} {}'.format(key, day, value, unit))
                else:
                    result.append('The {} is {} {}'.format(key, value, unit))
                i += 1
        else:
            result.append('I am so sorry, there is no forecast available for {}'.format(day))
        return result

    def _matcher_forecast_for_weekend(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'ORTH': "vær", 'OP': "?"},
            {'ORTH': "vøret", 'OP': "?"},
            {'ORTH': "helgen", 'OP': "?"}]
        matcher['en'] = [
            {'ORTH': "forecast", 'OP': "?"},
            {'ORTH': "weekend", 'OP': "?"}]
        return matcher

    def forecast_for_weekend(self, kwargs):
        day = 'Saturday'
        result = []
        if day in self.forecast:
            f = self.forecast[day]
            i = 0
            for key in f:
                value, unit = f[key]
                if i == 0:
                    result.append('The {} for {} is {} {}'.format(key, day, value, unit))
                else:
                    result.append('The {} is {} {}'.format(key, value, unit))
                i += 1
        else:
            result.append('I am so sorry, there is no forecast available for {}'.format(day))
        return result

    def _matcher_temperature_today(self)->list:
        matcher = defaultdict(list)
        matcher['no'] = [
            {'ORTH': "temperatur", 'OP': "?"},
            {'ORTH': "temperaturen", 'OP': "?"},
            {'ORTH': "idag", 'OP': "?"}]
        matcher['en'] = [
            {'ORTH': "temperature", 'OP': "?"},
            {'ORTH': "today", 'OP': "?"}]
        return matcher

    def temperature_today(self, kwargs)->list:
        t = self.forecast['today']['temperature']
        return ['The outdoor temperature today is {} {}'.format(t[0],t[1])]

    def _matcher_temperature_tomorrow(self):
        matcher = defaultdict(list)
        matcher['no'] = [
            {'ORTH': "temperatur", 'OP': "?"},
            {'ORTH': "temperaturen", 'OP': "?"},
            {'ORTH': "imorgen", 'OP': "?"}]
        matcher['en'] = [
            {'ORTH': "temperature", 'OP': "?"},
            {'ORTH': "tomorrow", 'OP': "?"}]
        return matcher

    def temperature_tomorrow(self, kwargs)->list:
        tomorrow = DateTimeConverter().tomorrow()
        t = self.forecast[tomorrow]['temperature']
        return ['The outdoor temperature forecast for tomorrow is {} {}'.format(t[0],t[1])]

class Yr(hass.Hass):
    ''' The forecast from Met.no '''

    def initialize(self):
        entity = self.args['entity'] # The event to listen to
        url = self.args['gql_server'] # The skill server url
        domain = self.args['domain'] # The skill domain
        logger = self.log
        self.weather = Weather(url,domain, logger)
        # For state callbacks, a class defined callback function should look like this:
        # def my_callback(self, entity, attribute, old, new, kwargs)
        self.update(entity, None, None, None,None)
        self.listen_state(self.update,entity)
        # Get the yr state
        args = self.get_state(entity, "all")
        self.weather._set_args(args)
        # Initialize the instance
        self.weather.initialize()

    def update(self, entity, attribute, old, new, kwargs):
        ''' The abstract callback for state-ful classes
            entity:     The name of the entity the call-back was requested for.
            attribute:  The name of the attribute the call-back was requested for.
            old:        The value of the state before the state change.
            new:        The value of the state after the state change.
            kwargs:     A dictionary containing any constraints and/or additional user specific keyword arguments
                        supplied to the listen_state() call.
        '''
        args = self.get_state(entity, "all")
        self.weather._set_args(args)




