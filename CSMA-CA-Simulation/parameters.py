from scipy.constants import c
from math import ceil
# c为光速

# NB: sim time are nanoseconds, distances are in meters, powers in watt

# 802.11n parameters. Values from wikipedia
# https://en.wikipedia.org/wiki/IEEE_802.11
# https://en.wikipedia.org/wiki/DCF_Interframe_Space
# https://en.wikipedia.org/wiki/Short_Interframe_Space
# Freq: 2.4 GHz, OFDM, 20 MHz bandwidth, 65 Mbit/s

### SIMULATION PARAMETERS
RANDOM_SEED = 15
SIM_TIME = 2*1e9

PRINT_LOGS = True
NUMBER_OF_NODES = 5     # 1*AP + (NUMBER_OF_NODES-1)*STA
STARTING_RATE = 2000
TARGET_RATE = 2000

NODE_POSITION = []
# NODE_POSITION = [[10,10],[19,5],[1,7],[16,13],[3,18]]    # NONE while NODE_POSITION remains random
# The length of list NODE_POSITION should be the same as NUMBER_OF_NODES

### RADIO PARAMETERS
TRANSMITTING_POWER = 0.1 # Watt, legal limit in EU for EIRP
RADIO_SWITCHING_TIME = 0
RADIO_SENSITIVITY = 1e-10 # power under which signal is not sensed


### SIGNAL PARAMETERS
FREQUENCY = 2400000000 # 2.4 GHz
WAVELENGTH = c/FREQUENCY

### PHY PARAMETERS
BITRATE = 65000000 # 65 Mbit/s, 802.11n 20 MHz channels, MCS = 7, GI = 0.8us
BIT_TRANSMISSION_TIME = 1/BITRATE * 1e9
NOISE_FLOOR = 1e-9
PHY_PREAMBLE_TIME = 32000 # 11n PHY preamble time 
 
### MAC PARAMETERS
SLOT_DURATION = 9000    # 9 us 
SIFS_DURATION = 18000   # 18 us
DIFS_DURATION = SIFS_DURATION + (2 * SLOT_DURATION)
MAC_HEADER_LENGTH = 34*8 # 34 byte fixed fields of a mac packet
MIN_MAC_PAYLOAD_LENGTH = 2304*8*2   # 11n, max MSDU size = 2304
MAX_MAC_PAYLOAD_LENGTH = 7935*8     # 11n, max A-MSDU size = 7935
ACK_LENGTH = MAC_HEADER_LENGTH
MAX_MAC_QUEUE_SIZE = 10
MAX_RETRANSMITION_TIME = 10
# ack timeout = transmission time of biggest possible pkt + rtt for 300m distance + sifs + ack transmission time
# ACK_TIMEOUT = (MAX_MAC_PAYLOAD_LENGTH + MAC_HEADER_LENGTH) * BIT_TRANSMISSION_TIME + PHY_PREAMBLE_TIME + 2 * round((300 / c) * pow(10, 9), 0) + SIFS_DURATION + ACK_LENGTH * BIT_TRANSMISSION_TIME
ACK_TIMEOUT = SIFS_DURATION + ceil((ACK_LENGTH * BIT_TRANSMISSION_TIME + PHY_PREAMBLE_TIME) / SLOT_DURATION + 1) * SLOT_DURATION

AC = 'BE'
if AC == 'BE':
    CW_MIN = 32
    CW_MAX = 1024
elif AC == 'VI':
    CW_MIN = 16
    CW_MAX = 32
elif AC == 'VO':
    CW_MIN = 8
    CW_MAX = 16

def get_attrs(li):
    attrs = []
    s='Parameters of this simulation:\n*****\n\n'
    for attr in li:
        if attr.isupper():
            attrs.append(attr)
    for attr in attrs:
        s+=attr+' = '+str(eval(attr))+'\n'
    return attrs,s+'*****\n'

attrs,s=get_attrs(dir())
