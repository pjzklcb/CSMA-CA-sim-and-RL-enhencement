import simpy
import random

import phy
import macPacket
import parameters
import stats

class Mac(object):
    def __init__(self, node):
        self.node = node
        self.env = self.node.env
        self.name = self.node.name
        self.ether = self.node.ether
        self.latitude = self.node.latitude
        self.longitude = self.node.longitude
        self.stats = self.node.stats
        self.phy = phy.Phy(self)
        self.send = self.env.process(self.send())
        self.queue = []
        self.isSensing = False
        self.sensing = None  # keep sensing process
        self.isWaitingAck = False
        self.waitingAck = None  # keep pending process


    def enqueue(self, destination, payloadLength, id):
        if len(self.queue) > parameters.MAX_MAC_QUEUE_SIZE:
            print('Time %d, %s: MAC queue full, dropping packet %s' % (self.env.now, self.name, id))
            self.stats.logDroppedPacket(id, self.env.now)
            return

        length = payloadLength + parameters.MAC_HEADER_LENGTH
        macPkt = macPacket.MacPacket(self.name, destination, length, id, False)
        self.queue.append(macPkt)
        self.stats.logGeneratedPacket(id, self.env.now)


    def send(self):
        while True:
            yield self.env.timeout(parameters.SLOT_DURATION)

            # sensing phase
            if self.isSensing:          # I'm sensing for another packet, I wait
                yield self.sensing

            # check if I have a packet to send
            if len(self.queue) > 0:
                macPkt = self.queue[0]
                self.sensing = self.env.process(self.waitIdleAndSend(macPkt))
                yield self.sensing  

                self.waitingAck = self.env.process(self.waitAck(macPkt))
                yield self.waitingAck  # wait until the ack is received or timeout


    def handleReceivedPacket(self, macPkt):
        # 成功收到信息
        if macPkt.destination == self.name and not macPkt.ack:  # send ack to normal packets
            if parameters.PRINT_LOGS:
                print('Time %d, %s: MAC receives packet %s from %s and sends ACK' % (self.env.now, self.name, macPkt.id, macPkt.source))
            self.node.receive(macPkt.id, macPkt.source)
            self.stats.logDeliveredPacket(macPkt.id, macPkt.transmitTime, self.env.now)
            # Generate and send ACK
            ack = macPacket.MacPacket(self.name, macPkt.source, parameters.ACK_LENGTH, macPkt.id, True)
            yield self.env.timeout(parameters.SIFS_DURATION)
            yield self.env.process(self.phy.send(ack))

        elif macPkt.destination == self.name:
            if parameters.PRINT_LOGS:
                print('Time %d, %s: MAC receives ACK %s from %s' % (self.env.now, self.name, macPkt.id, macPkt.source))
            if self.isWaitingAck:    # check if still waiting for the ACK
                self.waitingAck.interrupt()


    def waitAck(self, macPkt): # 重传
        self.isWaitingAck = True
        if parameters.PRINT_LOGS:
            print('Time %d, %s: MAC waits ACK of %s' % (self.env.now, self.name, macPkt.id))
        try:
            yield self.env.timeout(parameters.ACK_TIMEOUT)  
            # timeout expired, resend
            if macPkt.retransmissionTimes > parameters.MAX_RETRANSMITION_TIME:
                if parameters.PRINT_LOGS:
                    self.stats.logfailedRetransmission(macPkt.id,self.env.now)
                    print('Time %d, %s: %s fails finally' % (self.env.now, self.name, macPkt.id))
            else:    
                macPkt.retransmissionTimes += 1
                if parameters.PRINT_LOGS:
                    print('Time %d, %s: %s timeout without ACK from %s' % (self.env.now, self.name, macPkt.id, macPkt.destination))
                
                if parameters.PRINT_LOGS:
                    print('Time %d, %s: MAC plans to retransmit %s, retransmitCounter = %d' % (self.env.now, self.name, macPkt.id, macPkt.retransmissionTimes))
                self.stats.logRetransmission(self.name,self.env.now)

        except simpy.Interrupt:
            # ACK received
            self.queue.pop(0)
        
        self.isWaitingAck = False


    def waitIdleAndSend(self, macPkt): 
        # 闲置等待并发送
        self.isSensing = True
        if parameters.PRINT_LOGS:
            print('Time %d, %s: MAC starts sensing for packet %s' % (self.env.now, self.name, macPkt.id))
        backoff = random.randint(0, min(pow(2,macPkt.retransmissionTimes-1)*parameters.CW_MIN, parameters.CW_MAX)-1) * parameters.SLOT_DURATION

        currentEndTime = self.env.now
        for packets in self.ether.txPackets:
            if packets.endTime > currentEndTime:
                currentEndTime = packets.endTime
        
        while True:
            try:
                yield self.env.timeout(currentEndTime - self.env.now)

                yield self.env.timeout(parameters.DIFS_DURATION)

                while backoff > 0:
                    yield self.env.timeout(parameters.SLOT_DURATION)
                    backoff -= parameters.SLOT_DURATION

                if parameters.PRINT_LOGS:
                    print('Time %d, %s: MAC gets access for packet %s' % (self.env.now, self.name, macPkt.id))
                macPkt.transmitTime = self.env.now
                yield self.env.process(self.phy.send(macPkt))   # wait until the packet is sent
                self.isSensing = False
                return
            
            except simpy.Interrupt as endTime:
                if currentEndTime < endTime.cause:
                    currentEndTime = endTime.cause
