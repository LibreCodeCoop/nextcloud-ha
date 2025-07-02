# Setup de replicação no postgres
- Este manual exemplifica como fazer a configuração de replicação no postgres, de maneira manual.
- São considerados ao menos 2 servidores, mas, podem ser adicionados mais.

- Nota: a leitura e escrita é feita apenas no principal.

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


- Crie o arquivo `.env` e substitua as variáveis:
```bash
POSTGRES_USER=postgres #Nome do usuário do postgres
POSTGRES_PASSWORD=example #Senha do usuário - Alterar
POSTGRES_DB=postgres #Nome do banco de dados

POSTGRES_REPLICATION_USER=usuario_replicacao #Nome do usuário de replicação
POSTGRES_REPLICATION_PASSWORD=senha_replicacao #Senha do usuário de replicação
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

- Verifique que o usuário foi criado: `docker exec -ti postgres-postgres-1 psql -U postgres -c '\du;'`


## Servidor secundário
- O servidor secundário deve estar em modo de espera de modo a receber a replicação do primário e não aceitar escrita no banco para evitar inconsistências.
- Para inicializar a réplica, o primeiro passo é fazer uma cópia do primário. 

- Crie o arquivo `.env` com as variáveis de acordo com seu ambiente:
```bash
POSTGRES_PASSWORD= #Senha do banco atual
POSTGRES_PRIMARY_HOST= #Endereço IP ou DNS do servidor primário
POSTGRES_PRIMARY_PORT=5432 #Se a porta for diferente da padrão, alterar
POSTGRES_REPLICATION_USER= #Nome do usuário de replicação - precisa ser o mesmo que no servidor primário
POSTGRES_REPLICATION_PASSWORD= # Senha do usuário de replicação - precisa ser o mesmo que no servidor primário

```

- Vamos utilizar o comando `pg_basebackup` para fazer uma cópia inicial do banco de dados que está no servidor primário.

- Primeiro vamos limpar o diretório de dados: `rm -rf ./volumes/postgres/data/*`
- Vamos usar o comando `source` com o argumento `.env` para usar as variáveis no comando posterior.
- Depois, vamos criar um container temporário para rodar o comando `pg_basebackup`:
```bash
docker run --rm -v ./volumes/postgres/data:/var/lib/postgresql/data postgres:16-alpine \
  bash -c "PGPASSWORD=$POSTGRES_REPLICATION_PASSWORD pg_basebackup -h $POSTGRES_PRIMARY_HOST -p $POSTGRES_PRIMARY_PORT -U $POSTGRES_REPLICATION_USER -D /var/lib/postgresql/data -P -R -v --wal-method=stream"
```

- O parâmetro `-R` se encarregará de criar o arquivo `standby.signal`, o qual é responsável por indicar ao postgres que esta instância é uma réplica em espera.

- Após essa parte, vamos criar arquivo resposável por executar o banco de dados.
- Crie o arquivo `compose.yml`:


```bash
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
      - ./volumes/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./pg_hba.conf:/var/lib/postgresql/data/pg_hba.conf 
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

- Suba o container: `docker compose up -d`


