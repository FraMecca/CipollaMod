from cube2protocol.cube_data_stream import CubeDataStream
from cipolla.protocol import swh

EXT_ACK = -1
EXT_VERSION = 105
EXT_NO_ERROR = 0
EXT_ERROR = 1
EXT_PLAYERSTATS_RESP_IDS = -10
EXT_PLAYERSTATS_RESP_STATS = -11
EXT_UPTIME = 0
EXT_PLAYERSTATS = 1
EXT_TEAMSCORE = 2

def get_ext_info_reply_cds(rcds):
    cds = CubeDataStream()

    cds.write(rcds.data)

    cds.putint(EXT_ACK)
    cds.putint(EXT_VERSION)

    return cds

class LanInfoResponder(object):
    def __init__(self, lan_info_protocol, room):
        self.lan_info_protocol = lan_info_protocol
        self.room = room

    def info_request(self, address, millis):
        cds = CubeDataStream()
        cds.putint(millis)

        swh.put_info_reply(
            cds,
            self.room.lan_info_name,
            self.room.player_count,
            self.room.maxplayers,
            self.room.mode_num,
            self.room.map_name,
            self.room.timeleft,
            self.room.mastermask,
            self.room.is_paused,
            100)

        self.respond(bytes(cds), address)

    def ext_info_request(self, address, rcds):
        cmd = rcds.getint()

        if cmd == EXT_UPTIME:
            if not rcds.empty(): return
            self.ext_uptime_request(address, rcds)
        elif cmd == EXT_PLAYERSTATS:
            cn = rcds.getint()
            if not rcds.empty(): return
            self.ext_player_stats_request(address, rcds, cn)
        elif cmd == EXT_TEAMSCORE:
            if not rcds.empty(): return
            self.ext_team_stats_request(address, rcds)
        else:
            if not rcds.empty(): return
            self.ext_error(address, rcds)

    def ext_uptime_request(self, address, rcds):
        cds = get_ext_info_reply_cds(rcds)

        cds.putint(1337)

        self.respond(bytes(cds), address)

    def ext_player_stats_request(self, address, rcds, pn):
        player = self.get_player(pn) if pn > 0 else None

        if player is None:
            players = list(self.get_players(address))
        else:
            players = [player]

        self.ext_send_player_ids(address, rcds, players)
        for player in players:
            self.ext_send_player_stats(address, rcds, player)

    def ext_send_player_ids(self, address, rcds, players):
        cds = get_ext_info_reply_cds(rcds)

        cds.putint(EXT_NO_ERROR)

        cds.putint(EXT_PLAYERSTATS_RESP_IDS)

        for player in players:
            cds.putint(player.pn)

        self.respond(bytes(cds), address)

    def ext_send_player_stats(self, address, rcds, player):
        cds = get_ext_info_reply_cds(rcds)

        cds.putint(EXT_NO_ERROR)

        cds.putint(EXT_PLAYERSTATS_RESP_STATS)

        cds.putint(player.pn)
        cds.putint(player.ping)
        cds.putstring(player.name)
        cds.putstring(player.teamname)
        cds.putint(player.state.frags)
        cds.putint(player.state.flags)
        cds.putint(player.state.deaths)
        cds.putint(player.state.teamkills)
        cds.putint(player.state.acc_percent_int)
        cds.putint(player.state.health)
        cds.putint(player.state.armour)
        cds.putint(player.state.gunselect)
        cds.putint(player.privilege)
        cds.putint(player.state.state)

        ip = player.client.host
        octs = ip.split('.')[:3]
        for i in range(3):
            cds.putbyte(int(octs[i])) # send 0 if don't wanna send ips

        self.respond(bytes(cds), address)

    def ext_team_stats_request(self, address, rcds):
        cds = get_ext_info_reply_cds(rcds)

        # TODO: send teamscores correctly
        # cds.putint(self.room.is_teammode)
        cds.putint(0)
        cds.putint(self.room.mode_num)
        cds.putint(self.room.timeleft)

        # if self.room.is_teammode:
        #    pass

        self.respond(bytes(cds), address)

    def ext_error(self, address, rcds):
        cds = get_ext_info_reply_cds(rcds)

        cds.putint(EXT_ERROR)

        self.respond(bytes(cds), address)

    def respond(self, data, address):
        self.lan_info_protocol.send(data, address)

    def get_player(self, pn):
        return self.room.get_player(pn)

    def get_players(self, address):
        """
        Find if there is a room containing a client with this address.
        If there is then return the clients in that room. Otherwise,
        return the clients in the room which is associated with this
        responder.
        """
        room = None

        # room = self.room_manager.find_room_for_client_ip(address[0])
        # TODO maybe remove method

        if room is None:
            room = self.room

        return room.players
