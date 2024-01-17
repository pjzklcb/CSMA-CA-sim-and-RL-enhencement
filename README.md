# CSMA-CA-simulation and RL enhancement
Based on https://github.com/Daniel-ChenJH/CSMA-CA-simulation-and-RL-enhancement

Simplify the PHY and Channel model so that all the transmission events sync with SLOT_DURATION to speedup the simulation.

# Modifications
- parameters.py - Simulation setting parameters, including simulation time (in nanoseconds), number of nodes, lambda of Poisson traffic and access category.
1. Add random seed.
2. Add different CW_min and CW_max for different AC.
3. Remove packet loss.
4. Add MAC queue size.

- main.py - Main program.
1. Set Node0 as AP, and only uplink is considered.

- ether.py - Channel model.
1. Ignore the propagration loss and delay.
2. Record current packets transmitted in the channel.

- node.py - Node class.
1. Set the minimum payload size.

- mac.py - MAC layer.
1. Add MAC queue.
2. send() method check queue every SLOT_DURATION to check if there are any packets to be sent.
3. Packet pops out from the queue only if its ACK is correctly received or it exceeds the retransmission times limit.
4. Remove pendingPackets so that retransmission won't compete for the channel independently.
5. MAC waits for the channel to be IDLE before sending and does not sense the channel every SLOT_DURATION.

- phy.py - PHY layer.
1. Packet only calls ether.transmit() at the beginning and end of the packet instead of every SLOT_DURATION. 

- macPacket.py - MAC frame.
1. Record the time of getting channel access and starting TX.

- phyPacket.py - PHY frame.
1. Record the expecting time of ending TX.
