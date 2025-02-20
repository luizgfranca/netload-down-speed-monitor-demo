import time
import math

from datetime import datetime
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation

# this should be the interface used in the device
# to access the internet
INTERFACE_TO_MONITOR='wlp4s0'

INTERFACE_NAME_POSITION = 0
INTERFACE_BYTES_POSITION = 1

NS_IN_MS = 1_000_000
BYTES_IN_KB = 1_000


class SeriesManager:
    def __init__(self):
        self.iteration = 0
        self.sc = []
        self.sd = []
        self.last_computation_time = math.floor(time.time_ns() / NS_IN_MS)

    def load_sc_datapoint(self):
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

        data_point = (t, float(info[0][INTERFACE_BYTES_POSITION]) / BYTES_IN_KB)
        print('Sc: ', data_point)
        self.sc.append(data_point)
        f.close()

    def load_sd_datapoint(self):
        i = len(self.sc) -1
        value = self.sc[i][1] - self.sc[i-1][1]
        t = self.sc[i][0]
        data_point = (t, value)
        print('Sd: ', data_point)
        self.sd.append((t, value))

    def tick(self):
        t = math.floor(time.time_ns() / NS_IN_MS)
        print('tick', t)
        if t - self.last_computation_time < 1000:
            return

        self.last_computation_time = t
        self.iteration += 1
        self.load_sc_datapoint()
        if len(self.sc) > 1:
            self.load_sd_datapoint()


mgr = SeriesManager()

x_data, y_data = [], []

figure = pyplot.figure()
figure.set_facecolor("black")
figure.gca().set_facecolor("black")
figure.gca().spines['bottom'].set_color('#dddddd')
figure.gca().spines['top'].set_color('#dddddd') 
figure.gca().spines['right'].set_color('#dddddd')
figure.gca().spines['left'].set_color('#dddddd')

figure.gca().tick_params(axis='x', colors='#dddddd')
figure.gca().tick_params(axis='y', colors='#dddddd')

figure.gca().yaxis.label.set_color('#dddddd')

figure.gca().set_ylabel('Load (KB)')

figure.gca().set_xticks([])

line, = pyplot.plot(x_data, y_data, '-')

def update(frame):
    mgr.tick()
    x_data.append(mgr.iteration)
    y_data.append(mgr.sd[len(mgr.sd)-1][1] if len(mgr.sd) > 0 else 0)
    line.set_data(x_data, y_data)    

    figure.gca().relim()
    figure.gca().set_xlim((
        mgr.iteration - 20 if mgr.iteration > 20 else 0, 
        mgr.iteration if mgr.iteration > 20 else 20, 
    ))
    figure.gca().autoscale_view()
    return line,

animation = FuncAnimation(figure, update, interval=10)

pyplot.show()