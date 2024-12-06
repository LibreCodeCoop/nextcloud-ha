# Cluster Galera MariaDB


## Requisitos
- Antes de configurar um cluster, verifique se a sua aplicação atende aos seguintes requisitos:

- [ ] Garantir que todas as tabelas tenham uma chave primária
- [ ] Usar somente InnoDB como um mecanismo de armazenamento
- [ ] Certificar-se de que você não precisa de suporte a transações distribuídas (XA)
- [ ] Garantir que o aplicativo não use LOCK/UNLOCK TABLES
- [ ]Levar em consideração linhas ativas de alta simultaneidade, onde há constantes UPDATEs para a mesma linha; é aqui que se pode usar wsrep_retry_autocommit=n (n=1 ou 5 e assim por diante).
- [ ] Não escrever diretamente na tabela mysql.user; em vez disso, usar CREATE USER pois as instruções DDL ficam presas.


## Configuração do cluster com Galera Manager
- Após criar o cluster, copie a chave pública para os outros nós.

![alt text](/assets/galera-ssh-keys.png)

- Pode utilizar o playbook `ssh-key-setup.yml`. 
- Crie um arquivo chamado galera-key.pub com a chave pública.
- Execute o playbook: `ansible-playbook ssh-key-setup.yml`
>nota: para utilizar módulos posix, a versão do ansible deve ser maior que 2.14

- Clique na caixa "I have added public key to /root/.ssh/authorized_keys file on all nodes" e "Add Nodes"
- O próximo passo é adicionar os nós que farão parte do cluster
- Clique nos três pontinhos e depois em "Add node":

![alt text](/assets/galera-add-node.png)

- Insira:
> nome do nó
> sistema operacional
> segmento (deixe o valor padrão)
```
Explicação: é possível ter múltiplos clusters em múltiplos datacenters e ser visível numa única página de visualização do cluster.
A configuração de segmento permite definir a proximidade de cada máquina.
Por exemplo: 
- 3 nós em um datacenter (Segmento 0)
- 2 nós em outro datacenter (Segmento 1)
```
> o endereço de acesso SSH (pode ser o domínio, também)
> a porta do SSH (22 é o padrão, mas pode ser diferente, consulte seu servidor)

![alt text](/assets/galera-add-node-2.png)
- Clique em "Check Access" para verificar a conexão com o servidor.
- Se estiver correto, clique em "close" e depois "Deploy" para realizar a configuração do novo servidor.

![alt text](/assets/galera-check-ssh.png)
- Se tudo ocorrer como esperado na configuração do nó, aparecerá a seguinte tela:

![alt text](/assets/galera-add-node-sucess.png)

- Basta seguir o mesmo processo para a quantidade desejada de nós a serem adicionados. É possível remover, posteriormente.


## Recuperação em casos de desastres


### Todos os três nós são parados manualmente, sem erros
- O cluster está completamente parado e o problema é como inicializá-lo novamente. É importante que um nó grave sua última posição executada no arquivo `grastate.dat.`
Comparando o número seqno neste arquivo, você pode ver qual é o nó mais avançado (provavelmente o último parado). O cluster deve ser inicializado usando este nó, caso contrário, os nós que tinham uma posição mais avançada terão que executar o SST completo para se juntar ao cluster inicializado a partir do menos avançado. Como resultado, algumas transações serão perdidas.
- No nosso cenário com 3 nós e nó que devemos inicializar será a `primario` pois é o nó mais avançado (com os dados mais recentes). Podemos ver isso observando o valor ao lado do seu nome (68tx, no exemplo abaixo).

![alt text](/assets/galera-crash-1.png)

- É necessário acessar o console do nó primário e iniciar o cluster manualmente, com o comando `galera_new_cluster`.
- Vá em primario -> console:

![alt text](/assets/galera-crash-2.png)

- Depois de inicializado, basta inicializar os demais nós:

![alt text](/assets/galera-crash-3.png)

## Testando o cluster
- Quando estiver com o cluster em funcionamento, é uma boa prática testar se o seu funcionamento está correto.

### Testes de replicação
- Seguindo esses passos vamos verificar se o cluster está funcionando como esperado. No servidor primário, vamos verificar se todos os nós estão conectados entre si. Execute o comando `SHOW STATUS` como mostrado:


#### Arquivos de configuração
- As configurações feitas pelo Galera Manager Daemon (gmd) estão em `/etc/default/gmd`.
- Essas configurações são alteradas via scripts mas se alteradas o `daemon` deve ser recarregado utilizando o comando `systemctl restart gmd`.

#### Logs
- Os arquivos de logs estão localizados no diretório `/var/log/gmd`.
- Há um arquivo de log para o daemon gmd (ou seja, default.log), um para o cluster, um par para cada host e um para cada nó.
- Na tabela abaixo há a explicação do que contém em cada arquivo:

default.log - O arquivo de log principal para o daemon gmd, o arquivo default.log, contém informações relacionadas a iniciar e parar o daemon.
logs de cluster - Há um arquivo de log para cada cluster. Seu nome contém o nome do cluster anexado a ele (por exemplo, cluster-1.log). Este arquivo de log contém algumas informações muito básicas sobre as configurações do cluster.
logs de hosts - Para cada host dentro do cluster é gerado um arquivo de logs (por exemplo, cluster-1-host-1.log)
logs dos nós