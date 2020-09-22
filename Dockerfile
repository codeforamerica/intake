FROM python:3

RUN mkdir /usr/src/app
WORKDIR /usr/src/app
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
	apt-get -y install build-essential wget software-properties-common

RUN wget -qO - https://deb.nodesource.com/setup_12.x | bash - && \
	apt-get -y install nodejs
    
RUN	wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add - && \
    add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/ && \
	apt-get update && \
	apt-get install -y adoptopenjdk-8-hotspot
	