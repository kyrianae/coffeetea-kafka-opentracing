
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
import socket
import random
from multiprocessing.dummy import Pool as ThreadPool
from jaeger_client import Config
from opentracing import Format
from kafka import KafkaProducer

nb_client = 1
root = 'http://127.0.0.1:5000'
drinks = ['coffee', 'tea']
means_of_payment = ['gold', 'card']
energy = {
    'coffee': 3,
    'tea': 2
    }
clients=[]


def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'local_agent': {
                'reporting_host': "127.0.0.1",
                'reporting_port': 6831,
            },
            'logging': True,
        },
        service_name=service,
    )
    # this call also sets opentracing.tracer
    return config.initialize_tracer()


tracer = init_tracer('customer')
urllib3.disable_warnings(InsecureRequestWarning)


def call_api(path, header):
    global root
    result = requests.get(root+path, headers=header, verify=False)
    print('call api ' + path + ' ' + str(result.status_code))
    result.raise_for_status()
    return result


class Client:
    def __init__(self, name):
        self.name=name
        self.energy=0

    def drink(self):
        r = random.getrandbits(1)
        p = means_of_payment[random.getrandbits(1)]
        try:
            call_api('/order/'+drinks[r]+'/' + p + '/' + self.name, {})
            self.energy = energy.get(drinks[r])

            self.last=True
        except Exception as e:
            print(e)
            self.last = False

    def live(self):
        while (True):
            if self.energy <= 0:
                self.drink()
            self.energy += -1
            time.sleep(0.5)


def launch(o):
    o.live()


for i in range (0, nb_client, 1):
    clients.append(Client('customer_'+str(i)))

pool = ThreadPool(nb_client)
results = pool.map(launch, clients)
pool.close()
