import sys

from cube2common.constants import message_types
from cube2protocol.cube_data_stream import CubeDataStream
from cube2protocol.read_cube_data_stream import ReadCubeDataStream
from cube2protocol.sauerbraten.collect.client_read_stream_protocol import sauerbraten_stream_spec
from cube2protocol.sauerbraten.collect.read_physics_state import read_physics_state


class ClientReadMessageProcessor(object):
    def process(self, channel, data):
        if len(data) == 0: return []

        if channel == 0:
            messages = self._parse_channel_0_data(data)
        elif channel == 1:
            messages = sauerbraten_stream_spec.read(data, {'aiclientnum':-1})
        else:
            return []
            print(channel)
            # ...  <cube int: port><cube str: domain><cube int: mode num><cube str: map name>
            cds = CubeDataStream(data)
            print((cds.getint()))
            print((cds.getint()))
            print((cds.getint()))
            print((cds.getint()))
            print((cds.getint()))

            print((cds.getstring()))

            print((cds.getbyte()))

            print((cds.getstring()))

            print((repr(data)))
            sys.exit(0)

        return messages

    def _parse_channel_0_data(self, data):
        cds = ReadCubeDataStream(data)
        message_type = cds.getint()

        if message_type == message_types.N_POS:
            cn = cds.getuint()

            physics_state = read_physics_state(cds)

            message = ('N_POS', {'clientnum': cn, 'physics_state': physics_state, 'raw_position': data})

        elif message_type == message_types.N_JUMPPAD:
            cn = cds.getint()
            jumppad = cds.getint()

            message = ('N_JUMPPAD', {'aiclientnum': cn, 'jumppad': jumppad})

        elif message_type == message_types.N_TELEPORT:
            cn = cds.getint()
            teleport = cds.getint()
            teledest = cds.getint()

            message = ('N_TELEPORT', {'aiclientnum': cn, 'teleport': teleport, 'teledest': teledest})

        return [message]
