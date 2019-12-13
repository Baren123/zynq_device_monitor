#coding: utf-8

import os
import psutil
import socket
import fcntl
import struct
import json
import re
from adbutils import adb
import time

RK_TOTAL = 10
RK_NUMBER_RULE_BEGIN_CHANGE = 7
RK_CPU_NBR = 4

class RKTester(object):
    def __init__(self, dev_index, dev_ser, ifname):
        self.dev_index = dev_index
        self.dev_ser = dev_ser
        self.ifname = ifname
        self.test_list = [
            ("get rk cpu temp", "_cpu_temp", self.getRkCpuTemp),
            ("get rk gpu temp", "_gpu_temp", self.getRkGpuTemp),
            ("get zynq cpu usage", "zynq_cpu_usage", self.getZynqCpuUsage),
            ("get zynq mem usage", "zynq_mem_usage", self.getZynqMemUsage),
            ("get rk cpu usage", "_cpu_usage", self.getRkCpuUsage),
            ("get rk gpu usage", "_gpu_usage", self.getRkGpuUsage),
            ("get rk mem usage", "_mem_usage", self.getRkMemUsage),
            ("get zynq ip", "zynq_ip", self.getZynqIp),
            ("get rk ip", "_ip", self.getRkIp)]

    #温度
    def getRkCpuTemp(self):
        output = adb.device(serial = self.dev_ser).shell(["cat", "/sys/class/thermal/thermal_zone0/temp"])
        return round(float(output.strip())/1000, 3)

    def getRkGpuTemp(self):
        output = adb.device(serial = self.dev_ser).shell(["cat", "/sys/class/thermal/thermal_zone1/temp"])
        return round(float(output.strip())/1000, 3)

    #使用率
    def getZynqCpuUsage(self):
        return psutil.cpu_percent(0)

    def getZynqMemUsage(self):
        return psutil.virtual_memory().percent

    def getRkCpuUsage(self):
        cpu_total_usage = 0
        for i in range(RK_CPU_NBR):
            output = adb.device(serial = self.dev_ser).shell("ssu 0 cat /sys/devices/system/cpu/cpu" + str(i) + "/cpufreq/cpuinfo_cur_freq")
            cpu_total_usage += float(output)/100000
        return round(cpu_total_usage, 3)

    def getRkGpuUsage(self):
        output = adb.device(serial = self.dev_ser).shell(["cat", "/sys/devices/platform/ffa30000.gpu/devfreq/ffa30000.gpu/load"])
        return output[output.find(':')+1:output.find('@')]


    def getRkMemUsage(self):
        output = adb.device(serial = self.dev_ser).shell(["cat", "/sys/class/thermal/thermal_zone1/temp"])
        return round(float(output.strip())/1000, 3)

    #获取IP
    def getZynqIp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        zynq_ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes((self.ifname[:15]).encode('utf-8')))
        )[20:24])
        return zynq_ip.strip()

    def getRkIp(self):
        output = adb.device(serial = self.dev_ser).shell("ifconfig |grep \"Bcast\" | sed 's/.*addr://;s/Bcast.*//'")
        return output.strip()

    def testAll(self,input_dirct):
        for i in range(len(self.test_list)):
            test_name, dirct_key, test_func = self.test_list[i]
            if test_name == 'get zynq cpu usage' or test_name == 'get zynq ip' or test_name == 'get zynq mem usage':
                input_dirct[dirct_key] = test_func()
            else:
                input_dirct["rk_" + str(self.dev_index) + dirct_key] = test_func()
        return True


if __name__ == '__main__':

    rk_id_dict = {}
    dev_info = {}
    succeeded = []
    failed = []
    start_time = time.time()
    f = os.popen('adb devices -l')
    lines = f.readlines()
    for i in range(RK_TOTAL):
        for line in lines:
            if i < RK_NUMBER_RULE_BEGIN_CHANGE-1:
                is_search_result = re.search("device usb:1-1."+str(i+1),line)
            else:
                is_search_result = re.search("device usb:1-1.7."+str(i-5),line)
            if is_search_result:
                rk_id_dict[i+1]=line.split(' ')[0]

    for dev_index in range(1,RK_TOTAL+1):
        ser = rk_id_dict[dev_index]
        tester = RKTester(dev_index, ser, 'eth0')
        if tester.testAll(dev_info):
            succeeded.append(dev_index)
        else:
            failed.append(dev_index)
    print("need_time:{}".format(time.time()-start_time))
    jsonStr = json.dumps(dev_info)
    print (jsonStr)

