import time
import math


# this should be the interface used in the device
# to access the internet
INTERFACE_TO_MONITOR='wlp4s0'

INTERFACE_NAME_POSITION = 0
INTERFACE_BYTES_POSITION = 1

NS_IN_MS = 1_000_000

sc = []
sd = []

def load_sc_datapoint():
    t = math.floor(time.time_ns() / NS_IN_MS)
    f = open('/proc/net/dev', 'r')
    data = f.readlines()
    interface_info_lines = data[2:]

    all_info = []
    for it in interface_info_lines:
        all_info.append([x for x in it.split(' ') if x != ''])

    info = [x for x in all_info if x[INTERFACE_NAME_POSITION].strip(':') == INTERFACE_TO_MONITOR]

    if len(info) == 0:
        print('invalid interface name selected')

    data_point = (t, float(info[0][INTERFACE_BYTES_POSITION]))
    sc.append(data_point)
    f.close()

def load_sd_datapoint():
    i = len(sc) -1
    value = sc[i][1] - sc[i-1][1]
    t = sc[i][0]
    data_point = (t, value)
    print(data_point)
    sd.append((t, value))

load_sc_datapoint()
time.sleep(1)

while(True):
    load_sc_datapoint()
    load_sd_datapoint()

    if len(sd) > 0:
        print(sc[len(sc)- 1], ' -> ', sd[len(sd)- 1])
    else:
        print(sc[len(sc)- 1])
    
    time.sleep(1)