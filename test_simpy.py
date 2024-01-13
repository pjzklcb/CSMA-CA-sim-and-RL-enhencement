import simpy

class Node(object):
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.loop = None
        print('Time %d: %s created' % (self.env.now, self.name))

    def checkProcess(self):
        yield self.env.timeout(2)
        print('Time %d: step1' % (self.env.now))

    def checkProcess2(self):
        print('Time %d: pre-step2' % (self.env.now))
        yield self.env.timeout(0)
        print('Time %d: step2' % (self.env.now))
    
    def checkProcess3(self):
        print('Time %d: pre-step3' % (self.env.now))
        yield self.env.process(self.checkProcess())
        print('Time %d: step3' % (self.env.now))

    def alwaysOn(self, number):
        while True:
            yield self.env.timeout(number)
            print('Time %d: alwaysOn with %d' % (self.env.now, number))
    
    def checkProcess4(self):
        self.loop = self.env.process(self.alwaysOn(3))
        print('Time %d: step4' % (self.env.now))

def main():
    env = simpy.Environment()
    node1 = Node(env, 'node1')
    env.process(node1.checkProcess())
    env.process(node1.checkProcess2())
    env.process(node1.checkProcess3())
    node1.checkProcess4()
    print('Time %d: step5' % (env.now))
    env.run(until=20)

if __name__ == '__main__':
    main()