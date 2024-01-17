import simpy
import math
from scipy.constants import c, pi
import random

import parameters

class Ether(object):
    def __init__(self, env, capacity=simpy.core.Infinity):
        self.env = env
        self.capacity = capacity
        self.channels = []
        self.listeningNodes = []
        self.txPackets = []


    def computeDistance(self, senderLatitude, senderLongitude, receiverLatitude, receiverLongitude):
        return math.sqrt(pow(senderLatitude - receiverLatitude, 2) + pow(senderLongitude - receiverLongitude, 2))


    def latencyAndAttenuation(self, phyPkt, srcLatitude, srcLongitude, dstChannel, dstNode, beginOfPacket, endOfPacket):
        # 延迟和衰减
        # distance = self.computeDistance(srcLatitude, srcLongitude, dstNode.latitude, dstNode.longitude) + 1e-3 # add 1mm to avoid distance=0
        # delay = round((distance / c) * pow(10, 9), 0)
        # receivingPower = parameters.TRANSMITTING_POWER * pow(parameters.WAVELENGTH/(4 * pi * distance), 2) # NB. used FSPL propagation model with isotropic antennas
        delay, receivingPower = 0, 1e-7   # ignore propagation loss and delay
        phyPkt.power = receivingPower
        yield self.env.timeout(delay)

        return dstChannel.put((phyPkt, beginOfPacket, endOfPacket))


    def transmit(self, phyPkt, srcLatitude, srcLongitude, beginOfPacket, endOfPacket):
        events = [self.env.process(self.latencyAndAttenuation(phyPkt, srcLatitude, srcLongitude, dstChannel, dstNode, beginOfPacket, endOfPacket)) for dstChannel, dstNode in zip(self.channels, self.listeningNodes)]
        if beginOfPacket:
            self.txPackets.append(phyPkt)
        elif endOfPacket:
            self.txPackets.remove(phyPkt)
        return self.env.all_of(events)


    def getInChannel(self, node):
        channel = simpy.Store(self.env, capacity=self.capacity)
        self.channels.append(channel)
        self.listeningNodes.append(node)
        return channel


    def removeInChannel(self, inChannel, node):
        self.channels.remove(inChannel)
        self.listeningNodes.remove(node)

