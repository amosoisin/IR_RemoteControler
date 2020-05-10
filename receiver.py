import RPi.GPIO as GPIO
import datetime
from enum import Enum
import time


class Receiver:
    def __init__(self):
        self.RCV_PIN = 8
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.RCV_PIN, GPIO.IN)
        self.last_change_us = self.__micros()
        self.state = GPIO.HIGH
        self.signal = []
        self.signal_len_th = 10

    def start(self):
        while True:
            if (self.state == GPIO.LOW):
                self.__wait_low()
            elif (self.__wait_high() == 1):
                if (len(self.signal) >= self.signal_len_th):
                    return
                self.signal.clear()
                continue

            now = self.__micros()
            elapsed_us = now - self.last_change_us
            self.signal.append(elapsed_us)
            self.last_change_us = now
            self.state = GPIO.HIGH if self.state == GPIO.LOW else GPIO.LOW

    def analyze(self):
        period = self.__period()
        signal_bin = []
        for sig_idx, us in enumerate(self.signal[3:]):
            if (sig_idx % 2 == 0 and us > period*7): #high && 8T
                self.signal = self.signal[1:sig_idx]
                break
            elif (sig_idx % 2 != 0): #low
                if (us > 2*period): # high:low=1:3 -> 1
                    signal_bin.append(1)
                else:               # high:low=1:1 -> 0
                    signal_bin.append(0)
        return signal_bin

    def __period(self):
        if (len(self.signal) >= self.signal_len_th):
            sample_start = 3
            sample_max = 21
            period_sample = self.signal[sample_start:sample_max:2]
            return sum(period_sample)//len(period_sample)
        return 0

    def __wait_low(self):
        while (GPIO.input(self.RCV_PIN) == GPIO.LOW):
            pass

    def __wait_high(self):
        timeout_us = 1 * pow(10, 5)
        start = self.__micros()
        while (GPIO.input(self.RCV_PIN) == GPIO.HIGH):
            if (self.__micros() - start > timeout_us):
                return 1
        return 0
        
    def __micros(self):
        return datetime.datetime.today().microsecond


def input_filename():
    while True:
        print("register_name: ", end="")
        file_name = input()
        if (not file_name):
            print("Please input filename")
            continue
        break
    file_name = file_name + ".sig"
    return file_name


if __name__ == "__main__":
    import pickle
    import sys

    file_dir = "data/RE208/"

    print("Input signal to Receiver")
    receiver = Receiver()
    receiver.start()
    signal_bin = receiver.analyze()
    print(signal_bin)
    print("Do you save this? (yes/no): ", end="")
    if (input() != "yes"):
        sys.exit()
    file_name = input_filename()
    with open(file_dir+file_name, "wb") as f:
        pickle.dump(signal_bin, f)
    print("Saved!! : " + file_dir + file_name)
