# etcd
- O etcd é um repositório de chave-valor confiável e distribuído para os dados mais críticos de um sistema distribuído, com foco em:

Simples: API bem definida e voltada para o usuário (gRPC)
Seguro: TLS automático com autenticação opcional por certificado de cliente
Rápido: benchmark de 10.000 gravações/seg
Confiável: distribuído corretamente usando Raft

- O etcd é escrito em Go e usa o algoritmo de consenso Raft para gerenciar um banco de dados chave/valor replicado de alta disponibilidade.

# história
**2013-06**
Commit Inicial,
Contribuição da CoreOS

**2014-06**
Kubernetes V0.4,
10x comunidade

**2015-02**
Primeira Versão Estável do etcd V2.0,
Protocolo de consistência Raft,
1.000 escritas/segundo

**2017-01**
Novas APIs,
Proxy gRPC de leitura linearizada rápida

**2018-11**
Incubação CNCF,
30+ projetos usando etcd,
400+ grupos de contribuição,
9 mantenedores de 8 empresas

**2019**
etcd V3.4,
Membro "Learner",
Leitura totalmente concorrente,
Melhorias de desempenho

# algoritmo raft
- Raft é um algorítmo de consenso distribuído, ou seja, ele garante que os dados sejam replicados com consistência num sistema distribuído.
- Consiste em três partes principais:
    1. Eleição de Líder: um dos nós do sistema é eleito como líder e todos seguem o mesmo. Ele quem controla as operações de escrita no sistema. Isso evita que um nó que está em espera processe dados, por exemplo.
    2. Replicação de Logs:
    3. Segurança da Eleição:



# etcd em docker
- É necessário export a API do etcd para "fora" docontainer, então defina o IP que será acessível a API:
** Nota: é possível criar um rede no docker para interligar os containers e referenciá-los pelo nome **
```bash
export HostIP="10.13.0.20"
```
- Crie o arquivo `compose.yml`:
```bash
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.20
    container_name: etcd
    restart: unless-stopped
    ports:
      - "2380:2380"
      - "2379:2379"
    volumes:
      - "/usr/share/ca-certificates/:/etc/ssl/certs"
    command: >
      /usr/local/bin/etcd
      --name etcd
      --advertise-client-urls http://${HostIP}:2379
      --listen-client-urls http://0.0.0.0:2379
      --initial-advertise-peer-urls http://${HostIP}:2380
      --listen-peer-urls http://0.0.0.0:2380
      --initial-cluster-token etcd-cluster-1
      --initial-cluster etcd=http://${HostIP}:2380
      --initial-cluster-state new
    
    environment:
      - HostIP=${HostIP}
```

- A partir do seu terminal, para verificar quem faz parte do cluster:
```bash
docker compose exec etcd etcdctl member list -w table
```

# etcd com ssl
