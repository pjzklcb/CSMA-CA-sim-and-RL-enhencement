class PhyPacket(object):
    def __init__(self, power, endTime, macPkt):
        self.power = power
        self.corrupted = False
        self.macPkt = macPkt
        self.interferingSignals = {}
        self.endTime = endTime  # expected end time of transmission
