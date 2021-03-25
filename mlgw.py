# mlgw listener

import appdaemon.plugins.hass.hassapi as hass


class MLGWListener(hass.Hass):

    def initialize(self):
        # Start listening for mlgw messages
        self.listen_event(self.receive_mlgw_msg, 'mlgw.ML_telegram')

    def receive_mlgw_msg(self, event_id, payload_event, *args):
        # Do something with the payload
        #keys = payload_event.keys()
        #dtype = data['type']
        #payload_type = data['payload_type']
        #payload = data['payload
        #from_device = payload_event['from_device']
        #to_device = payload_event['to_device']
        #dtype = payload_event['type']
        payload = payload_event['payload']
        #src_dest = payload_event['src_dest']
        #orig_src = payload_event['orig_src']
        #from_mln = payload_event['from_mln']
        size = len(payload)
        #source = payload['source']
        #activity = payload['activity']
        #source_medium = payload['source_medium']
        #sourceID= payload['sourceID']
        #track = payload['channel_track']
        msg =''
        #msg = 'From: '+ from_device +', '
        #msg = msg + 'To: ' + to_device +', '
        #msg = msg + 'Type: ' + dtype + ', '
        #msg = msg + 'Source dest: ' + ', '
        #msg = msg + 'Origin src: ' + ', '
        #msg = msg + 'From mln: ' + str(from_mln) + ', '
        #msg = msg + 'Payload size: ' + str(size) +', '
        #msg = msg + 'Source: ' + source +', '
        #msg = msg + 'Activity: ' + activity +', '
        #msg = msg + 'Source medium: ' + source_medium +', '
        #msg = msg + 'Track: ' + track + ', '
        #msg = msg + 'Source ID: '+ sourceID 
        for key in payload_event:
            msg = msg + key +': ' + str(payload_event[key]) +', '
        for key in payload:
            msg = msg + key +': ' + str(payload[key]) +', '
        msg = '<<< Payload size: ' + str(size) +', ' + msg + '>>>'
        self.log(msg)
 