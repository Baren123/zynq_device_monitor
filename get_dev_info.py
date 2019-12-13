#!/usr/bin/python3
# -*- coding=utf-8 -*-

import os
import psutil
import socket
import fcntl
import struct
import json
import re
from adbutils import adb

RK_TOTAL = 10
RK_NUMBER_RULE_BEGIN_CHANGE = 7
RK_CPU_NBR = 4

class DeviceInfo(object):
    def __init__(self, rk_id_dict, ifname):
        self.rk_id_dict = rk_id_dict
        self.ifname = ifname
        self.zynq_perform_list = [
            ("cpu_usage", self.getZynqCpuUsage),
            ("mem_usage", self.getZynqMemUsage),
            ("ip", self.getZynqIp)]

        self.rk_perform_list = [
            ("cpu_temp", self.getRkCpuTemp),
            ("gpu_temp", self.getRkGpuTemp),
            ("cpu_usage", self.getRkCpuUsage),
            ("gpu_usage", self.getRkGpuUsage),
            ("mem_usage", self.getRkMemUsage),
            ("ip", self.getRkIp)]


    def getZynqCpuUsage(self):
        return psutil.cpu_percent(0)

    def getZynqMemUsage(self):
        return psutil.virtual_memory().percent

    def getZynqIp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        zynq_ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes((self.ifname[:15]).encode()))
        )[20:24])
        return zynq_ip.strip()

    def getRkCpuTemp(self, rk_connect):
        output = rk_connect.shell("cat /sys/class/thermal/thermal_zone0/temp")
        return round(float(output.strip())/1000, 3)

    def getRkGpuTemp(self, rk_connect):
        output = rk_connect.shell("cat /sys/class/thermal/thermal_zone1/temp")
        return round(float(output.strip())/1000, 3)

    def getRkCpuUsage(self, rk_connect):
        cpu_total_usage = 0
        for i in range(RK_CPU_NBR):
            output = rk_connect.shell("ssu 0 cat /sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_cur_freq" % i)
            cpu_total_usage += float(output)/100000
        return round(cpu_total_usage, 3)

    def getRkGpuUsage(self, rk_connect):
        output = rk_connect.shell("cat /sys/devices/platform/ffa30000.gpu/devfreq/ffa30000.gpu/load")
        return output[:output.find('@')]


    def getRkMemUsage(self, rk_connect):
        output = rk_connect.shell("cat /sys/class/thermal/thermal_zone1/temp")
        return round(float(output.strip())/1000, 3)


    def getRkIp(self, rk_connect):
        output = rk_connect.shell("ifconfig |grep \"Bcast\" | sed 's/.*addr://;s/Bcast.*//'")
        return output.strip()

    def performZynq(self):
        zynq_info_dict = {}
        for i in range(len(self.zynq_perform_list)):
            dirct_key, test_func = self.zynq_perform_list[i]
            zynq_info_dict[dirct_key] = test_func()
        return zynq_info_dict

    def performRK(self):
        all_rk_info_list = []
        for rk_nbr in range(1, RK_TOTAL+1):
            rk_info_dict = {}
            rk_connect = adb.device(serial=self.rk_id_dict[rk_nbr])
            for i in range(len(self.rk_perform_list)):
                desc_func, test_func = self.rk_perform_list[i]
                rk_info_dict[desc_func] = test_func(rk_connect)
            all_rk_info_list.append(rk_info_dict)
        return all_rk_info_list

    def performAll(self):
        dev_info_dict = {}
        dev_info_dict['zynq'] = self.performZynq()
        dev_info_dict['rk'] = self.performRK()
        return dev_info_dict


if __name__ == '__main__':

    rk_id_dict = {}
    dev_info = {}
    f = os.popen('adb devices -l')
    lines = f.readlines()
    for i in range(1, RK_TOTAL+1):
        for line in lines:
            if i < RK_NUMBER_RULE_BEGIN_CHANGE:
                is_search_result = re.search("device usb:1-1.%d" % i, line)
            else:
                is_search_result = re.search("device usb:1-1.7.%d" % (i-6), line)
            if is_search_result:
                rk_id_dict[i]=line.split(' ')[0]

    info = DeviceInfo(rk_id_dict, 'eth0')
    dev_info = info.performAll()


    jsonStr = json.dumps(dev_info)
    print (jsonStr)


