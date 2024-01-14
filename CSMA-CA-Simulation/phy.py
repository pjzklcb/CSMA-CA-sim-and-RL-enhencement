import simpy
import math

import phyPacket
import parameters

class Phy(object):
    def __init__(self, mac):
        self.mac = mac
        self.env = self.mac.env
        self.name = self.mac.name
        self.ether = self.mac.ether
        self.latitude = self.mac.latitude
        self.longitude = self.mac.longitude
        self.listening = self.env.process(self.listen())
        self.receivingPackets = []
        self.isSending = False      # keep radio state (Tx/Rx)
        self.transmission = None    # keep the transmitting process


    def send(self, macPkt):
        if not self.isSending:  # I do not send if I'm already sending
            yield self.env.timeout(parameters.RADIO_SWITCHING_TIME) # RX -> TX
            self.listening.interrupt()
        
        self.transmission = self.env.process(self.encapsulateAndTransmit(macPkt))
        yield self.transmission

        # restore listening
        self.inChannel = self.ether.getInChannel(self)
        yield self.env.timeout(parameters.RADIO_SWITCHING_TIME) # TX -> RX
        if parameters.PRINT_LOGS:
            print('Time %d, %s: PHY starts listening' % (self.env.now, self.name))
        self.listening = self.env.process(self.listen())


    def encapsulateAndTransmit(self, macPkt):   # 封装和传输
        self.isSending = True
        phyPkt = phyPacket.PhyPacket(parameters.TRANSMITTING_POWER, False, macPkt) # start of packet

        if macPkt.ack:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY starts transmitting %s ACK' % (self.env.now, self.name, phyPkt.macPkt.id))
        else:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY starts transmitting %s' % (self.env.now, self.name, phyPkt.macPkt.id))
        self.ether.transmit(phyPkt, self.latitude, self.longitude, True, False) # beginOfPacket=True, endOfPacket=False

        duration = macPkt.length * parameters.BIT_TRANSMISSION_TIME + parameters.PHY_PREAMBLE_TIME
        duration = math.ceil(duration/parameters.SLOT_DURATION) * parameters.SLOT_DURATION  # round up to the nearest slot
        if parameters.PRINT_LOGS:
            print('Time %d, %s: PHY will finish transmitting at %d' % (self.env.now, self.name, self.env.now + duration))

        while True:
            if duration <= parameters.SLOT_DURATION:
                yield self.env.timeout(duration)    # wait only remaining time
                break
            yield self.env.timeout(parameters.SLOT_DURATION) # send a signal every slot
            self.ether.transmit(phyPkt, self.latitude, self.longitude, False, False)  # beginOfPacket=False, endOfPacket=False
            duration -= parameters.SLOT_DURATION

        yield self.ether.transmit(phyPkt, self.latitude, self.longitude, False, True)  # beginOfPacket=False, endOfPacket=True
        if macPkt.ack:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY ends transmitting %s ACK' % (self.env.now, self.name, phyPkt.macPkt.id))
        else:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY ends transmitting %s' % (self.env.now, self.name, phyPkt.macPkt.id))

        self.isSending = False


    def listen(self):
        self.inChannel = self.ether.getInChannel(self)
        yield self.env.timeout(parameters.RADIO_SWITCHING_TIME) # simulate time of radio switching
        if parameters.PRINT_LOGS:
            print('Time %d, %s: PHY starts listening' % (self.env.now, self.name))
        while True:
            try:
                (phyPkt, beginOfPacket, endOfPacket) = yield self.inChannel.get()
                # the signal just received will interfere with other signals I'm receiving (and vice versa)
                for receivingPkt in self.receivingPackets:
                    if receivingPkt != phyPkt:
                        # receivingPkt.interferingSignals[phyPkt.macPkt.id] = phyPkt.power
                        # phyPkt.interferingSignals[receivingPkt.vmacPkt.id] = receivingPkt.power
                        receivingPkt.corrupted = True
                        phyPkt.corrupted = True
                if endOfPacket and phyPkt.macPkt.destination == self.name:
                    if parameters.PRINT_LOGS:
                        print('Time %d, %s: PHY receives signal %s from %s with power %e' % (self.env.now, self.name, phyPkt.macPkt.id, phyPkt.macPkt.source, phyPkt.power))
                if self.mac.isSensing:  # interrupt mac if it is sensing for idle channel
                    self.mac.sensing.interrupt()
                if phyPkt.power > parameters.RADIO_SENSITIVITY: # decodable signal
                    if beginOfPacket:  # begin of packet
                        self.receivingPackets.append(phyPkt)
                    elif endOfPacket:   # end of packet
                        if phyPkt in self.receivingPackets:
                            self.receivingPackets.remove(phyPkt)
                            if not phyPkt.corrupted:
                                self.env.process(self.mac.handleReceivedPacket(phyPkt.macPkt))
                            else:
                                if parameters.PRINT_LOGS:
                                    print('Time %d, %s: %s collisioned' % (self.env.now, self.name, phyPkt.macPkt.id))

            except simpy.Interrupt:        # listening can be interrupted by a message sending
                if parameters.PRINT_LOGS:
                    print('Time %d, %s: PHY stops listening' % (self.env.now, self.name))
                self.ether.removeInChannel(self.inChannel, self)
                self.receivingPackets.clear()   # switch to TX mode, so drop all ongoing receptions
                return


    # def computeSinr(self, phyPkt):
    #     interference = 0
    #     for interferingSignal in phyPkt.interferingSignals:
    #         interference += float(phyPkt.interferingSignals[interferingSignal])
    #     return phyPkt.power/(interference + parameters.NOISE_FLOOR)
