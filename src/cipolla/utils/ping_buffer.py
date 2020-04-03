from typing import List

class PingBuffer(object):
    BUFFERSIZE = 15
    def __init__(self) -> None:
        self.pings: List[int] = []
    
    def add(self, ping: int) -> None:
        self.pings.append(ping)
        if len(self.pings) > self.BUFFERSIZE:
            self.pings.pop(0)
            
    def avg(self):
        return float(sum(self.pings)) / max(len(self.pings), 1)
