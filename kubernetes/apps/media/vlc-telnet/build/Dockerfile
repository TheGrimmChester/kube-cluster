FROM ubuntu:24.04

COPY startup.sh /home/vlcuser/startup.sh

RUN chmod +x /home/vlcuser/startup.sh;

RUN apt-get update && apt-get upgrade -y;

RUN apt-get install -y python3-minimal;
RUN apt-get install -y linux-sound-base;
RUN apt-get install -y alsa-base;
RUN apt-get install -y alsa-utils;
RUN apt-get install -y vlc;
RUN useradd --groups audio --shell /bin/sh vlcuser;
RUN apt-get clean autoclean
RUN apt-get autoremove --yes
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/

EXPOSE 4212

WORKDIR /home/vlcuser/

ENTRYPOINT ["sh", "/home/vlcuser/startup.sh"]
