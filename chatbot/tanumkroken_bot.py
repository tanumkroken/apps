# Tanumkroken bot
import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime

from utilities import Logger
import appdaemon.plugins.hass.hassapi as hass
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.dsl import  DSLSchema, DSLType, dsl_gql, DSLField, DSLMutation, DSLQuery
from graphql.error import GraphQLSyntaxError



class QuerySkill:
    ''' Builds a valid GraphQL query using the gql DSL module'''
    def __init__(self, url: str, logger, log_level: str):
        self.url = url
        self.log = Logger(logger, log_level)
        self.err  = [] # List of  errors
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

    def ask_jeeves(self, user_name: str, sentence: str):
        ''' Args:
            ----
            sentence: the user request to be parsed by the nlp
        '''
        response = {}
        ds = DSLSchema(self.client.schema)
        query = dsl_gql(DSLQuery(
            ds.Query.ask_jeeves.args(user=user_name, sentence=sentence).select(
                ds.Response)))
        if query is not None:
            self.log.debug('Ask Jeeves: ' + sentence + ' Result: ' + str(query['data']))
            response = query['data']
        return response

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

class TelegramBot(hass.Hass):

    def initialize(self):
        # Set the apps log level:
        if 'log_level' in self.args:
            self.log_level = self.args['log_level']
        else:
            self.log_level = 'INFO'
        logger = self.log
        self.log = Logger(logger, self.log_level)
        # Start listening for Telegram updates
        self.listen_event(self.receive_telegram_text, 'telegram_text')
        self.time_between_conversations = 60 * 60
        self.last_conversation = {}
        self.url = self.args['gql_server'] # The Jeeves URL
        self.jeeves = QuerySkill(self.url,logger, self.log_level)


    def receive_telegram_text(self, event_id, payload_event, *args):
        # Do something with the text
        user_id = payload_event['user_id']
        message = payload_event['text']
        user_name = payload_event['user_name']
        self.ask_jeeves(user_id, user_name, message)


    def ask_jeeves(self, user_id: str, user_name: str, message: str) -> dict:
        """
            Executes a query from a query string.
            The query is verified locally before the request is sent to the server
        """
        payload = {}
        try:
            payload = self.jeeves.ask_jeeves(user_name, message)
            if payload is not None:
                success = True
            else:
                self.log.error(f'No response from server {self.url}')
        except GraphQLSyntaxError as err:
            self.log.error('Syntax error in query: ' + err.message)
        for msg in payload:
            self.call_service('telegram_bot/send_message',
                      target=user_id,message=msg)
