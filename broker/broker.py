# -*- coding: utf-8 -*-
# The skills broker
from requests import exceptions, HTTPError
import json
from skills import GQLClient
import appdaemon.plugins.hass.hassapi as hass
from collections import defaultdict


class Broker(hass.Hass):
    ''' The skills broker class'''

    def initialize(self):
        ''' Broker initialisation'''
        self.skill_callback = defaultdict(list)
        self.listen_event(self.receive_telegram_text, 'telegram_text')
        URL = self.args['gql_server'] # The NLP server
        header = {}
        self.gql_client = GQLClient(URL,header)
        if self.args['logging'] is True:
            self.log('Module ' + self.name + ' was initialized', ascii_encode=False)
            self.log('Initialized GQL client for {}'.format(URL), ascii_encode=False)

    def register_call_back(self, sign: str, cb):
        ''' Register a skill set '''
        self.skill_callback[sign] = cb # sign is the call-back signature on the form "<app name>/<method>
        if self.args['logging'] is True:
            self.log('Registered call back for app: ' + sign)

    def call_skill_service(self, service, kwargs) -> str:
        ''' Call a registered service '''
        response = 'No service'
        if service in self.skill_callback:
            cb = self.skill_callback[service]
            response = self.call_service(cb,kwargs)
        return response

    def receive_telegram_text(self, event_id, payload_event, *args):
        # Do something
        user_id = payload_event['user_id']
        message = payload_event['text']
        self.log('broker, received telegram text: ' + message, ascii_encode=False)
        query = self.match(message)
        data = self.gql_client.execute(query)
        if self.args['logging'] is True:
            if self.gql_client.is_success() is True:
                self.log('Successfully got match on skill ' + str(data), ascii_encode=False)
            else:
                self.log('No success on match '+ str(data) + ' Error: ' + self.gql_client.get_error(),
                         ascii_encode=False)
            self.log('Response:' + str(data))
        response = 'Sorry, no answer'
        if self.gql_client.is_success() is True:
            call_back = data['call_back']
            if call_back in self.skill_callback:
                method = self.skill_callback[call_back]
                response = method()
        self.call_service('telegram_bot/send_message',
                                 target=user_id,message=response)
        return


    def match(self, text):
        query = '''query{match_skill(sentence: "msg")
          {
          domain
          call_back
            success
            errors
            sentence
          }
        }'''
        q =  query.replace('msg',text)
        if self.args['logging'] is True:
            self.log('Query: ' + q, ascii_encode=False)
        return q


    def find_in_obj(self, obj, condition, path=None):

        if path is None:
            path = []

        # In case this is a list
        if isinstance(obj, list):
            for index, value in enumerate(obj):
                new_path = list(path)
                new_path.append(index)
                for result in self.find_in_obj(value, condition, path=new_path):
                    yield result

        # In case this is a dictionary
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = list(path)
                new_path.append(key)
                for result in self.find_in_obj(value, condition, path=new_path):
                    yield result

                if condition == key:
                    new_path = list(path)
                    new_path.append(key)
                    yield new_path
