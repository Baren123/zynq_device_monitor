#coding: utf-8

import socket
import zmq
import random
import json
import time
import re
import paramiko
import base64
import hmac
import hashlib


cxt = zmq.Context()
sock = cxt.socket(zmq.ROUTER)
sock.bind("tcp://*:9001")
poller = zmq.Poller()
poller.register(sock, zmq.POLLIN)

HOST = '<broadcast>'
PORT = 7032
BUFSIZE = 1024
ADDR = (HOST, PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', PORT))
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# s.setblocking(False) #设置为非阻塞
s.settimeout(5)


SSH_PORT = 22
USERNAME = 'leye'
PASSWDWORD = ' '

# class ShellAgentStatus(object):
#     OK = 0
#     FAILED = 1
#     UNKNOWN_CMD = 2
#     CHECK_FAILED = 3
#     INVALID_PARAM = 4
#     TIMEOUT = 5
#     DEV_OFFLINE = 6



class ShellAgentStatus(object):
    OK = 10000
    UNKNOWN_ERROR = 10001
    INVALID_SIGNATURE = 10002
    FORMAT_ERROR = 10003
    UNKNOWN_CMD = 10004
    INVALID_PARAMETERS = 10005
    INVALID_IDENTITY = 10006
    BUSY = 10007
    TIMEOUT = 10008
    OFFLINE = 10009

class ShellPerformResult(object):
    OK = 0
    FAILE = 1
    OFFLINE = 2




class ShellAgentServer(object):

    def __init__(self, msg, dev_uid_dict):
        self.msg = msg
        self.dev_uid_dict = dev_uid_dict
        self.response = [
            ["exec_shell",  self.handleExecShell]
        ]


    def run(self):
        print("run_0")
        print(repr(self.msg))
        output = self.handle(self.msg)
        output += '\n'
        return output


    def handle(self,msg):
        msg = msg.strip()
        print("handle:{}".format(msg))
        cmd_msg = msg[:msg.find('#')]
        my_dict = json.loads(cmd_msg)
        cmd, param, uid = 'exec_shell', my_dict["shell"], my_dict["uids"]
        print("cmd: {}, param: {}, uid: {}".format(cmd, param, uid))

        status, result = self.handleReq(cmd, param, uid)
        ###########  输出数据json处理 ###############
        result = str(result)
        result_b64 = base64.b64encode(str.encode(result))
        netkey = '1mJeqJr7UqDoXwcU89z08jeO'
        if status == ShellPerformResult.OFFLINE:
            result_dict = {"cmd":"res.exec_shell","time":int(time.time()),"uid":uid, "task_id":" ",
                "out_put":result_b64, "result":status, "status":ShellAgentStatus.OFFLINE}
        else:
            result_dict = {"cmd":"res.exec_shell","time":int(time.time()),"uid":uid, "task_id":" ",
                "out_put":result_b64, "result":status, "status":ShellAgentStatus.OK}
        output_message = json.dumps(result_dict)
        signature = hmac.new(netkey.encode('utf-8'), output_message.encode('utf-8'), hashlib.sha256).hexdigest()
        output = output_message + '#' + signature
        print("output_msg: {}".format(output))
        return output


    def handleReq(self, cmd, param, uid):
        handle = None
        _cmd, _handle = self.response[0]
        print("run_1")
        if _cmd == cmd:
            handle = _handle
        if handle is None:
            return ShellAgentStatus.UNKNOWN_CMD, None
        elif type(handle) is str:
            return ShellAgentStatus.OK, handle
        else:
            return handle(cmd, param, uid)

    def handleExecShell(self,cmd, param, uid):
        if uid in dev_uid_dict:
            ip = dev_uid_dict[uid]
            ssh.connect(ip, port=SSH_PORT, username=USERNAME, password=PASSWDWORD)#连接服务器
            _, output_result, error_code = ssh.exec_command(param)
            output = output_result.read()
            if len(error_code.readline()) == 0:
                print("perform_shell ip：{}, result:{}".format(ip,output))
                return ShellPerformResult.OK, output
            else:
                return ShellPerformResult.FAILE, None
        else:
            return ShellPerformResult.OFFLINE, None


# 执行ssh连接
def connectSsh(host_ip):
    ssh.connect(hostname=host_ip, port=SSH_PORT, username=USERNAME, password=PASSWDWORD)#连接服务器
    _, output_result, _ = ssh.exec_command('wget -P ~/tmp -N http://120.77.68.95/test/mkp/get_dev_info.py')
    result = output_result.read()
    print("ssh_result:{}".format(result))
    return result


if __name__ == '__main__':

    dev_uid_dict = {}
    dev_info_dict = {}
    ssh = paramiko.SSHClient()#创建SSH对象
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())#允许连接不在know_hosts文件中的主机

    input_str = "get_uid mkp"
    s.sendto(str(input_str).encode(),ADDR)
    result,ADDR = s.recvfrom(BUFSIZE)
    while True:
        try:
            result,ADDR = s.recvfrom(BUFSIZE)
            print("result:{}".format(result.decode()))
            if result:
                result = result.decode()
                uid = re.sub("[\W]+", "",result.split(' ')[-1])
                dev_uid_dict[uid] = ADDR[0]
                dev_info_dict = connectSsh(ADDR[0])
                print("dev_dict{}".format(dev_uid_dict))
        except socket.timeout as e:
            print("dev_uid_dict{}".format(dev_uid_dict))
            s.close()
            break

    while True:
        events = dict(poller.poll(timeout=1))
        if sock in events and events[sock] == zmq.POLLIN:
            identity, msg = sock.recv_multipart()
            print("recv:{}".format(msg))
            msg_conver = msg.decode('utf-8')
            ser = ShellAgentServer(msg_conver, dev_uid_dict)
            tmp = ser.run()
            msg = tmp.encode('utf-8')
            print("send:{}".format(msg))
            sock.send_multipart([identity, msg])
