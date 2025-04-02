# etcd



# Docker
- Docker-compose do servidor 1:
  ```bash
  ```


- Adicionar o outro nó ao cluster:
  ```bash
  docker compose exec -it etcd etcdctl member add server2 http://187.57.255.128:2380
  ```


- Docker-compose do servidor 2:

  ```bash
  ```


- Verificar o estado do cluster:
    ```bash
    docker compose exec etcd etcdctl cluster-health
    ```

# Resolvendo erros/warnings

- `etcdserver: server is likely overloaded`
- Será necessário mudar o tempo do batimento do cluster ETCD e o tempo para
  eleição de um novo líder com os seguintes parâmetros:
    ```bash
    --heartbeat-interval 250
    --election-timeout 1250
    ```

- Após inicializado o cluster no servidor 1, é possível adicionar outros membros ao cluster:
    ```bash
    docker compose exec -it etcd1 etcdctl member add server2 --peer-urls=http://IP-SERVIDOR-2:2380
    ```