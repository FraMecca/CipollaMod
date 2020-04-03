from cube2common.constants import disconnect_types


class RoomEntryFailure(Exception):
    disconnect_type = disconnect_types.DISC_NONE


class RoomEntryPermissionDenied(RoomEntryFailure):
    disconnect_type = disconnect_types.DISC_PRIVATE


class RoomEntryDeniedMaxClients(RoomEntryFailure):
    disconnect_type = disconnect_types.DISC_MAXCLIENTS

class UnknownEvent(Exception): pass
