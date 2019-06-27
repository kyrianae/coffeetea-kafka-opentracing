import time
from flask import Flask
import json
from flask_cors import CORS
import logging
from urllib3.exceptions import InsecureRequestWarning
import requests
import urllib3
from jaeger_client import Config
from opentracing import Format
from kafka import KafkaProducer

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

bootstraps = "kafka-1:19092,kafka-2:29092,kafka-3:39092"
topic = 'order'


def gett():
    return str(time.time())


server_id="counter-"+gett()


def send_ordering_message(data):
    try:
            producer = KafkaProducer(bootstrap_servers=bootstraps.split(','),
                                     value_serializer=lambda x:
                                     json.dumps(x).encode('utf-8'))
            producer.send(topic, value=data)
            producer.flush()
            return True
    except:
            print("connexion lost")
            return False





# def call_api(port,path, header):
#     print('call api ' + path)
#     urllib3.disable_warnings(InsecureRequestWarning)
#     result = requests.get(root+':'+str(port)+path, headers=header, verify=False)
#     # result.raise_for_status()
#     return result


@app.route('/order/<drink>/<payment>/<name>')
def buy_drink(drink, payment, name):
    span = tracer.start_span('ask for order')
    span.set_tag('drink', drink)
    span.set_tag('customer', name)
    span.set_tag('payment', payment)

    res = {}
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=res)
    span.finish()


    message = {
        'drink': drink,
        'customer': name,
        'payment': payment,
        'counter': server_id,
    }

    tracer.inject(
        span_context=span.context,
        format=Format.TEXT_MAP,
        carrier=message)

    output = send_ordering_message(message)

    # if True:
    #     print (name+' buys '+drink)
    #     call_api(5003, '/wip/add/'+drink, res)
    #     call_api(5003, '/add/client', res)
    #     r = call_api(5001, '/produce/'+drink, res)
    #     if r.status_code == 200:
    #         call_api(5002, '/bill/' + payment + '/' + name, res)
    #         span.set_tag('error', False)
    #     else:
    #         span.set_tag('error', True)
    response = app.response_class(
            response='OK' if output else 'ORDER NOT PASSED',
            status=200 if output else 500,
            mimetype='application/json'
        )
    #
    #     call_api(5003, '/wip/sup/'+drink, res)
    #     transfert.finish()
    return response


# Run server
app.run(port=5000, host='0.0.0.0')