from scipy import rand
import simpy
import random

import node
import phy
import ether
import parameters
import stats
import os
import sys
import datetime

class Logger(object):
    # CJH 2022/5/11
    def __init__(self, fileN=''):
        os.mkdir(fileN)
        fileN = os.path.join(fileN,"simulation.log" )
        self.terminal = sys.stdout
        self.log = open(fileN, "a+",encoding='utf-8')
 
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.flush() #每次写入后刷新到文件中，防止程序意外结束
    def flush(self):
        self.log.flush()


def main():
    random.seed(parameters.RANDOM_SEED)

    file='results_'+parameters.AC+'_lambda_'+str(parameters.TARGET_RATE)+datetime.datetime.now().strftime("_%Y-%m-%d-%H-%M-%S")
    sys.stdout = Logger(file)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"-sim.log\n\n"+parameters.s+'\nLog starting\n------------------------\n')

    # 创建仿真环境
    env = simpy.Environment()
    eth = ether.Ether(env)
    statistics = stats.Stats(file)

    nodes = []

    for i in range(0, parameters.NUMBER_OF_NODES):
        if i == 0:
            name = "AP"
        else:
            name = "Node" + str(i)
        [pos1,pos2]=parameters.NODE_POSITION[i] if parameters.NODE_POSITION else [random.randint(0,20),random.randint(0,20)]
        nodes.append(node.Node(env, name, eth, pos1, pos2, statistics))

    for i in range(1, parameters.NUMBER_OF_NODES):
        destinations = ['AP']
        # for j in range(0, parameters.NUMBER_OF_NODES):
        #     if i != j:
        #         destinations.append(nodes[j].name)
        # 设定节点事件
        env.process(nodes[i].keepSendingIncreasing(parameters.STARTING_RATE, parameters.TARGET_RATE, destinations))
        #env.process(nodes[i].keepSending(parameters.TARGET_RATE, destinations))

    if not parameters.PRINT_LOGS:
        env.process(printProgress(env))

    # 开始运行
    env.run(until=parameters.SIM_TIME)

    #作图
    statistics.plotNodePosition(nodes)
    statistics.plotCumulativePackets()
    statistics.plotThroughput()
    statistics.plotDelays()
    statistics.plotRetransmissions()
    statistics.plotfailedPacket()


def printProgress(env):
    while True:
        print('Progress: %d / %d' % (env.now * 1e-9, parameters.SIM_TIME * 1e-9))
        yield env.timeout(1e9)


if __name__ == '__main__':
    main()
