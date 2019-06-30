FROM python:3.6.8-alpine

RUN pip3 install flask
RUN pip3 install flask-cors
RUN pip3 install kafka-python 
RUN pip3 install jaeger-client
RUN pip3 install urllib3
RUN pip3 install requests
RUN pip3 install zipkin
RUN pip3 install influxdb

COPY code code
