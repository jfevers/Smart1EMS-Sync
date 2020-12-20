FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/* ./
VOLUME /EMS/config /EMS/data

#EXPOSE 5000
CMD [ "python", "./SyncSmart1EMS.py", "/EMS/config" ]
