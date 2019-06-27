import time

# from basictracer import propagator
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

# from opencensus.trace.tracer import Tracer
# from opencensus.trace import time_event as time_event_module
# from opencensus.ext.zipkin.trace_exporter import ZipkinExporter
# from opencensus.ext.prometheus.stats_exporter import PrometheusStatsExporter
# from opencensus.trace.samplers import always_on
# from opencensus.trace import status
from influxdb import InfluxDBClient

from jaeger_client import Config
from opentracing import Format
import random

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


clientinflux= InfluxDBClient('localhost', 8086, 'root', 'root', 'example')

clientinflux.create_database('example')


tracer=init_tracer('data')

# Flask
app = Flask(__name__)
CORS(app)

coffee_bean=0
tea_leaf=0
water=0
total=0
client=0
coffee_in_progress=0
tea_in_progress=0
root = 'http://127.0.0.1:5003'
fill_coffee_in_progress =  False
fill_water_in_progress =  False
fill_tea_in_progress =  False

def gett():
    return str(time.time())

def call_api(path, header):
    print('call api ' +path)
    urllib3.disable_warnings(InsecureRequestWarning)
    result = requests.get(root+path, headers=header, verify=False)
    # result.raise_for_status()
    return result


@app.route('/state')
def state():
    global tea_leaf,coffee_bean,water,total,client,coffee_in_progress ,tea_in_progress,fill_coffee_in_progress ,fill_water_in_progress,fill_tea_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('state', child_of=parentspan)
    res = {}

    res = {
        'tea_leaf': tea_leaf,
        'coffee_bean': coffee_bean,
        'water': water,
        'total': total,
        'client': client,
        'coffee_in_progress': coffee_in_progress,
        'tea_in_progress': tea_in_progress,
        'fill_coffee_in_progress': fill_coffee_in_progress,
        'fill_water_in_progress': fill_water_in_progress,
        'fill_tea_in_progress': fill_tea_in_progress
    }
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )
    span.finish()
    return response


@app.route('/resource/add/<resource>')
def add_resource(resource):
    print ('add ' + resource)
    global coffee_bean, fill_coffee_in_progress, water, fill_water_in_progress, tea_leaf, fill_tea_in_progress
    parent_span = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add '+resource, child_of=parent_span)
    res = {}

    # if resource == 'coffee':
    cf = False
    cw = False
    # elif resource == 'tea':

    if resource == 'coffee':
        fill = fill_coffee_in_progress
    elif resource == 'tea':
        fill = fill_tea_in_progress
    else:
        fill = fill_water_in_progress

    if not fill:
        fill = True
        if resource == 'coffee':
            fill_coffee_in_progress = True
        elif resource == 'tea':
            fill_tea_in_progress = True
        else:
            fill_water_in_progress = True
        logging.info('filling ' + resource + ' tank')
        t = None

        if resource == 'coffee':
            t2s = random.randint(2500, 3500) /1000
            time.sleep(t2s)
            add = 40
            coffee_bean += 40
            t = coffee_bean
        elif resource == 'tea':
            t2s = random.randint(1500, 2500) /1000
            time.sleep(t2s)
            add = 20
            tea_leaf += 20
            t = tea_leaf
        else:
            t2s = random.randint(4500, 5500) / 1000
            time.sleep(t2s)
            add = 100
            water += 100
            t = water

        json_body = [
            {
                "measurement": "rt",
                "tags": {
                    "type": resource
                },

                "fields": {
                    "resource": t,
                    "movement": add
                }
            }]

        clientinflux.write_points(json_body)

        if resource == 'coffee':
            fill_coffee_in_progress = False
        elif resource == 'tea':
            fill_tea_in_progress = False
        else:
            fill_water_in_progress = False

        logging.info('filled ' + resource + ' tank')
        cf = True

    while ( fill ):
        logging.info('waiting end of ' + resource + ' filling')
        time.sleep(1)
        cw = True
    res = {
           'cw':str(cw),
           'cf':str(cf)
    }
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype = 'application/json'
    )
    span.finish()
    return response


@app.route('/add/coffee')
def add_coffee():
    print ('add coffee')
    global coffee_bean, fill_coffee_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add coffee', child_of=parentspan)
    res = {}

    cf = False
    cw = False

    if not fill_coffee_in_progress:
        fill_coffee_in_progress = True
        logging.info('filling coffee tank')
        time.sleep(random.randint(2500, 3500) / 1000)
        coffee_bean += 40


        json_body = [
            {
                "measurement": "rt",
                "tags": {
                    "type": "coffee"
                },

                "fields": {
                    "resource": coffee_bean,
                    "movement":40
                }
            }
        ]
        clientinflux.write_points(json_body)
        fill_coffee_in_progress = False
        logging.info('filled coffee tank')
        cf = True

    while (fill_coffee_in_progress):
        logging.info('waiting end of tea filling')
        time.sleep(1)
        cw = True
    res = {
           'cw':str(cw),
           'cf':str(cf)
    }
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype = 'application/json'
    )
    span.finish()
    return response


@app.route('/add/tea')
def add_tea():
    print ('add tea')
    global tea_leaf, fill_tea_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add tea', child_of=parentspan)
    res = {}

    tf = False
    tw = False

    if not fill_tea_in_progress:
        fill_tea_in_progress = True
        logging.info('filling teat tank')
        # time.sleep(2)
        time.sleep( random.randint(1500, 2500) / 1000)
        tea_leaf += 20

        json_body = [
            {
                "measurement": "rt",
                "tags": {
                    "type": "tea"
                },

                "fields": {
                    "resource": tea_leaf,
                    "movement": 20
                }
            }
        ]
        clientinflux.write_points(json_body)

        fill_tea_in_progress = False
        logging.info('filled tea tank')
        tf = True

    while (fill_tea_in_progress):
        logging.info('waiting end of tea filling')
        time.sleep(1)
        tw = True
    res = {
           'tw':str(tw),
           'tf':str(tf)
    }
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype = 'application/json'
    )
    span.finish()
    return response

@app.route('/add/water')
def add_water():
    print ('add water')
    global water,fill_water_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add water', child_of=parentspan)
    res = {}

    wf=False
    ww=False

    if not fill_water_in_progress:
        fill_water_in_progress = True
        logging.info('filling water tank')
        time.sleep(3+random.randint(0,200) / 1000)
        water += 100
        json_body = [
            {
                "measurement": "rt",
                "tags": {
                    "type": "water"
                },

                "fields": {
                    "resource": water,
                    "movement": 100
                }
            }
        ]
        clientinflux.write_points(json_body)

        fill_water_in_progress = False
        logging.info('filled water tank')
        wf=True

    while (fill_water_in_progress):
        logging.info('waiting end of water filling')
        time.sleep(1)
        ww=True
    res = {
           'ww':str(ww),
           'wf':str(wf)
    }
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )
    span.finish()
    return response

@app.route('/add/client')
def add_client():
    global tea_leaf, coffee_bean, water, total, client, coffee_in_progress, tea_in_progress, fill_coffee_in_progress, fill_water_in_progress, fill_tea_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add client', child_of=parentspan)
    res = {}

    print ('add client')
    client += 1
    json_body = [
        {
            "measurement": "rt",
            "tags": {
                "type": "client"
            },

            "fields": {
                # "resource": coffee_bean,
                "movement": 1
            }
        }
    ]
    clientinflux.write_points(json_body)

    response = app.response_class(
        response=json.dumps('OK'),
        status=200,
        mimetype='application/json'
    )
    span.finish()
    return response


@app.route('/wip/<action>/<drink>')
def wip(action, drink):
    global tea_leaf, coffee_bean, water, total, client, coffee_in_progress, tea_in_progress, fill_coffee_in_progress, fill_water_in_progress, fill_tea_in_progress
    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('add wip '+drink, child_of=parentspan)
    print ('wip '+action+' '+drink)
    if drink == 'tea':
        tea_in_progress += 1 if action == 'sup' else -1
    else:
        coffee_in_progress += 1 if action == 'sup' else -1

    response = app.response_class(
        response=json.dumps('OK'),
        status=200,
        mimetype='application/json'
    )

    if drink == 'tea':
        p = tea_in_progress
    else:
        p = coffee_in_progress

    json_body = [
        {
            "measurement": "wip",
            "tags": {
                "type": drink
            },

            "fields": {
                "resource": p
            }
        }
    ]
    clientinflux.write_points(json_body)
    span.finish()
    return response

@app.route('/cashin/<payment>')
def cash_in(payment):
    global total
    parent_span = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('cash in', child_of=parent_span)
    print('cash_in '+payment)
    total += 1
    print('total ' + str(total) + ' $')
    response = app.response_class(
        response=json.dumps('OK'),
        status=200,
        mimetype='application/json'
    )
    span.finish()
    return response

@app.route('/consume/<r>')
def consume(r):
    global tea_leaf, coffee_bean, water
    s = 200
    print ('consume '+r)

    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('consume '+r, child_of=parentspan)
    res = {}
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=res)

    error = False
    if r == 'tea':
        if tea_leaf <= 0:
            call_api('/add/tea', res)
            s = 404
            error = True
        else:
            tea_leaf += -1
            json_body = [
                {
                    "measurement": "rt",
                    "tags": {
                        "type": "tea"
                    },

                    "fields": {
                        "resource": tea_leaf,
                        "movement": -1
                    }
                }
            ]
            clientinflux.write_points(json_body)

            time.sleep(random.randint(0, 50) / 1000)
            print('tea '+str(tea_leaf))
    elif r == 'coffee':
        if coffee_bean <= 0:
            call_api('/add/coffee', res)
            s = 404
            error = True
        else:
            coffee_bean += -1
            json_body = [
                {
                    "measurement": "rt",
                    "tags": {
                        "type": "coffee"
                    },

                    "fields": {
                        "resource": coffee_bean,
                        "movement": -1
                    }
                }
            ]
            clientinflux.write_points(json_body)

            time.sleep(random.randint(0, 50) / 1000)
            print('coffee ' + str(coffee_bean))
    else:
        if water <= 0:
            call_api('/add/water', res)
            s=404
            error=True
        else:
            water += -1
            json_body = [
                {
                    "measurement": "rt",
                    "tags": {
                        "type": "water"
                    },

                    "fields": {
                        "resource": water,
                        "movement": -1
                    }
                }
            ]
            clientinflux.write_points(json_body)

            time.sleep(random.randint(0, 50) / 1000)
            print('water ' + str(water))
    span.set_tag('error', error)
    res = {}
    response = app.response_class(
        response=json.dumps(res),
        status=s,
        mimetype='application/json'
    )
    span.finish()
    return response


@app.route('/revert/<r>')
def revert(r):
    global tea_leaf, coffee_bean, water
    s = 200
    print ('revert'+r)

    parent_span = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('revert '+r, child_of=parent_span)
    res = {}
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=res)

    error = False
    nb=None
    if r == 'tea':
        tea_leaf += 1
        nb = tea_leaf
        print('tea '+str(tea_leaf))
    elif r == 'coffee':
        coffee_bean += 1
        nb = coffee_bean
        print('coffee ' + str(coffee_bean))
    else:
        water += 1
        nb = water
        print('water ' + str(water))

    json_body = [
                {
                    "measurement": "rt",
                    "tags": {
                        "type": r
                    },

                    "fields": {
                        "resource": nb,
                        "movement": 1
                    }
                }
            ]
    clientinflux.write_points(json_body)
    time.sleep(random.randint(0, 50) / 1000)
    res = {}
    response = app.response_class(
        response=json.dumps(res),
        status=s,
        mimetype='application/json'
    )
    span.finish()
    return response

# Run server
app.run(port=5003, host='0.0.0.0')