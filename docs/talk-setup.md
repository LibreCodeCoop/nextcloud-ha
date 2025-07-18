# Nextcloud Talk - Backend de Alto Desempenho (HPB)

## Visão Geral

Este guia explica como configurar um Backend de Alto Desempenho (HPB) para o Nextcloud Talk usando contêineres Docker. O HPB melhora significativamente a performance de videoconferências com múltiplos participantes.

### Arquitetura do Sistema

O HPB consiste em três componentes principais:

1. **Serviço STUN/TURN** - Gerencia conectividade através de NAT/firewall
2. **Serviço de Sinalização** - Coordena comunicação WebRTC entre participantes
3. **Servidor Janus** - Processa streams de áudio e vídeo

### Repositório de Referência
- [Contêineres Docker](https://github.com/LibreCodeCoop/nextcloud-docker)

---

## Pré-requisitos

### DNS
Configure as seguintes entradas no seu provedor de DNS:
- `turn.seudominio.tld`
- `talksignaling.seudominio.tld`
- `janus.seudominio.tld`

### Aplicativos Nextcloud
Instale o aplicativo `talk` na sua instância Nextcloud.

### Portas Necessárias
Certifique-se de que as seguintes portas estejam liberadas no firewall:
```
3478/tcp/udp   # TURN/STUN
3479/tcp/udp   # TURN adicional
5349/tcp/udp   # TURNS (TLS)
5350/tcp/udp   # TURNS adicional
```

---

## Etapa 1: Geração de Segredos

O HPB requer três segredos únicos para autenticação:

### Gerando Segredos
```bash
# Gere 3 segredos diferentes usando openssl
openssl rand --hex 32
```

Execute o comando 3 vezes para obter:
- **TURN_SECRET**: Autenticação do servidor TURN
- **SIGNALING_SECRET**: Autenticação do serviço de sinalização  
- **INTERNAL_SECRET**: Comunicação interna entre componentes

### Exemplo de Segredos
```bash
TURN_SECRET=86a057a959534eb761b20afb4122da6b5475a5f8db20ba16abbb91c65132ca03
SIGNALING_SECRET=f7d8e9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8
INTERNAL_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

⚠️ **IMPORTANTE**: Substitua os valores de exemplo pelos seus próprios segredos gerados.

---

## Etapa 2: Configuração do Servidor TURN (Coturn)

### Configuração do Contêiner
```yaml
networks:
  reverse-proxy:
    external: true
    name: reverse-proxy
  redis:
    external: true
    name: redis
  internal:
    external: true
    name: internal

services:
  coturn:
    image: coturn/coturn:debian
    container_name: coturn-talk
    ports:
      - "3478:3478/tcp"
      - "3478:3478/udp"
      - "3479:3479/tcp"
      - "3479:3479/udp"
      - "5349:5349/tcp"
      - "5349:5349/udp"
      - "5350:5350/tcp"
      - "5350:5350/udp"
    environment:
      - VIRTUAL_HOST=talk-turn.domain.tld
      - LETSENCRYPT_HOST=talk-turn.domain.tld
      - LETSENCRYPT_EMAIL=email@domain.tld
      - VIRTUAL_PORT=3478
    networks:
      - internal
      - redis
      - reverse-proxy
    volumes:
      - ./coturn/turnserver.conf:/etc/coturn/turnserver.conf
    restart: unless-stopped
```

### Arquivo de Configuração (turnserver.conf)
```conf
# Configuração básica
listening-port=3478
tls-listening-port=5349
realm=turn.seudominio.tld
server-name=turn.seudominio.tld

# Autenticação
use-auth-secret
static-auth-secret=SEU_TURN_SECRET_AQUI

# Rede
external-ip=SEU_IP_PUBLICO_AQUI
listening-ip=0.0.0.0

# Segurança
no-multicast-peers
no-cli
no-tlsv1
no-tlsv1_1

# Logging
log-file=/var/log/coturn/turn.log
verbose
```

### Teste do Servidor TURN
Use a ferramenta online para testar:
- URL: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
- STUN/TURN URI: `turn:turn.seudominio.tld:3478`
- Username: `user-test`
- Password: `SEU_TURN_SECRET`


Clique em `Add server` e depois `Gather Candidates`.
O IP e porta devem ser listados.

---

## Etapa 3: Configuração do Serviço de Sinalização
### Arquivos de configuração
Crie o arquivo `volumes/hpb/config/server.conf` com o seguinte conteúdo (altere conforme necessário):

```bash
[http]
# IP and port to listen on for HTTP requests.
# Comment line to disable the listener.
listen = 0.0.0.0:8080


[app]
# Set to "true" to install pprof debug handlers.
# See "https://golang.org/pkg/net/http/pprof/" for further information.
debug = false

# Comma separated list of trusted proxies (IPs or CIDR networks) that may set
# the "X-Real-Ip" or "X-Forwarded-For" headers. If both are provided, the
# "X-Real-Ip" header will take precedence (if valid).
# Leave empty to allow loopback and local addresses.
trustedproxies = 172.19.0.1/16

[sessions]
# Secret value used to generate checksums of sessions. This should be a random
# string of 32 or 64 bytes.
hashkey = ${RANDOM-STRING}

# Optional key for encrypting data in the sessions. Must be either 16, 24 or
# 32 bytes.
# If no key is specified, data will not be encrypted (not recommended).
blockkey = ${RANDOM-STRING}

[clients]
# Shared secret for connections from internal clients. This must be the same
# value as configured in the respective internal services.
internalsecret = ${INTERNAL_SECRET}

[backend]
# Type of backend configuration.
# Defaults to "static".
#
# Possible values:
# - static: A comma-separated list of backends is given in the "backends" option.
# - etcd: Backends are retrieved from an etcd cluster.
# backendtype = static

# For backend type "static":
# Comma-separated list of backend ids from which clients are allowed to connect
# from. Each backend will have isolated rooms, i.e. clients connecting to room
# "abc12345" on backend 1 will be in a different room than clients connected to
# a room with the same name on backend 2. Also sessions connected from different
# backends will not be able to communicate with each other.
backends = backend

# For backend type "etcd":
# Key prefix of backend entries. All keys below will be watched and assumed to
# contain a JSON document with the following entries:
# - "url": Url of the Nextcloud instance.
# - "secret": Shared secret for requests from and to the backend servers.
#
# Additional optional entries:
# - "maxstreambitrate": Maximum bitrate per publishing stream (in bits per second).
# - "maxscreenbitrate": Maximum bitrate per screensharing stream (in bits per second).
# - "sessionlimit": Number of sessions that are allowed to connect.
#
# Example:
# "/signaling/backend/one" -> {"url": "https://nextcloud.domain1.invalid", ...}
# "/signaling/backend/two" -> {"url": "https://domain2.invalid/nextcloud", ...}
#backendprefix = /signaling/backend

# Allow any hostname as backend endpoint. This is extremely insecure and should
# only be used while running the benchmark client against the server.
allowall = false

# Common shared secret for requests from and to the backend servers. Used if
# "allowall" is enabled or as fallback for individual backends that don't have
# their own secret set.
# This must be the same value as configured in the Nextcloud admin ui.
#secret = the-shared-secret-for-allowall

# Timeout in seconds for requests to the backend.
timeout = 20

# Maximum number of concurrent backend connections per host.
# changed from 8 to 20
connectionsperhost = 40

# If set to "true", certificate validation of backend endpoints will be skipped.
# This should only be enabled during development, e.g. to work with self-signed
# certificates.
#skipverify = false

# For backendtype "static":
# Backend configurations as defined in the "[backend]" section above. The
# section names must match the ids used in "backends" above.
#[backend-1]
[backend]
# URL of the Nextcloud instance
url = https://${NEXTCLOUD-URL}

# Shared secret for requests from and to the backend servers. Leave empty to use
# the common shared secret from above.
# This must be the same value as configured in the Nextcloud admin ui.

secret = ${SIGNAL-SECRET}
# Limit the number of sessions that are allowed to connect to this backend.
# Omit or set to 0 to not limit the number of sessions.
#sessionlimit = 10

# The maximum bitrate per publishing stream (in bits per second).
# Defaults to the maximum bitrate configured for the proxy / MCU.
#maxstreambitrate = 1048576

# The maximum bitrate per screensharing stream (in bits per second).
# Defaults to the maximum bitrate configured for the proxy / MCU.
#maxscreenbitrate = 2097152

#[another-backend]
# URL of the Nextcloud instance
#url = https://cloud.otherdomain.invalid

# Shared secret for requests from and to the backend servers. Leave empty to use
# the common shared secret from above.
# This must be the same value as configured in the Nextcloud admin ui.
#secret = the-shared-secret

[nats]
# Url of NATS backend to use. This can also be a list of URLs to connect to
# multiple backends. For local development, this can be set to "nats://loopback"
# to process NATS messages internally instead of sending them through an
# external NATS backend.
url = nats://cloud.domain.tld:4222

[mcu]
# The type of the MCU to use. Currently only "janus" and "proxy" are supported.
# Leave empty to disable MCU functionality.
type = janus

# For type "janus": the URL to the websocket endpoint of the MCU server.
# For type "proxy": a space-separated list of proxy URLs to connect to.
url = ws://cloud.domain.tld:8188


# The maximum bitrate per publishing stream (in bits per second).
# Defaults to 1 mbit/sec.
# For type "proxy": will be capped to the maximum bitrate configured at the
# proxy server that is used.
maxstreambitrate = 1048576
#maxstreambitrate = 56242
# The maximum bitrate per screensharing stream (in bits per second).
# Default is 2 mbit/sec.
# For type "proxy": will be capped to the maximum bitrate configured at the
# proxy server that is used.
maxscreenbitrate = 2097152
#maxscreeenbitrate = 1000000


[turn]
# API key that the MCU will need to send when requesting TURN credentials.
apikey = ${TURN-API-KEY}

# The shared secret to use for generating TURN credentials. This must be the
# same as on the TURN server.
secret = ${TURN-SECRET}

# A comma-separated list of TURN servers to use. Leave empty to disable the
# TURN REST API.
servers = turn:cloud.domain.tld:3478?transport=udp,turn:cloud.domain.tld:3478?transport=tcp
```

Adicione o arquivo `volumes/hbp/config/gnatsd.conf` as seguintes configurações:
```bash
cluster {

	port: 4244  # port for inbound route connections

	routes = [
		# You can add other servers here to build up a cluster.
		#nats-route://otherserver:4244
	]

}
```


### Configuração do Contêiner
```yaml
  spreedbackend:
    image: mwalbeck/nextcloud-spreed-signaling
    volumes:
      - ./volumes/hpb/config/server.conf:/config/server.conf
      - ./volumes/hpb/ssl/:/etc/nginx/ssl/
    restart: unless-stopped
    environment:
      - JANUS_URL=janus.tld
      - USE_JANUS=1
      - VIRTUAL_HOST=talk-signaling.tld
      - LETSENCRYPT_HOST=talk-signaling-poc.tld
      - LETSENCRYPT_EMAIL=adm@librecode.coop
      - VIRTUAL_PORT=8080
    networks:
      - reverse-proxy
      - internal
```

### Teste do Serviço de Sinalização
```bash
curl -i https://talk-signaling.seudominio.tld/api/v1/welcome
```

**Resposta esperada:**
```json
{
  "nextcloud-spreed-signaling": "Welcome",
  "version": "1.3.2~docker"
}
```

---

## Etapa 4: Configuração do Servidor Janus

### Configuração do Contêiner
Arquivo `.docker/janus/Dockerfile`:
```bash
# Modified from https://gitlab.com/powerpaul17/nc_talk_backend/-/blob/dcbb918d8716dad1eb72a889d1e6aa1e3a543641/docker/janus/Dockerfile
FROM alpine:3.20

RUN apk add --no-cache curl autoconf automake libtool pkgconf build-base \
  glib-dev libconfig-dev libnice-dev jansson-dev openssl-dev zlib libsrtp-dev \
  gengetopt libwebsockets-dev git curl-dev libogg-dev

# usrsctp
# 08 Oct 2021
ARG USRSCTP_VERSION=7c31bd35c79ba67084ce029511193a19ceb97447

RUN cd /tmp && \
    git clone https://github.com/sctplab/usrsctp && \
    cd usrsctp && \
    git checkout $USRSCTP_VERSION && \
    ./bootstrap && \
    ./configure --prefix=/usr && \
    make -j$(nproc) && make install

# libsrtp
ARG LIBSRTP_VERSION=2.6.0
RUN cd /tmp && \
    wget https://github.com/cisco/libsrtp/archive/v$LIBSRTP_VERSION.tar.gz && \
    tar xfv v$LIBSRTP_VERSION.tar.gz && \
    cd libsrtp-$LIBSRTP_VERSION && \
    ./configure --prefix=/usr --enable-openssl && \
    make shared_library -j$(nproc) && \
    make install && \
    rm -fr /libsrtp-$LIBSRTP_VERSION && \
    rm -f /v$LIBSRTP_VERSION.tar.gz

# JANUS

#ARG JANUS_VERSION=1.2.2
ARG  JANUS_VERSION=1.2.3
RUN mkdir -p /usr/src/janus && \
    cd /usr/src/janus && \
    curl -L https://github.com/meetecho/janus-gateway/archive/v$JANUS_VERSION.tar.gz | tar -xz && \
    cd /usr/src/janus/janus-gateway-$JANUS_VERSION && \
    ./autogen.sh && \
    ./configure --disable-rabbitmq --disable-mqtt --disable-boringssl && \
    make -j$(nproc) && \
    make install && \
    make configs

WORKDIR /usr/src/janus/janus-gateway-$JANUS_VERSION

CMD [ "janus" ]

```

Arquivo docker-compose:
```yaml
services:
  janus:
    build: .docker/janus
    command: ["janus", "--full-trickle"]
    # Se o servidor tiver um endereço privado, descomente abaixo e substitua por seu IP público.
    # Certifique-se de ter a porta 8088 liberada.
    # command: "janus --full-trickle --nat-1-1=SEU_IP_PUBLICO"
    network_mode: host
    restart: unless-stopped
    environment:
      - VIRTUAL_HOST=janus.domino.tld
      - LETSENCRYPT_HOST=janus.domino.tld
      - LETSENCRYPT_EMAIL=email@domino.tld
```

---

## Etapa 5: Configuração no Nextcloud

### Configurações TURN
Acesse `/settings/admin/talk` no seu Nextcloud:

Clique em `Adicionar servidor de back-end de alto desempenho`.

Preencha com a **URL do servidor de alto desempenho** e o `SIGNALING_SECRET` criado anteriormente. No nosso exemplo `wss://talksignaling.seudominio.tld`.


**Servidor TURN:**
Adicione um novo servidor clicando em `Adicionar um novo servidor TURN`.

- Tipo de TURN: `turn: e turns:`
- URL do servidor TURN: `turn.seudominio.tld:3478`
- Segredo do servidor TURN: `SEU_TURN_SECRET`
- Protocolos: TCP e UDP habilitados

**Servidor TURNS (TLS):**
- URL do servidor TURNS: `turns.seudominio.tld:5349`
- Segredo: `SEU_TURN_SECRET`

### Configurações HPB
**Infraestrutura de Alto Desempenho:**
- URL: `https://talksignaling.seudominio.tld`
- Segredo compartilhado: `SEU_SIGNALING_SECRET`

---

## Solução de Problemas

### Problemas Comuns

#### 1. Erro de Autorização (401)
**Sintoma:**
```
session [...]: realm <cloud.seudominio.tld> user <>: incoming packet message processed, error 401: Unauthorized
```

**Solução:**
- Verifique se o segredo no frontend (Nextcloud) é idêntico ao configurado no backend (Coturn)
- Confirme que não há espaços extras nos segredos

#### 2. Timeout de Conexão
**Sintoma:**
```
Could not send request [...]: context deadline exceeded
```

**Solução:**
- Verifique conectividade de rede entre componentes
- Confirme que as portas estão abertas no firewall
- Verifique se os DNS estão resolvendo corretamente

#### 3. Erro NATS
**Sintoma:**
```
Could not create connection (nats: no servers available for connection)
```

**Solução:**
- Verifique conflitos de nome de contêiner
- Use nomes únicos para os contêineres
- Reinicie os serviços na ordem correta

#### 4. Warnings de SSRC
**Sintoma:**
```
Unknown SSRC, dropping packet (SSRC ...)
```

**Explicação:**
- Isso é normal durante videoconferências
- Indica múltiplos streams de áudio/vídeo sendo processados

---

## Monitoramento e Logs

### Comandos Úteis
```bash
# Verificar logs do Coturn
docker logs coturn-talk -f

# Verificar logs do Signaling
docker logs spreed-signaling -f

# Verificar logs do Janus
docker logs janus-talk -f

# Verificar status dos contêineres
docker ps
```

### Ferramentas de Diagnóstico

#### Firefox WebRTC
- Acesse: `about:webrtc`
- Monitore conexões ativas e estatísticas

#### Teste de Conectividade
```bash
# Teste TURN
curl -v turn.seudominio.tld:3478

# Teste Signaling
curl -v https://talksignaling.seudominio.tld/api/v1/welcome

# Teste Janus
curl -v http://janus.seudominio.tld:8088/janus/info
```

---

## Referências

### Documentação Oficial
- [Nextcloud Talk](https://nextcloud.com/talk/)
- [Coturn Documentation](https://github.com/coturn/coturn)
- [Janus Gateway](https://janus.conf.meetecho.com/)

### Repositórios
- [Nextcloud Docker Images](https://github.com/LibreCodeCoop/nextcloud-docker)
- [Spreed Signaling](https://github.com/mwalbeck/docker-nextcloud-spreed-signaling)
- [Coturn](https://github.com/coturn/coturn)

### Ferramentas de Teste
- [WebRTC Trickle ICE](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/)
- [TURN Server Tester](https://gabrieltanner.org/blog/turn-server/)

---

## Notas de Segurança

1. **Segredos**: Mantenha os segredos seguros e não os compartilhe
2. **Firewall**: Configure adequadamente as regras de firewall
3. **TLS**: Use certificados SSL válidos para todos os endpoints
4. **Monitoramento**: Monitore logs regularmente para detectar problemas
5. **Atualizações**: Mantenha os contêineres atualizados com patches de segurança
