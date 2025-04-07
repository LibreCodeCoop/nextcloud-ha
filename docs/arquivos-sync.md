# Sincronização de arquivos
- Uma ferramenta para sincronização dos arquivos deve ser adotada, de maneira a replicar os dados de um servidor para os demais participantes.
- Essa ferramenta deve: a) Detectar mudanças instantaneamente; b) Minimizar overhead de rede; c) Oferece ecanismos eficientes de transferência; d) Suportam delta-transfer (só enviam as partes modificadas); Entre outras.

- O que levar em conta ao escolher uma tecnologia de sincronização:
- Taxa de transferência
- IOPS
- Escalabilidade
- Resiliência
- Tempo de Recuperação e Plano de recuperação em desastres
- Estratégias de replicação
- Overhead
- Replicação Geográfica

## Ferramentas disponíveis
- Algumas ferramentas para sincronizar dados:

    - [GlusterFS](https://www.gluster.org/)
    - [RBD: https](https://linbit.com/drbd/)
    - [Unison](https://github.com/bcpierce00/unison)
    - [Lsyncd](https://lsyncd.github.io/lsyncd/)


- É possível configurar o Nextcloud para utilizar armazenamento em objeto como seu [primeiro armazenamento](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/primary_storage.html#configuring-object-storage-as-primary-storage
), dispensando o uso de uma pasta localmente.
- Também é possível configurar [múltiplos buckets](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/primary_storage.html#multibucket-object-store) a serem utilizado.

- A fazer: configurar duas ou mais instâncias para utilizar múltiplos buckets.
- Opções object storage:
    - [Seaweedfs](https://github.com/seaweedfs/seaweedfs?tab=readme-ov-file#introduction)
    - [Garage S3](https://garagehq.deuxfleurs.fr/)
    - [MooseFS](https://github.com/moosefs/moosefs)


- Abaixo, uma tabela comparativa produzida por [Grey Skipwith, 2023](https://aaltodoc.aalto.fi/server/api/core/bitstreams/4b0dd60c-cba2-4c01-9972-3dafd81708a4/content)

| | Ceph | GlusterFS | HDFS |
|---|---|---|---|
| Arquitetura | Distribuída | Descentralizada | Centralizada |
| Gerenciamento de Metadados | Múltiplos MDSs | Sem MDS | Um MDS |
| Método de Armazenamento Subjacente | Baseado em Objeto | Baseado em Arquivo | Baseado em Bloco |
| Modelo de Escalabilidade | Horizontal | Horizontal | Horizontal |
| Caso de Uso Principal | Armazenamento Unificado | Sistema de Arquivos | Armazenamento de Big Data |
| Interface de Armazenamento | Arquivo, Bloco, Objeto | Arquivo | Arquivo |



### Garage S3
- "Garage é um armazenamento de dados geodistribuído leve que implementa o protocolo de armazenamento de objetos Amazon S3. Ele permite que aplicativos armazenem grandes blobs, como fotos, vídeos, imagens, documentos, etc., em uma configuração redundante de vários nós. O S3 é versátil o suficiente para também ser usado para publicar um site estático"
- Características do GarageS3:
a) Habilitado para Internet: feito para vários sites (por exemplo, datacenters, escritórios, residências, etc.) interconectados por meio de conexões regulares de Internet.
b) Autocontido e leve: funciona em qualquer lugar e se integra bem em ambientes existentes para atingir infraestruturas hiperconvergentes.
c) Altamente resiliente: altamente resiliente a falhas de rede, latência de rede, falhas de disco, falhas de administrador de sistema.
d) Simples: simples de entender, simples de operar, simples de depurar.
e) Desempenhos extremos: altos desempenhos restringem muito o design e a infraestrutura; buscamos desempenhos apenas por meio do minimalismo.
f) Extensividade de recursos: não planejamos adicionar recursos adicionais em comparação aos fornecidos pela API S3.
g) Otimizações de armazenamento: codificação de apagamento ou qualquer outra técnica de codificação aumentam a dificuldade de colocar dados e sincronizar; nos limitamos à duplicação.
h) Compatibilidade POSIX/Sistema de arquivos: não pretendemos ser compatíveis com POSIX ou emular qualquer tipo de sistema de arquivos. De fato, em um ambiente distribuído, tais sincronizações são traduzidas em mensagens de rede que impõem restrições severas à implantação.

- Ponto negativo: não faz a checagem de integridade dos dados.

#### Configuração
1 - Copiar a

- Após fazer a instalação, configurar o cluster e adicionar uma chave de acesso ao bucket criado, configure os registros DNS.
- Por exemplo: 
- Entrada 1: 20.180.0.10 -> garage.dominio.com.br.
- Entrada 2: 20.180.0.30 -> garage.dominio.com.br.
- Entrada 3: 20.180.0.60 -> garage.dominio.com.br.


### GlusterFS

- Os servidores usados ​​para criar o pool de armazenamento devem ser resolvíveis pelo nome do host.
- O daemon glusterd deve estar em execução em todos os servidores de armazenamento que você deseja adicionar ao pool de armazenamento. V
- O firewall nos servidores deve ser configurado para permitir acesso à porta 24007.

- No seu serviço de DNS, adicione as entradas do tipo A para os servidores.

- No meu caso cenário:
```
    server1.librecode.coop - 189.x.x.x
    server2.librecode.coop - 177.x.x.x
    server3.librecode.coop - 38.x.x.x
```

#### Terminologia:
- Terminologia utilizada:
```
nó de sondagem - nó que inicia a operação de sondagem
nó sondado - nó que está sendo adicionado ao cluster

A sondagem de peer gluster é uma operação unidirecional. Quando um novo nó é
sondado com seu nome de host, o nó de sondagem sabe sobre o nome de host do
nó sondado e o adiciona ao seu banco de dados. No entanto, o nó sondado
consegue ver apenas o endereço IP do nó de sondagem da conexão de rede.
Portanto, ele registra apenas o endereço IP em seu banco de dados. Para
substituir o endereço IP pelo nome do host, outra operação de sondagem de peer com
nome de host do nó de sondagem pode ser feita a partir do nó sondado.

-Vijay
```

- Idealmente o diretório contendo os arquivos que serão sincronizados devem ficar em outro disco, separado do sistema operacional.

    apt update
    apt install glusterfs-server
    systemctl start glusterd
    systemctl enable glusterd

- No servidor 1:
```
    gluster peer probe servidor2
    gluster peer probe servidor3

```
- No servidor 2, com o comando `gluster peer status`:

```
    # gluster peer status
    Number of Peers: 2

    Hostname: server1.librecode.coop
    Uuid: fa9c3f27-0b60-4718-93bd-b54b79e84e66
    State: Peer in Cluster (Connected)
    Other names:
    server1.librecode.coop

    Hostname: server3.librecode.coop
    Uuid: 3418bdcc-8f9d-4082-993b-121656fcea14
    State: Peer in Cluster (Connected)

```

- Em todos servidores, crie um volume a ser compartilhado:
    `mkdir -p /data/brick1/gv0`

- O próximo passo é criar o volume no gluster, escolhendo o tipo (distribuído, replicado, distribuído replicado, disperso e distribuído dispersado). Neste exemplo vamos escolher o tipo *replicado*, o qual replicará o conteúdo dos volumes.
- Crie o volume no glusterfs (atente-se a opção ``replica 3`` pois deve corresponder ao número de réplicas):
> Nota: Usar apenas 2 volumes não é recomendado pois pode haver o problem de [split-brain](https://docs.gluster.org/en/main/Administrator-Guide/Split-brain-and-ways-to-deal-with-it/). Se decidir usar mesmo assim, use a opção ``force`` ao final do comando.
```
    gluster volume create gv0 replica 3 server1.librecode.coop:/data/brick1/gv0 server2.librecode.coop:/data/brick1/gv0 server3.librecode.coop:/data/brick1/gv0
```
- Inicialize o volume
```
    gluster volume start gv0
```

- Agora vamos precisar montar esse volume no servidor, seguindo essa sintaxe 
```
    mount.glusterfs <IP ou hostname>:<nome_do_volume> <ponto_de_montagem>
```
- O IP ou hostname pode ser de qualquer servidor que esteja presente no cluster.

- No servidor1: 
```
    mkdir /mnt/gluster-gv0
    mount.glusterfs server1.librecode.coop:/gv0 /mnt/gluster-gv0
```
- Se desejar acessar os dados no servidor 2 ou 3, repita o processo acima.

- Verifique que foi montado com sucesso:
- A saída do comando `mount` deve aparecer a seguinte linha:
```
    server1.librecode.coop:/gv5 on /mnt/gluster-gv5 type fuse.glusterfs (rw,relatime,user_id=0,group_id=0,default_permissions,allow_other,max_read=131072)
```

- A saída do comando `gluster volume info`:
```
    Volume Name: gv0
    Type: Replicate
    Volume ID: 93b0fce3-d5a7-4fc2-a6be-798b0f680ce0
    Status: Started
    Snapshot Count: 0
    Number of Bricks: 1 x 2 = 2
    Transport-type: tcp
    Bricks:
    Brick1: server1.librecode.coop:/data/brick1/gv0
    Brick2: server2.librecode.coop:/data/brick1/gv0
    Options Reconfigured:
    cluster.granular-entry-heal: on
    storage.fips-mode-rchecksum: on
    transport.address-family: inet
    nfs.disable: on
    performance.client-io-threads: off
```

- Vamos testar, criando arquivos no volume:
```
    for i in `seq -w 1 100`; do cp -rp /var/log/dpkg.log /mnt/gluster-gv0/copy-test-$i; done
```

- Verificando se foram criados (essa pasta deve ser igual em todos servidores a partir de agora):
```
    ls -lha /mnt/gluster-gv0
```

#### Removendo volumes
- Para remover um volume, é necessário diminuir o número de réplicas do mesmo, afim de que não
seja replicado em outros servidores. 
- O exemplo abaixo demonst  ra a exclusão do volume `gv0` que está no servidor `server1.librecode.coop` que
  está sincronizando a pasta `/mnt/gluster-gv0`.
```bash
    gluster volume remove-brick gv0 replica 1 server1.librecode.coop:/mnt/gluster-gv0 force
    gluster volume delete gv0
 ```



#### Montando volumes automaticamente
- Adicione ao /etc/fstab seguindo o padrão:
> `HOSTNAME-OU-ENDEREÇOIP:/NOME-DO-VOLUME PONTO-DE-MONTAGEM glusterfs defaults,_netdev 0 0`

```
    server1.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
    server2.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
    server3.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
```

#### Monitorando carga de trabalho
- O GlusterFS Top é um comando que permite ver a performânce dos blocos que estão sendo sincronizados.
- É necessário habilitar a coleta de estatísticas no volume desejado.
    ```bash
    gluster volume profile $NOME-DO-VOLUME start 
    ```
- Vendo as estatísticas (informações de entrada e saída) do volume:
    ```bash
    gluster volume profile $NOME-DO-VOLUME info
    ```
- Quando não precisar mais das estatísticas, pode desabilitar:
    ```bash
    gluster volume profile $NOME-DO-VOLUME stop
    ```

**GlusterFS Top**
- É possível ver a quantidade de descritores de arquivos (fd) abertos e a contagem máxima:

    ```bash
    gluster volume top $NOME-DO-VOLUME open brick $NOME-DO-BRICK list-cnt 10
    ```

- Para visualizar as maiores chamadas de leituras de arquivos (qual arquivo está sendo mais acessado). Se o nome do brick não for especificado, uma lista de 100 arquivos será exibida por padrão (removendo a opção `brick $NOME-DO-BRICK`):
    ```bash
    gluster volume top $NOME-DO-VOLUME read brick $NOME-DO-BRICK list-cnt 10
    ```
- Outras opções disponíveis são:
    - write: arquivos com maior escrita
    - opendir: diretórios mais acessados
    - readdir: diretórios mais lidos

- Visualizando o desempenho de leitura:
- Com este comando é possível ver métricas de leitura de arquivos em cada brick.
    ```bash
    gluster volume top $NOME-DO-VOLUME read-perf bs 256 count 1 list-cnt 10
    ```

- Visualizando o desempenho de escrita:
- Este comando iniciará uma adição para a contagem e tamanho de bloco especificados e medirá a taxa de transferência correspondente.
    ```bash
    gluster volume top $NOME-DO-VOLUME write-perf bs 256 count 1 list-cnt 10
    ```

### Ansible role
- No diretório `roles` é possível encontrar um `role` para utilizar no Ansible.
- 1) Inclua o `role` a sua playbook:
```
---
- hosts: glusterfs_servers
  become: yes
  roles:
    - glusterfs
```

- 2) Adicione ao seu `inventory.ini` o endereço dos servidores:
```
[glusterfs_servers]
server1.exemplo.coop
server2.exemplo.coop
server3.exemplo.coop
```
3) Execute a playbook
```
    ansible-playbook -i inventory playbook.yml
```

