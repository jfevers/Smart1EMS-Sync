FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/Smart1Xml2Mqtt.py ./

#RUN pip install -r requirements.txt
#EXPOSE 5000
CMD [ "python", "./Smart1Xml2Mqtt.py" ]
