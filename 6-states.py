import time
from flask import Flask
from flask import request
import subprocess
import datetime
import json
import os
from flask_cors import CORS
import logging
from urllib3.exceptions import InsecureRequestWarning
import requests
import urllib3
from time import sleep as sleep
from influxdb import InfluxDBClient

import socket
import random
from multiprocessing.dummy import Pool as ThreadPool

nb_client=50
root = 'http://127.0.0.1:5003'

def call_api(path, header):
    global root
    urllib3.disable_warnings(InsecureRequestWarning)
    result = requests.get(root+path, headers=header, verify=False)
    result.raise_for_status()
    return result

client = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')

client.create_database('example')


while True:
    r= None
    try :
        r = call_api('/state', {})
        print (r.content)

        # 'tea_leaf':tea_leaf,
        # 'coffee_bean':coffee_bean,
        # 'water':water,
        # 'total':total,
        # 'client':client,
        # 'coffe_in_progress':coffe_in_progress,
        # 'tea_in_progress':tea_in_progress,
        # 'fill_coffee_in_progress':fill_coffee_in_progress,
        # 'fill_water_in_progress':fill_water_in_progress,
        # 'fill_tea_in_progress':fill_tea_in_progress

        j = json.loads(r.content.decode())
        # print(j)
    # if True :
        json_body = [
            {
            "measurement": "coffeetea",
            "tags": {
                "type": "tea",
                "fill": j['fill_tea_in_progress'],
            },

            "fields": {
                "resource": j['tea_leaf'],
                "refills": 1.0 if j['fill_tea_in_progress'] else 0.0,
                "wip_produce": j['tea_in_progress'],
            }
        }
        ]
        client.write_points(json_body)
        json_body = [
            {
                "measurement": "coffeetea",
                "tags": {
                    "type": "coffee",
                    "fill": j['fill_coffee_in_progress'],
                },

                "fields": {
                    "resource": j['coffee_bean'],
                    "refills": 1.0 if j['fill_coffee_in_progress'] else 0.0,
                    "wip_produce": j['coffee_in_progress'],
                }
            }
        ]
        client.write_points(json_body)
        json_body = [
            {
                "measurement": "coffeetea",
                "tags": {
                    "type": "water",
                    "fill": j['fill_water_in_progress']
                },

                "fields": {
                    "refills": 1.0 if j['fill_water_in_progress'] else 0.0,
                    "resource": j['water'],

                }
            }
        ]
        client.write_points(json_body)
        json_body = [
            {
                "measurement": "stats",
                "tags": {
                    "type": "gold"
                },

                "fields": {
                    "value": j['total'],
                    "clients": j['client']
                }
            }
        ]
        client.write_points(json_body)
    except:
        print('not reached or error')

    sleep(0.5)
