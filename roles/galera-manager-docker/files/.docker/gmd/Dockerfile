FROM ubuntu:20.04 AS gmd

RUN apt-get update && apt-get install -y ca-certificates curl gnupg openssh-client

COPY galera-manager.list /etc/apt/sources.list.d/
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv BC19DDBA && \
    apt-get update && apt-get install -y galera-manager

COPY entrypoint.sh /
RUN chmod 0755 /entrypoint.sh

ENV GMD_CONFIG_DIR=/var/lib/gmd
ENV GMD_LOGS_DIR=/var/log/gmd

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gmd", "run", "--bind-address", ":8080"]
