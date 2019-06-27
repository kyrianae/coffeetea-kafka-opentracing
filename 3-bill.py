import time
from flask import Flask
from flask import request
import json
from flask_cors import CORS
import logging
from urllib3.exceptions import InsecureRequestWarning
import requests
import urllib3
import random
from jaeger_client import Config
from opentracing import Format


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
    return config.initialize_tracer()


tracer=init_tracer('billing')

app = Flask(__name__)
CORS(app)

root = 'http://127.0.0.1:5003'

def gett():
    return str(time.time())

def call_api(path, header):
    print('call api ' +path)
    urllib3.disable_warnings(InsecureRequestWarning)
    result = requests.get(root+path, headers=header, verify=False)
    # result.raise_for_status()
    return result

@app.route('/bill/<payment>/<name>')
def bill(payment, name):

    parentspan = tracer.extract(
        Format.HTTP_HEADERS,
        request.headers
    )
    span = tracer.start_span('bill', child_of=parentspan)
    span.set_tag('customer', name)
    span.set_tag('payment', payment)

    res = {}
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=res)

    res=call_api('/cashin/'+payment,res)
    span.finish()
    sspan = span = tracer.start_span(payment, child_of=span)

    time.sleep(random.randint(0, 200) / 1000)

    # logging.info('total ' +str(res['total']) + ' $')
    response = app.response_class(
        response=json.dumps({}),
        status=200,
        mimetype='application/json'
    )

    sspan.finish()

    return response

# Run server
app.run(port=5002, host='0.0.0.0')


