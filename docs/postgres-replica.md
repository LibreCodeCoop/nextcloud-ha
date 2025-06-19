# Setup de replicação no postgres
- Este manual exemplifica como fazer a configuração de replicação no postgres, de maneira manual.
- São considerados ao menos 2 servidores, mas, podem ser adicionados mais.

- **Notas importantes**:
  ```bash
  - a leitura e escrita é feita apenas no principal;
  - se o primário falhar, será necessário promover a replica manualmente;
  ```
  
## Servidor primário
- Crie o arquivo `compose.yml`:

```
networks:
  postgres:
    external: true
    name: postgres
  reverse-proxy:
    external: true
    name: reverse-proxy
    
services:
  postgres:
    ports:
      - 5432:5432
    container_name: postgres-postgres-1
    image: postgres:16-alpine
    restart: always
    volumes:
      - ./volumes/postgres/data:/var/lib/postgresql/data
      - ./.docker/postgres/init-user-db.sh:/docker-entrypoint-initdb.d/init-user-db.sh
      - ./postgresql.conf:/var/lib/postgresql/postgresql.conf:rw
      - ./pg_hba.conf:/var/lib/postgresql/data/pg_hba.conf:rw
    networks:
      - postgres
    environment:
      - POSTGRES_PASSWORD
      - POSTGRES_DB
      - POSTGRES_USER
      - TZ
      - POSTGRES_REPLICATION_USER
      - POSTGRES_REPLICATION_PASSWORD

```

- Crie o script `init-replication-user.sh` responsável por criar o usuário de replicação assim que o container for inicializado:
```bash
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $POSTGRES_REPLICATION_USER WITH REPLICATION ENCRYPTED PASSWORD '$POSTGRES_REPLICATION_PASSWORD';
    SELECT pg_create_physical_replication_slot('replication_slot');
EOSQL
```


- Crie o arquivo `.env` e substitua as :
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=example
POSTGRES_DB=postgres

POSTGRES_REPLICATION_USER=usuario_replicacao
POSTGRES_REPLICATION_PASSWORD=senha_replicacao
TZ=America/Sao_Paulo

```

- Crie o arquivo `postgresql.conf` com o seguinte conteúdo:
```
# Configurações básicas do Postgres
listen_addresses = '*'
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB

# Configurações de réplica
wal_level = replica  # Replicacao
max_wal_senders = 10  # Número máximo de conexões para replicação
wal_keep_size = 1GB   # Quantidade de segmentos WAL para replicação
max_replication_slots = 10  # Número máximo de slots de replicação

```

- No arquivo `pg_hba.conf` é especificado quais hosts podem se conectar a quais bancos.
- No exemplo abaixo, quem acessa o banco é a aplicação, que está no mesmo servidor que o banco, e o usuário de replicação, que está em outro servidor com outro endereço IP.

```
# TYPE  DATABASE        USER                    ADDRESS                        METHOD
local   all             all                                                    trust
host    all             all                     127.0.0.1/32                   trust
host 	  all		          all		                  172.0.0.0/8		                 trust
host    all             usuario_replicacao      IP_Servidor_Secundário/32      md5
```

- Caso seja necessário replicar para outro servidor, acrescente outra linha modificando o endereço do mesmo.

***Nota: está sendo feita a replicação de todos os bancos. Em caso de replica somente de um banco específico, mude a variável `all` para o nome do seu banco**

- Inicie o container: `docker compose up -d`

## Servidor secundário
- O servidor secundário deve estar em modo de espera de modo a receber a replicação do primário e não aceitar escrita no banco para evitar inconsistências.
- Para inicializar a réplica, o primeiro passo é fazer uma cópia 
- Crie o arquivo `.env`

```
networks:
  postgres:
    external: true
    name: postgres
services:
  postgres:
    container_name: postgres
    image: postgres:16-alpine
    restart: always
    volumes:
      - ./volumes/postgres/data:/var/lib/postgresql/data
      - ./volumes/replica-postgresql.conf:/etc/postgresql/postgresql.conf
      - ./pg_hba.conf:/var/lib/postgresql/data/pg_hba.conf 
      - ./setup-replica.sh:/docker-entrypoint-initdb.d/setup-replica.sh
    networks:
      - postgres
    environment:
      - POSTGRES_PASSWORD
      - POSTGRES_REPLICATION_USER
      - POSTGRES_REPLICATION_PASSWORD
      - POSTGRES_PRIMARY_HOST
      - POSTGRES_PRIMARY_PORT
    ports:
      - "5432:5432"

```
