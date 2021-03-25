# Tanumkroken bot
import appdaemon.plugins.hass.hassapi as hass
import time


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
        if 'temperature' in message:
            # Report the temperature
            self.send_outside_temperature(user_id)
        elif 'weather' in message and 'today' in message:
            self.send_today_weather(user_id)
        elif 'tomorrow' in message:
            self.send_tomorrow_weather(user_id)
        else:
            msg = 'I did not get that'
            self.call_service('telegram_bot/send_message',
                target=user_id, message=msg)


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

    def send_outside_temperature(self, user_id):
        """Send information about today temperature forecast"""
        # Get the weather app
        weather = self.get_app('weather_yr')
        t = weather.get_today_temperature()
        msg = 'The outside temperature is {}'.format(t)
        self.call_service('telegram_bot/send_message', target=user_id,message=msg)

    def send_today_weather(self, user_id):
        weather = self.get_app('weather_yr')
        msg = weather.today()
        self.call_service('telegram_bot/send_message',
            target=user_id,message=msg)

    def send_tomorrow_weather(self, user_id):
        weather = self.get_app('weather_yr')
        msg = weather.tomorrow()
        self.call_service('telegram_bot/send_message',
            target=user_id,message=msg)

