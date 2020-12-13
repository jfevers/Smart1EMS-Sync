FROM python:alpine3.7
COPY src/*.py /app
WORKDIR /app
#RUN pip install -r requirements.txt
#EXPOSE 5000
CMD python ./Smart1Xml2Mqtt.py
