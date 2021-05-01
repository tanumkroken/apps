# Tanumkroken bot
import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime


class TelegramBot(hass.Hass):

    def initialize(self):
        # Start listening for Telegram updates
        self.listen_event(self.receive_telegram_text, 'telegram_text')
        self.time_between_conversations = 60 * 60
        self.last_conversation = {}


    def receive_telegram_text(self, event_id, payload_event, *args):
        # Do something with the text
        user_id = payload_event['user_id']
        message = payload_event['text']
        self.greet_user_if_new_conversation(user_id, payload_event['from_first'])


    def greet_user_if_new_conversation(self, user_id, user_name):
        """Say hi when there is a new conversation"""
        # For new users automatically set the time to zero.
        if user_id not in self.last_conversation:
            self.last_conversation[user_id] = 0
        # Compute the time difference in seconds since the last message.
        time_diff = time.time() - self.last_conversation[user_id]
        if time_diff > self.time_between_conversations:
            msg = f"Hi {user_name}"
            # Send a message to the user.
            self.call_service('telegram_bot/send_message',
                            target=user_id,
                            message=msg)
        self.last_conversation[user_id] = time.time()


    def ruter(self, message, user_id):
        ruter = self.get_app('transportation')
        departures = ruter.queryNextDeparturesFromYourLocalStop()
        now = datetime.now()
        self.log(now, ascii_encode=False)
        msg = ''
        for call in departures:
            call_time =  self.convert_utc(call)
            self.log(call_time)
            self.log(str(departures[call]), ascii_encode=False)
            msg = 'The next bus leaves at {} towards {}'.format(call_time, departures[call][0]['destination'])
            break
        self.call_service('telegram_bot/send_message',
                          target=user_id,message=msg)
        return