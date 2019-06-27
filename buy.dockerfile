FROM local/common-python:1.1

COPY ./1-buy.py .

CMD [ "python", "./1-buy.py" ]

