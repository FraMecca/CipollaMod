import heapq

from typing import Optional

from cipolla.config_manager import ConfigManager

class ClientNumberProvider(object):
    def __init__(self, max_clients: int) -> None:
        self.cn_pool = list(range(max_clients))
        heapq.heapify(self.cn_pool)

    def acquire_cn(self) -> int:
        return heapq.heappop(self.cn_pool)

    def release_cn(self, cn: int) -> None:
        heapq.heappush(self.cn_pool, cn)

class ClientNumberHandle(object):
    def __init__(self, client_number_handle_provider: ClientNumberProvider) -> None:
        self._client_number_provider = client_number_handle_provider
        self.cn: Optional[int] = self._client_number_provider.acquire_cn()

    def release(self) -> None:
        if self.cn is None: return
        self._client_number_provider.release_cn(self.cn)
        self.cn = None

class ClientNumberHandleProvider(object):
    def __init__(self, client_number_handle_provider: ClientNumberProvider) -> None:
        self._client_number_provider = client_number_handle_provider

    def acquire_cn_handle(self) -> ClientNumberHandle:
        return ClientNumberHandle(self._client_number_provider)

def get_client_number_handle_provider() -> ClientNumberHandleProvider:
    # TODO: what for? Remove
    max_client_sum = 0
    for room in ConfigManager().rooms.values():
        max_client_sum += room.maxclients

    client_number_provider = ClientNumberProvider(max_client_sum)

    return ClientNumberHandleProvider(client_number_provider)
