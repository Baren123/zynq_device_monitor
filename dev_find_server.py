#coding: utf-8


import socket

HOST = ''
PORT = 7032
BUFSIZE = 1024
UID_PATH = '/run/dev_info/uid'


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST, PORT))

while True:
    data, addr = s.recvfrom(BUFSIZE)
    print('recv {} from {}'.format(data, addr))
    try:
        msg = data.decode()
    except UnicodeDecodeError as e:
        print(e)
        continue
    msg = msg.strip().split(' ')
    if len(msg) == 2 and msg[1] == 'mkp' and msg[0] == "get_uid":
        with open(UID_PATH) as f:
            output = f.read()
            msg_ret = "res.get_uid mkp " + output
            print("send {} to {}".format(msg_ret, addr))
            s.sendto(msg_ret.encode(), addr)

s.close()
