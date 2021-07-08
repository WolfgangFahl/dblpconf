# set base image (host OS)
FROM python:3.9

MAINTAINER Wolfgang Fahl <wf@bitplan.com>

# install some more utilities
RUN apt-get -y update && \
    apt-get -y --no-install-recommends --fix-missing install \
    procps \
    sudo

# set the working directory in the container
WORKDIR /source

# clone the dblpconf software
RUN git clone https://github.com/WolfgangFahl/dblpconf

# change into the source directory
WORKDIR /source/dblpconf

# install necessary requirements
RUN scripts/install

RUN mkdir -p /var/log/dblpconf
RUN touch /var/log/dblpconf/dblpconf.log

CMD scripts/run -s;sleep 1;tail -f /var/log/dblpconf/dblpconf.log
