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
import zipkin

from jaeger_client import Config
from opentracing import Format
from opentracing import scope
import opentracing

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
    t = config.initialize_tracer()


    return t

tracer=init_tracer('buy')


app = Flask(__name__)
CORS(app)

root = 'http://127.0.0.1'

def gett():
    return str(time.time())


def call_api(port,path, header):
    print('call api ' + path)
    urllib3.disable_warnings(InsecureRequestWarning)
    result = requests.get(root+':'+str(port)+path, headers=header, verify=False)
    # result.raise_for_status()
    return result


@app.route('/buy/<drink>/<payment>/<name>')
def buy_drink(drink, payment, name):
    span = tracer.start_span('transaction')
    span.set_tag('drink', drink)
    span.set_tag('customer', name)
    span.set_tag('payment', payment)

    res = {}
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=res)
    span.finish()

    if True:
        print (name+' buys '+drink)
        call_api(5003, '/wip/add/'+drink, res)
        call_api(5003, '/add/client', res)
        r = call_api(5001, '/produce/'+drink, res)
        if r.status_code == 200:
            call_api(5002, '/bill/' + payment + '/' + name, res)
            span.set_tag('error', False)
        else:
            span.set_tag('error', True)
        response = app.response_class(
            response=json.dumps(res),
            status=r.status_code,
            mimetype='application/json'
        )

        call_api(5003, '/wip/sup/'+drink, res)
        transfert.finish()
        return response


# Run server
# app.run(port=5000, host='0.0.0.0')