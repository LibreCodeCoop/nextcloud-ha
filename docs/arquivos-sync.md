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

- Idealmente o diretório contendo os arquivos que serão sincronizados devem ficar em outro disco, separado do sistema operacional.

    apt update
    apt install glusterfs-server
    systemctl start glusterd
    systemctl enable glusterd

- No servidor 1:
    gluster peer probe servidor2
    gluster peer probe servidor3


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
- No servidor 2:
    gluster peer probe servidor1
    gluster peer probe servidor3

- Em todos servidores, crie um volume a ser compartilhado:
    `mkdir -p /data/brick1/gv0`

- 
```
    gluster volume create gv0 replica 3 server1.librecode.coop:/data/brick1/gv0 server2.librecode.coop:/data/brick1/gv0 server3.librecode.coop:/data/brick1/gv0 force
```
- Inicialize o volume
```
    gluster volume start gv0
```

- Agora vamos precisar montar esse volume no servidor, seguindo essa sintaxe `mount.glusterfs <IP ou hostname>:<nome_do_volume> <ponto_de_montagem>`
- O IP ou hostname pode ser de qualquer servidor que esteja presente no cluster.

- No servidor1: 
```
    mkdir /mnt/gluster-test
    mount.glusterfs server1.librecode.coop:/gv0 /mnt/gluster-test
```
- Vamos testar, criando arquivos no volume:
```
    for i in `seq -w 1 100`; do cp -rp /var/log/dpkg.log /mnt/gluster-test/copy-test-$i; done
```

- Verificando se foram criados (essa pasta deve ser igual em todos servidores a partir de agora):
```
    ls -lha /mnt/gluster-teste
```

#### Montando volumes automacamente
- Adicione ao /etc/fstab `HOSTNAME-OU-ENDEREÇOIP:/NOME-DO-VOLUME PONTO-DE-MONTAGEM glusterfs defaults,_netdev 0 0`:

```
    server1.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
    server2.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
    server3.librecode.coop:/data/brick1/gv0 /mnt/gluster-test/ glusterfs defaults,_netdev 0 0
```

#### Ansible role
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

```
```
```
```
```
