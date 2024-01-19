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
        self.TX = None    # keep the transmitting process


    def send(self, macPkt):
        if not self.isSending:  # I do not send if I'm already sending
            yield self.env.timeout(parameters.RADIO_SWITCHING_TIME) # RX -> TX
            self.listening.interrupt()
        
        self.TX = self.env.process(self.encapsulateAndTransmit(macPkt))
        yield self.TX

        # restore listening
        yield self.env.timeout(parameters.RADIO_SWITCHING_TIME) # TX -> RX
        self.listening = self.env.process(self.listen())


    def encapsulateAndTransmit(self, macPkt):   # 封装和传输
        self.isSending = True

        duration = macPkt.length * parameters.BIT_TRANSMISSION_TIME + parameters.PHY_PREAMBLE_TIME
        duration = math.ceil(duration/parameters.SLOT_DURATION) * parameters.SLOT_DURATION  # round up to the nearest slot

        phyPkt = phyPacket.PhyPacket(parameters.TRANSMITTING_POWER, self.env.now+duration, macPkt) # framing PHY packet

        if macPkt.ack:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY starts transmitting %s ACK' % (self.env.now, self.name, phyPkt.macPkt.id))
        else:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: PHY starts transmitting %s' % (self.env.now, self.name, phyPkt.macPkt.id))
        self.ether.transmit(phyPkt, self.latitude, self.longitude, True, False) # beginOfPacket=True, endOfPacket=False

        
        if parameters.PRINT_LOGS:
            print('Time %d, %s: PHY will finish transmitting at %d' % (self.env.now, self.name, self.env.now + duration))
        yield self.env.timeout(duration)

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

        for packet in self.ether.txPackets:
            if packet.power > parameters.RADIO_SENSITIVITY: # decodable signal
                packet.corrupted = True
                self.receivingPackets.append(packet)

        while True:
            try:
                (phyPkt, beginOfPacket, endOfPacket) = yield self.inChannel.get()
                
                if phyPkt.power > parameters.RADIO_SENSITIVITY: # decodable signal
                    if beginOfPacket:  # begin of packet
                        self.receivingPackets.append(phyPkt)
                        # Interrupt MAC if it is sensing for IDLE channel
                        if self.mac.isSensing:  
                            self.mac.sensing.interrupt(phyPkt.endTime)
                    elif endOfPacket:   # end of packet
                        for receivingPkt in self.receivingPackets:
                            if receivingPkt != phyPkt:
                                receivingPkt.corrupted = True
                                phyPkt.corrupted = True
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
