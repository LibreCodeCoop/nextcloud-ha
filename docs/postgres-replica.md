# Setup de replicação no Postgres
- Este manual exemplifica como fazer a configuração de replicação no postgres, de maneira manual.
- São considerados ao menos 2 servidores, mas, podem ser adicionados mais.

- Nota: a leitura e escrita é feita apenas no principal.

## Conceitos fundamentais de replicação
- Write-Ahead Log(WAL): Garante a integridade dos dados e durabilidade das transações. As transações são registradas em um log de transações, o WAL, antes que sejam gravadas em disco. Na replicação, o WAL é o fluxo de dados que é enviado do servidor primário para os servidores secundários.

- Log Sequence Number(LSN): é um ponteiro para uma localização específica dentro do fluxo do WAL.

- Slots de replicação: recurso que garante que o servidor primário não remova segmentos do WAL que ainda são necessários por uma ou mais réplicas, mesmo que essas réplicas estejam temporariamente desconectadas.

## Tipos de replicação
- No Postgres temos diversas opções de replicação.

- Replicação Física (streaming replication): esse tipo de replicação trabalha no nível do bloco de dados, copiando o fluxo de WAL do primário para as réplicas.
  As réplicas são cópias exatas do primário e são ideais para alta disponibilidade e balanceamento de carga de leitura. É essa replicação que utilizaremos no exemplo.
  Pode ser **assíncrona** ou **síncrona**:

  - **Replicação Assíncrona**: O servidor primário não espera que a réplica confirme o recebimento e a aplicação dos dados do WAL antes de confirmar uma transação.

  - **Replicação Síncrona**: O servidor primário espera que a réplica confirme o recebimento e a gravação dos dados do WAL antes de confirmar uma transação.


- Replicação Lógica: trabalha em um nível superior, replicando alterações de dados com base em sua identidade de replicação (geralmente uma chave primária). Ela usa um modelo de publicação/assinatura, onde um servidor primário (publicador) publica alterações para um ou mais servidores secundários (assinantes). 
  Diferente da replicação física, a replicação lógica permite:

  - Replicar subconjuntos de dados (tabelas específicas, bancos de dados específicos).
  - Replicar entre diferentes versões do PostgreSQL.
  - Replicar entre diferentes arquiteturas de hardware.
  - Maior flexibilidade para transformações de dados durante a replicação.


- Usaremos a replicação física por ser mais simples de configurar.


## Configurações do Servidor Primário
- Para configurar o servidor primário, que será o ponto de escrita e origem dos dados replicados, seguiremos os passos abaixo utilizando Docker Compose para facilitar a criação do ambiente.

1. Estrutura de Arquivos:
- Certifique-se de ter a seguinte estrutura de diretório e arquivos:

```bash
.env
docker-compose.yml
init-replication-user.sh
pg_hba.conf
postgresql.conf
volumes/
└── postgres/
    └── data/ (será criado pelo Docker)
```

2. Arquivo `docker-compose.yml`:
- Crie o arquivo `docker-compose.yml`. Ele define o serviço do Postgres primário, mapeia as portas, volumes e variáveis de ambiente necessárias.

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


3. Crie o script `init-replication-user.sh` responsável por criar o usuário de replicação assim que o container for inicializado:
- Este script será executado na primeira inicialização do container para criar o usuário de replicação e um slot de replicação físico. 

  ```bash
  #!/bin/bash
  set -e

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
      CREATE USER $POSTGRES_REPLICATION_USER WITH REPLICATION ENCRYPTED PASSWORD '$POSTGRES_REPLICATION_PASSWORD';
      SELECT pg_create_physical_replication_slot('replication_slot');
  EOSQL
  ```


4. Crie o arquivo `.env` e substitua as variáveis de acordo com seu ambiente:
  Este arquivo contém as variáveis de ambiente que serão usadas pelo compose.yml e pelo script de inicialização.

  ```bash
  POSTGRES_USER=postgres #Nome do usuário do postgres
  POSTGRES_PASSWORD=example #Senha do usuário - Alterar
  POSTGRES_DB=postgres #Nome do banco de dados

  POSTGRES_REPLICATION_USER=usuario_replicacao #Nome do usuário de replicação
  POSTGRES_REPLICATION_PASSWORD=senha_replicacao #Senha do usuário de replicação
  TZ=America/Sao_Paulo
  ```

5. Crie o arquivo `postgresql.conf` com o seguinte conteúdo, o qual é essencial para a replicação acontecer:
  ```
  # Configurações básicas do Postgres
  listen_addresses = '*' # Permite conexões de qualquer IP. Em produção, restrinja a IPs específicos.
  max_connections = 100
  shared_buffers = 128MB # Ajuste conforme a memória disponível no servidor
  dynamic_shared_memory_type = posix

  # Configurações de Write-Ahead Log (WAL) e Réplica
  wal_level = replica  # Essencial para replicação física. Pode ser 'minimal', 'replica', 'logical', 'archive'.
  max_wal_senders = 10  # Número máximo de processos de envio de WAL (para réplicas).
  wal_keep_size = 1GB   # Quantidade de segmentos WAL a serem mantidos para réplicas. Ajuste conforme a necessidade e o atraso esperado.
  max_replication_slots = 10  # Número máximo de slots de replicação. Deve ser >= ao número de réplicas.

  # Outras configurações importantes para desempenho e recuperação
  checkpoint_timeout = 5min
  max_wal_size = 1GB # Tamanho máximo do arquivo WAL
  min_wal_size = 80MB
  ```

6. No arquivo `pg_hba.conf` é especificado quais hosts podem se conectar a quais bancos.
- No exemplo abaixo, quem acessa o banco é a aplicação, que está no mesmo servidor que o banco, e o usuário de replicação, que está em outro servidor com outro endereço IP.
- Substitua o `usuario_replicação` pelo que foi criado anteriormente e `IP_Servidor_Secundário/32` pelo endereço IP do servidor secundário. 

```
# TYPE  DATABASE        USER                    ADDRESS                        METHOD
local   all             all                                                    trust
host    all             all                     127.0.0.1/32                   trust
host 	  all		          all		                  172.0.0.0/8		                 trust
host    all             usuario_replicacao      IP_Servidor_Secundário/32      md5
```

- Caso seja necessário replicar para outro servidor, acrescente outra linha modificando/acrescentando o endereço da outra réplica.

***Nota: está sendo feita a replicação de todos os bancos. Em caso de replica somente de um banco específico, mude a variável `all` para o nome do seu banco**

7. Inicie o container: `docker compose up -d`

- Verifique se o container foi iniciado corretamente e se o usuário de replicação foi criado: 
  `docker compose exec -ti postgres psql -U postgres -c '\du;'`

- Você deve ver o usuário de replicação listado com o atributo `Replication`.


## Servidor secundário
- O servidor secundário deve estar em modo de espera de modo a receber a replicação do primário e não aceitar escrita no banco para evitar inconsistências.
- Para inicializar a réplica, o primeiro passo é fazer uma cópia do primário. 

1. Crie o arquivo `.env` com as variáveis de acordo com seu ambiente:
  ```bash
  POSTGRES_PASSWORD= #Senha do banco atual
  POSTGRES_PRIMARY_HOST= #Endereço IP ou DNS do servidor primário
  POSTGRES_PRIMARY_PORT=5432 #Se a porta for diferente da padrão, alterar
  POSTGRES_REPLICATION_USER= #Nome do usuário de replicação - precisa ser o mesmo que no servidor primário
  POSTGRES_REPLICATION_PASSWORD= # Senha do usuário de replicação - precisa ser o mesmo que no servidor primário
  ```

2. Cópia inicial dos dados (pg_basebackup)
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


## Verificar a replicação
- Maneiras de verificar a replicação no ambiente:
- No **servidor primário**, para ver as conexões de replicações ativas(substitua conforme o nome do seu container e nome de usuário):
```bash
docker exec -ti postgres-postgres-1 psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```
- A saída deve mostrar as conexões de replicação ativas. Exemplo:
```bash
pid  | usesysid |  usename   | application_name |  client_addr   | client_hostname | client_port |         backend_start         | backend_xmin |   state   |  sent_lsn  | write_lsn  | flush_lsn  | replay_lsn | write_lag | flush_lag | replay_lag | sync_priority | sync_state |          reply_time           
------+----------+------------+------------------+----------------+-----------------+-------------+-------------------------------+--------------+-----------+------------+------------+------------+------------+-----------+-----------+------------+---------------+------------+-------------------------------
 3314 |    16384 | replicator | walreceiver      | 192.168.1.128 |                 |       53852 | 2025-07-02 18:16:28.528077+00 |              | streaming | 0/540BAD70 | 0/540BAD70 | 0/540BAD70 | 0/540BAD70 |           |           |            |             0 | async      | 2025-05-02 18:46:26.971339+00

```


- Na **réplica**, verificar se está em modo de recuperação:
```bash
docker exec -ti postgres-postgres-1 psql -U postgres -c "SELECT pg_is_in_recovery();"
```
- Deve retornar `t` indicando verdadeiro, true. 


- Ver progresso da replicação: 
```bash
ocker exec -ti postgres psql -U postgres -c "SELECT now() AS current_time, pg_last_wal_receive_lsn() AS receive_lsn, pg_last_wal_replay_lsn()  AS replay_lsn pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) AS replay_delay;"
```



## Replica para Primária
- O que fazer quando a réplica precisa assumir o papél de primária e passar a responder as requisições dos clientes?
- Será necessário promover a réplica:
```bash
docker exec -ti postgres-postgres-1 psql -U postgres -c "SELECT pg_promote();"
# ou
docker exec -ti postgres-postgres-1 pg_ctl promote -D /var/lib/postgresql/data
```

- Feito isso, podemos configurar a nossa aplicação para usar esse banco de dados.

### Caminho contrário
- Se o antigo primário voltar a funcionar, devemos realizar o processo utilizando o `pg_basebackup` 
  
  à partir do antigo primário e configurar a replicação para o mesmo.


