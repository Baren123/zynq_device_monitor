#!/usr/bin/env python
#coding: utf-8

from flask import Flask,send_file,request, jsonify,render_template
import time
import os
import json
import random
import zmq
import sys
import base64
import hmac
import hashlib


cxt = zmq.Context()
sock = cxt.socket(zmq.DEALER)
sock.connect("tcp://127.0.0.1:9001")
# sock.connect("tcp://0.0.0.0:9001")

# zmq_setsockopt(ZMQ_RCVTIMEO = 5)

app = Flask(__name__)
@app.route('/login',methods=["GET"])
def login():
    return send_file("login.html")


@app.route('/getInfo', methods=["GET","POST"])
def getInfo():
    input_uid = request.form['input_uid']
    print("ui_input_uid:{}".format(input_uid))
    cmd_dict = {"cmd":"exec_shell", "time":int(time.time()), "identity":"mkp-admin","task_id":" ", "shell":"cat /run/dev_info/uid", "uids": input_uid}
    netkey = '1mJeqJr7UqDoXwcU89z08jeO'
    cmd_message = json.dumps(cmd_dict)
    signature = hmac.new(netkey.encode('utf-8'), cmd_message.encode('utf-8'), hashlib.sha256).hexdigest()
    cmd = cmd_message + '#' + signature
    sock.send_string(cmd)
    msg = sock.recv()
    print("ui_login_recv_msg:{}".format(msg))

    result_msg = msg[:msg.find('#')]
    my_dict = json.loads(result_msg)
    if my_dict["result"] == 2:
        return ('Input devices is not connect')
    else:
        return render_template('getInfo.html',input_uid=input_uid)


@app.route('/updataDevInfo/<input_uid>', methods=["GET","POST"])
def updataDevInfo(input_uid):
    get_uid = input_uid
    print("current_uid:{}".format(get_uid))
    netkey = '1mJeqJr7UqDoXwcU89z08jeO'
    cmd_dict = {"cmd":"exec_shell", "time":int(time.time()), "identity":"mkp-admin","task_id":" ", "shell":"cd ~/tmp && python3 get_dev_info.py","uids":get_uid}
    cmd_message = json.dumps(cmd_dict)
    signature = hmac.new(netkey.encode('utf-8'), cmd_message.encode('utf-8'), hashlib.sha256).hexdigest()
    cmd = cmd_message + '#' + signature
    sock.send_string(cmd)
    print("b64_send_string:{}".format(cmd))
    msg = sock.recv()
    print("b64_zmq_recv_string:{}".format(msg))
    result_msg = msg[:msg.find('#')]
    my_dict = json.loads(result_msg)
    out_data = my_dict["out_put"]
    b64_out_data = base64.b64decode(out_data)
    print("b64_out_data:{}".format(b64_out_data))
    return b64_out_data


if __name__ == "__main__":
    print ("run")
    app.run(host="0.0.0.0",port="5000")