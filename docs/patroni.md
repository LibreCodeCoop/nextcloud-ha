### Patroni
#### Configuração de Cluster Standby entre Data Centers
- Para fazer o cluster do Patroni do datacenter 1 para o datacenter 2, será utilizada a característica Standby Cluster. 
- Segundo a documentação:
    - É um cluster que não tem nenhum nó Postgres primário em execução (nenhum membro de leitura/gravação).
    - Esses clusters replicam dados de outro cluster e são úteis para replicação entre data centers.
    - Haverá um líder no cluster (um standby) responsável por replicar as alterações de um nó Postgres remoto.
    - Os outros standbys serão configurados com replicação em cascata a partir desse líder.

- Observação: O cluster standby não conhece o cluster de origem e pode usar restore_command ou um DCS (etcd, consul) independente.

- Existem configurações que são realizadas apenas na inicialização do cluster. Estas estão na seção `bootstrap` do arquivo `postgres0.yml`
- Se necessário alterar alguma configuração após, utilizar o comando `patronictl edit-config`.

#### Configuração
- Para fazer a instalação é possível utilizar o role do ansible chamado `patroni`, o qual está no diretório `roles`. 

##### Comandos úteis
- Acessar e listar cluster: `docker exec patroni1 patronictl list`
- Mostre as mudanças a cada 2 segundos: `docker exec patroni1 patronictl list -W`


##### Gerenciamento de Falhas
- Se um membro falhar:
    - Não reinicie o PostgreSQL diretamente. Use patronictl ou a API REST.
    - Apenas o Patroni deve gerenciar o PostgreSQL.

- Exemplo de cluster com falha:
```bash
+ Cluster: nome-do-cluster (7483271224010649624) --------+----+-----------+
| Member   | Host       | Role    | State        | TL | Lag in MB |
+----------+------------+---------+--------------+----+-----------+
| patroni1 | 172.23.0.5 | Leader  | running      | 91 |           |
| patroni2 | 172.23.0.6 | Replica | starting     |    |   unknown |
| patroni3 | 172.23.0.3 | Replica | start failed |    |   unknown |
+----------+------------+---------+--------------+----+-----------+
```

- É possível reiniciar o membro que está com falha com o seguinte comando:
`patronictl restart nome-do-cluster membro --scheduled now --force`

- Também é possível reconstruir o membro que está em `standby`:
`patronictl reinit nome-do-cluster membro --force`

###### Informações do Cluster
- Ver versão do Patroni: `patronictl version cluster`
- Ver status de um membro: `docker compose exec patroni1 curl http://172.23.0.3:8008`
- Tirar o cluster do modo de manutenção: `docker compose exec patroni1 patronictl resume`
- Mostrar as configurações dinâmicas: `docker compose exec patroni1 show-config`

###### Monitoramento
- O Patroni expõe endpoints úteis na API REST:
    - /metrics: Métricas no formato Prometheus.
    - /patroni: Status do cluster em JSON.

- Esses endpoints são utilizados para implementar verificações de monitoramento.

###### Teste de failover
- Quando o cluster está saudável, é possível realizar um teste de failover:
`patronictl switchover nome-do-cluster --leader líder-atual --candidate novo-candidato-a-lider`

###### Backup e Restauração
- Para backup do banco de dados utilizamos o utilitário `pg_dumpall`:
`docker exec patroni1 pg_dumpall -c -U postgres >  dump.sql`

- Para importar utilizamos o utilitário `pg_restore`:
`docker exec patroni1 pg_restore -C -j 4 dump.sql`

###### Resolução de problemas
- 1) Cluster sem líder
- Solução: forçar a eleição de um líder.
`patronictl failover nome-do-cluster --candidate candidato-a-lider --force`
