import matplotlib.pyplot as plt
import numpy as np
from numpy import mean, std
from scipy import misc
import itertools
import csv

import parameters


class Stats(object):
    def __init__(self,file):
        self.generatedPacketsTimes = {}     # packet id - timestamp of generation
        self.droppedPacketsTimes = {}       # packet id - timestamp of drop
        self.deliveredPacketsTimes = []     # packet id - timestamp of delivery
        self.failedRetransmissionTimes = {} # packet id - timestamp of failed retransmission attempt
        self.retransmissionTimes = []       # timestamps of retransmissions
        self.filename=file

    def plotNodePosition(self, nodes):
        plt.figure()
        i=0
        for node in nodes:
            if i == 0:
                plt.scatter(node.latitude, node.longitude,label='AP')
            else:
                plt.scatter(node.latitude, node.longitude,label='Node '+str(i))
            i += 1
        plt.legend()
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim([0,20])
        plt.ylim([0,20])
        plt.legend()
        file = self.filename+'/position' + str(parameters.TARGET_RATE) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        plt.close()


    def logGeneratedPacket(self, id, timestamp):
        self.generatedPacketsTimes[id] = timestamp


    def logDroppedPacket(self, id, timestamp):
        self.droppedPacketsTimes[id] = timestamp


    def logDeliveredPacket(self, id, beginTime, endTime):
        self.deliveredPacketsTimes.append([id, beginTime, endTime])


    def logRetransmission(self,sender,timestamp):
        self.retransmissionTimes.append([sender,timestamp])
    

    def logfailedRetransmission(self, id, timestamp):
        self.failedRetransmissionTimes[id] = timestamp

    
    def plotThroughput(self):
        plt.figure()
        filename = self.filename + '/delivered.csv'
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'beginTime', 'endTime'])
            for id, beginTime, endTime in self.deliveredPacketsTimes:
                writer.writerow([id, beginTime, endTime])

        timeSlots = np.arange(int(parameters.SIM_TIME / parameters.SLOT_DURATION)) * (parameters.SLOT_DURATION * 1e-9)
        diff = [[0]*len(timeSlots) for _ in range(parameters.NUMBER_OF_NODES-1)]
        for id, beginTime, endTime in self.deliveredPacketsTimes:
            nodeIdx = int(id.split('_')[1][4:])
            bt = int(beginTime / parameters.SLOT_DURATION)
            et = int(endTime / parameters.SLOT_DURATION)
            diff[nodeIdx-1][bt] += 1
            if endTime >= len(timeSlots):
                diff[nodeIdx-1][et] -= 1

        throughput = [[0]*len(timeSlots) for _ in range(parameters.NUMBER_OF_NODES-1)]
        for i in range(parameters.NUMBER_OF_NODES-1):
            acc = list(itertools.accumulate(diff[i]))
            curSum = 0
            for j in range(len(timeSlots)):
                curSum += acc[j]
                if j >= 50000:
                    curSum -= acc[j-50000]
                throughput[i][j] = float(curSum / 50000)
            plt.plot(timeSlots, throughput[i], label='Node'+str(i+1))

        totalThroughput = np.sum(np.array(throughput), axis=0)
        plt.plot(timeSlots, totalThroughput, label='Total')
    
        plt.legend()
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput')
        plt.legend()
        file = self.filename+'/throughput' + str(parameters.TARGET_RATE) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        print("Average throughput: {}".format(mean(totalThroughput)))

        plt.close()


    def plotDelays(self):
        plt.figure()
        delayMat = [list() for _ in range(parameters.NUMBER_OF_NODES-1)]
        delayList = []
        for id, _, endTime in self.deliveredPacketsTimes:
            nodeIdx = int(id.split('_')[1][4:])
            generatedTime = int(id.split('_')[0])
            delayMat[nodeIdx-1].append((endTime - generatedTime) * 1e-6)
            delayList.append((endTime - generatedTime) * 1e-6)

        for i in range(parameters.NUMBER_OF_NODES-1):
            y = np.arange(len(delayMat[i])) / float(len(delayMat[i]))
            plt.plot(np.sort(delayMat[i]), y, label='Node'+str(i+1))

        y = np.arange(len(delayList)) / float(len(delayList))
        plt.plot(np.sort(delayList), y, label='Total')

        plt.legend()
        plt.xlabel('Delay (ms)')
        plt.ylabel('CDF')
        plt.xlim(0, 100)
        plt.legend()
        file = self.filename+'/delays' + str(parameters.TARGET_RATE) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        print("Average delay: {}".format(mean(delayList)))
        print("Standard deviation of delay: {}".format(std(delayList)))
        print("Minimum delay: {}".format(min(delayList)))
        print("Maximum delay: {}".format(max(delayList)))

        plt.close()

    
    def plotfailedPacket(self):
        plt.figure()
        milliseconds = np.arange(0, int(parameters.SIM_TIME * 1e-6), 1)
        failedPacketEveryMillisecond = []
        for i in range(int(parameters.SIM_TIME * 1e-6)):
            failedPacketEveryMillisecond.append(0)
        for packet in self.failedRetransmissionTimes:
            failedPacketEveryMillisecond[int(self.failedRetransmissionTimes[packet]*1e-6)] += 1

        for i in range(len(failedPacketEveryMillisecond)-1):
            failedPacketEveryMillisecond[i+1] += failedPacketEveryMillisecond[i]
        plt.plot(milliseconds, failedPacketEveryMillisecond, 'r:', label='Failed Packets')

        plt.legend()
        plt.xlabel('Time (ms)')
        plt.ylabel('Failed Packets')
        plt.legend()
        file = self.filename+'/failed_packets_' + str(parameters.MAX_RETRANSMITION_TIME) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        print("Total number failed packets: {}".format((failedPacketEveryMillisecond[-1])))

        # for j in range(parameters.NUMBER_OF_NODES):
        #     plt.figure()
        #     failedPacketEveryMillisecond = []
        #     for i in range(int(parameters.SIM_TIME * 1e-6)):
        #         failedPacketEveryMillisecond.append(0)
        #     for packet in self.failedRetransmissionTimes:
        #         if int(packet.split('_')[1].replace('Node','')) != j : continue
        #         failedPacketEveryMillisecond[int(self.failedRetransmissionTimes[packet]*1e-6)] += 1

        #     for i in range(len(failedPacketEveryMillisecond)-1):
        #         failedPacketEveryMillisecond[i+1] += failedPacketEveryMillisecond[i]
        #     plt.plot(milliseconds, failedPacketEveryMillisecond, 'r:', label='Failed Packets of Node '+str(j))

        #     plt.legend()
        #     plt.xlabel('Time (ms)')
        #     plt.ylabel('Failed Packets')
        #     plt.legend()
        #     file = self.filename+'/failed_packets_' + str(parameters.MAX_RETRANSMITION_TIME) + '_Node_'+str(j) + '.pdf'
        #     plt.savefig(file, bbox_inches='tight', dpi=250)
        
        plt.close()



    def plotCumulativePackets(self):
        plt.figure()

        cumulativeGeneratedPackets = [1]
        generatedPacketsTimes = []
        i = 0
        for packet in self.generatedPacketsTimes:
            if i != 0:
                cumulativeGeneratedPackets.append(cumulativeGeneratedPackets[i-1] + 1)
            generatedPacketsTimes.append(self.generatedPacketsTimes[packet] * 1e-9)
            i += 1

        cumulativeDeliveredPackets = [1]
        deliveredPacketsTimes = []
        i = 0
        for _, _, endTime in self.deliveredPacketsTimes:
            if i != 0:
                cumulativeDeliveredPackets.append(cumulativeDeliveredPackets[i-1] + 1)
            deliveredPacketsTimes.append(endTime * 1e-9)
            i += 1

        plt.plot(generatedPacketsTimes, cumulativeGeneratedPackets, 'r-', label='Generated')
        plt.plot(deliveredPacketsTimes, cumulativeDeliveredPackets, 'g:', label='Delivered')

        plt.legend()
        plt.xlabel('Time (s)')
        plt.ylabel('Packets')
        plt.legend()
        file = self.filename+'/packets' + str(parameters.TARGET_RATE) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        print("Total number of generated packets: {}".format(len(generatedPacketsTimes)))
        print("Total number of delivered packets: {}".format(len(deliveredPacketsTimes)))

        # for j in range(parameters.NUMBER_OF_NODES):
        #     try:
        #         plt.figure()

        #         cumulativeGeneratedPackets = [1]
        #         generatedPacketsTimes = []
        #         i = 0
        #         for packet in self.generatedPacketsTimes:
        #             if int(packet.split('_')[1].replace('Node',''))!=j:continue
        #             if i != 0:
        #                 cumulativeGeneratedPackets.append(cumulativeGeneratedPackets[i-1] + 1)
        #             generatedPacketsTimes.append(self.generatedPacketsTimes[packet] * 1e-9)
        #             i += 1

        #         cumulativeDeliveredPackets = [1]
        #         deliveredPacketsTimes = []
        #         i = 0
        #         for packet in self.deliveredPacketsTimes:
        #             if int(packet.split('_')[1].replace('Node',''))!=j:continue # 此节点发出的包中被接收的
        #             if i != 0:
        #                 cumulativeDeliveredPackets.append(cumulativeDeliveredPackets[i-1] + 1)
        #             deliveredPacketsTimes.append(self.deliveredPacketsTimes[packet] * 1e-9)
        #             i += 1

        #         plt.plot(generatedPacketsTimes, cumulativeGeneratedPackets, 'r-', label='Generated')
        #         plt.plot(deliveredPacketsTimes, cumulativeDeliveredPackets, 'g:', label='Delivered')

        #         plt.legend()
        #         plt.xlabel('Time (s)')
        #         plt.ylabel('Packets of Node '+str(j))
        #         plt.legend()
        #         file = self.filename+'/packets' + str(parameters.TARGET_RATE) +'_Node_'+str(j) + '.pdf'
        #         plt.savefig(file, bbox_inches='tight', dpi=250)
        #     except:pass

        plt.close()


    def plotRetransmissions(self):
        plt.figure()
        retransmissionsEveryMillisecond = []
        for i in range(int(parameters.SIM_TIME * 1e-6)):
            retransmissionsEveryMillisecond.append(0)

        cumulative = 0
        for timestamp in self.retransmissionTimes:
            cumulative = cumulative + 1
            retransmissionsEveryMillisecond[int(timestamp[1] * 1e-6)] = cumulative

        for i in range(1, len(retransmissionsEveryMillisecond)):
            if retransmissionsEveryMillisecond[i] == 0:
                retransmissionsEveryMillisecond[i] = retransmissionsEveryMillisecond[i - 1]

        milliseconds = np.arange(0, int(parameters.SIM_TIME * 1e-6), 1)

        plt.plot(milliseconds, retransmissionsEveryMillisecond, 'r:', label='Retransmissions')

        plt.legend()
        plt.xlabel('Time (ms)')
        plt.ylabel('Retransmissions')
        plt.legend()
        file = self.filename+'/retransmissions' + str(parameters.TARGET_RATE) + '.pdf'
        plt.savefig(file, bbox_inches='tight', dpi=250)
        print("Total number of retransmissions: {}".format(cumulative))

        # for j in range(parameters.NUMBER_OF_NODES):
        #     plt.figure()
        #     retransmissionsEveryMillisecond = []
        #     for i in range(int(parameters.SIM_TIME * 1e-6)):
        #         retransmissionsEveryMillisecond.append(0)

        #     cumulative = 0
        #     for timestamp in self.retransmissionTimes:
        #         if int(timestamp[0].replace('Node',''))!= j : continue
        #         cumulative = cumulative + 1
        #         retransmissionsEveryMillisecond[int(timestamp[1] * 1e-6)] = cumulative

        #     for i in range(1, len(retransmissionsEveryMillisecond)):
        #         if retransmissionsEveryMillisecond[i] == 0:
        #             retransmissionsEveryMillisecond[i] = retransmissionsEveryMillisecond[i - 1]

        #     milliseconds = np.arange(0, int(parameters.SIM_TIME * 1e-6), 1)

        #     plt.plot(milliseconds, retransmissionsEveryMillisecond, 'r:', label='Retransmissions of Node '+str(j))

        #     plt.legend()
        #     plt.xlabel('Time (ms)')
        #     plt.ylabel('Retransmissions')
        #     plt.legend()
        #     file = self.filename+'/retransmissions' + str(parameters.TARGET_RATE)+'_Node_'+str(j) + '.pdf'
        #     plt.savefig(file, bbox_inches='tight', dpi=250)
        
        plt.close()
