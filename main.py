import time
import math

from datetime import datetime
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation, PillowWriter

from enum import Enum

class Approach(Enum):
    ZERO_FIRST = 1
    UPTIME_MEAN = 2
    RAPID_FIRST_COMPUTATION = 3

class Mode(Enum):
    LIVE_VIEW = 0
    SAVE_ANIMATION = 1

class TimeBase(Enum):
    TIMESTAMP = 0,
    UPTIME = 1

# this should be the interface used in the device
# to access the internet
INTERFACE_TO_MONITOR='wlp4s0'
selected_approach = Approach.RAPID_FIRST_COMPUTATION
MODE = Mode.SAVE_ANIMATION
DEBUG_TICK=False
FIXED_ADJUSTMENT_WINDOW=False



INTERFACE_NAME_POSITION = 0
INTERFACE_BYTES_POSITION = 1

DATAPOINT_TIME_POS = 0
DATAPOINT_VALUE_POS = 1

NS_IN_MS = 1_000_000
MS_IN_S = 1_000
BYTES_IN_KB = 1_000
DELTA_T_MS = 1000
DELTA_D_MS = 300

time_base = TimeBase.TIMESTAMP if selected_approach == Approach.ZERO_FIRST else TimeBase.UPTIME
def get_time():
    if selected_approach == Approach.ZERO_FIRST:
        return math.floor(time.time_ns() / NS_IN_MS)

    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds * 1000

def get_current_net_load_down():
    f = open('/proc/net/dev', 'r')
    data = f.readlines()
    interface_info_lines = data[2:]

    all_info = []
    for it in interface_info_lines:
        all_info.append([x for x in it.split(' ') if x != ''])

    info = [x for x in all_info if x[INTERFACE_NAME_POSITION].strip(':') == INTERFACE_TO_MONITOR]

    if len(info) == 0:
        print('invalid interface name selected')

    f.close()
    return float(info[0][INTERFACE_BYTES_POSITION]) / BYTES_IN_KB
    

class SeriesManager:
    def __init__(self):
        self.iteration = 0
        self.sc = []
        self.sd = []

        if selected_approach != Approach.RAPID_FIRST_COMPUTATION:
            self.last_computation_time = 0
            self.imaginary_first = (0,0)
        else:
            t = get_time()
            value = get_current_net_load_down()
            self.last_computation_time = t
            self.imaginary_first = (t,value)
            time.sleep(DELTA_D_MS / MS_IN_S)
            self.tick()

    def load_sc_datapoint(self):
        t = get_time()
        value = get_current_net_load_down()

        data_point = (t, value)
        print('Sc: ', data_point)
        self.sc.append(data_point)

    def _value_sc(self, i):
        return self.sc[i][DATAPOINT_VALUE_POS] if i >= 0 else self.imaginary_first[DATAPOINT_VALUE_POS]

    def _time_sc(self, i):
        return self.sc[i][DATAPOINT_TIME_POS] if i >= 0 else self.imaginary_first[DATAPOINT_TIME_POS]


    def _difference_with_variable_interval(self, i):
        return (
            DELTA_T_MS / (
                self._time_sc(i) - self._time_sc(i-1)
            )) * (
                self._value_sc(i) - self._value_sc(i-1)
            )

    def load_sd_datapoint(self, t):
        value = 0

        if selected_approach == Approach.ZERO_FIRST:
            if len(self.sc) > 1:
                i = len(self.sc) -1
                value = self.sc[i][1] - self.sc[i-1][1]
                t = self.sc[i][0]

            data_point = (t, value)
        if selected_approach == Approach.UPTIME_MEAN or selected_approach == Approach.RAPID_FIRST_COMPUTATION:
            value = self._difference_with_variable_interval(self.iteration)
            data_point = (t, value)

        print('Sd: ', data_point)
        self.sd.append((t, value))

    def tick(self):
        t = get_time()
        if DEBUG_TICK: print('tick', t)
        
        if selected_approach != Approach.RAPID_FIRST_COMPUTATION:
            if t - self.last_computation_time < DELTA_T_MS:
                return
        else:
            # while on the RAPID_FIST_COMPUTATION_APPROACH should wait for the shorter interval
            # only on the first iteration, otherwise behaves like the other approaches
            if self.iteration == 0 and t - self.last_computation_time < DELTA_D_MS:
                return
            elif self.iteration > 0 and t - self.last_computation_time < DELTA_T_MS:
                return

        self.last_computation_time = t
        self.load_sc_datapoint()
        self.load_sd_datapoint(t)
        self.iteration += 1


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

figure.gca().set_ylabel('Load (KB/s)')

figure.gca().set_xticks([])
figure.gca().set_autoscaley_on(True)

line, = pyplot.plot(x_data, y_data, '-')

def update(frame):
    mgr.tick()
    x_data.append(mgr.iteration)
    y_data.append(mgr.sd[len(mgr.sd)-1][1] if len(mgr.sd) > 0 else 0)
    line.set_data(x_data, y_data)    

    if FIXED_ADJUSTMENT_WINDOW:
        figure.gca().set_ylim(bottom=0, top=max(y_data) * 1.5)
    else:
        figure.gca().relim()

    figure.gca().set_xlim((
        mgr.iteration - 20 if mgr.iteration > 20 else 0, 
        mgr.iteration if mgr.iteration > 20 else 20, 
    ))
    figure.gca().autoscale_view()
    return line,

animation = FuncAnimation(figure, update, interval=10, frames=2_000)

if MODE == Mode.SAVE_ANIMATION:
    print('saving...')
    animation.save(filename="graph.gif", writer="pillow")
elif MODE == Mode.LIVE_VIEW:
    pyplot.show()