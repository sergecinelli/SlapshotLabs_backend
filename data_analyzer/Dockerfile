FROM public.ecr.aws/docker/library/python:3.13

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y supervisor && mkdir -p /var/log/supervisor

COPY game_events_analyzer.conf /etc/supervisor/conf.d/supervisord.conf

COPY requirements.txt /home/
RUN python3 -m pip install -r /home/requirements.txt && rm /home/requirements.txt

RUN mkdir /home/data_analyzer

WORKDIR /home/data_analyzer

COPY game_events_analyzer.py constants.py models.py ./

CMD [ "/usr/bin/supervisord","-c","/etc/supervisor/conf.d/supervisord.conf" ]
