# Autobase
- Autobase é uma ferramenta com interface gráfica para criar e gerenciar clusters de PostgreSQL.

## Requerimentos
### Console (Interface Gráfica)
- Fazendo a instalação para utilizar o console gráfico, os requisitos são:
- Docker
- Acesso às portas 80 (aplicação web) e 8080 (API)

### Linha de comando
- Fazendo a instalação a partir da linha de comando
- Privilégios de `root`
- Ou acesso ao `sudo`
- Ansible, para executar a `playbook`de instalação

### Portas
- Lista de portas TCP necessárias que devem estar abertas para o cluster de banco de dados:

5432 (postgresql)
6432 (pgbouncer)
8008 (patroni rest api)
2379, 2380 (etcd)

- para o esquema "PostgreSQL Alta-Disponibilidade com Balanceamento de Carga":

5000 (haproxy - (leitura/gravação) master)
5001 (haproxy - (somente leitura) todas as réplicas)
5002 (haproxy - (somente leitura) somente réplica síncrona)
5003 (haproxy - (somente leitura) somente réplicas assíncronas)
7000 (opcional, haproxy stats)

- para o esquema "PostgreSQL Alta-Disponibilidade com Consul Service Discovery":

8300 (Consul Server RPC)
8301 (Consul Serf LAN)
8302 (Consul Serf WAN)
8500 (API HTTP do Consul)
8600 (Servidor DNS do Consul)

### Sistema Operacional
- Antes de instalar o cluster, verifique que você está rodando uma versão atualizada do seu sistema operacional. Manutenção apropriada é essencial para segurança e performance.
- Verifique se a configuração dos serviços NTP (para sincronização da hora correta) estão configurados corretamente. Mais informações podem ser obtidas no site do [ntp.br](https://ntp.br/).

### Serviço de Consenso Distribuído
- O desempenho e a estabilidade do seu cluster etcd ou consul são altamente dependentes de drives rápidos e uma rede confiável. Para otimizar esses fatores:

- Evite armazenar dados etcd ou consul no mesmo disco que outros processos que exigem muitos recursos, como o banco de dados. Certifique-se de que os dados etcd/consul e PostgreSQL sejam armazenados em discos separados (variáveis ​​etcd_data_dir, consul_data_path) e use SSDs, se possível.
- É recomendável implantar seu cluster DCS em servidores dedicados, separados dos servidores de banco de dados, para minimizar a contenção de recursos. 
- Para mais otimização, consulte as [recomendações de hardware](https://etcd.io/docs/v3.5/op-guide/hardware/) e os [guias de ajuste](https://etcd.io/docs/v3.5/tuning/).

### Disposição dos membros do cluster em diferentes data centers

### Previnindo perda de dados durante falhas (modo síncrono)
- A replicação síncrona é desabilitada por padrão por questões de performance. Entretanto, para minimizar o risco de perda de dados durante a recuperação automática em caso de falhas, é possível habilitar a replicação síncrona modificando as seguintes variáveis:
```bash
    synchronous_mode: true
    synchronous_mode_strict: true
    synchronous_commit: 'on' (ou remote_apply)
```
- Fazendo essa configuração irá garantir que todas transações empenhadas serão reconhecidas por pelo menos uma réplica, reduzindo o risco de perda de dados.

## Instalação
- É possível fazer a instalação nos seguintes provedores de nuvem: AWS, GCP, Azure, DigitalOcean e Hetzner Cloud (todos os componentes são instalados em sua conta de nuvem). 
- Ou em seus servidor existentes, esteja em qualquer outra nuvem ou no seu próprio data center.
- Para fins de utilizar infraestrutura em solo nacional, vamos fazer a instalação customizada.

### Instalação do Autobase
- Na pasta docker existe o arquivo autobase-compose.yml.
- Altere as variáveis `PG_CONSOLE_API_URL` para o seu domínio e `PG_CONSOLE_AUTHORIZATION_TOKEN` para o token de acesso ao serviço.
- Para gerar um token no terminal, podes utilizar o comando `openssl rand -hex 30`, o qual irá gerar um número hexadecimal de 30 caracteres pseudo-aleatório.
- Abaixo as variáveis que devem ser alteradas:
```bash
      - PG_CONSOLE_API_URL=http://localhost:8080/api/v1
      - PG_CONSOLE_AUTHORIZATION_TOKEN=secret_token
```
- Para fins de **testes** nas máquinas virtuais criadas com o Vagrant, execute o comando na sua máquina local ou escolha uma das máquinas virtuais.
- Inicialize as máquinas virtuais.
```bash
    vagrant up
```

### Configuração do cluster: requisitos
- Pré-requisitos:
- Privilégios de `root` ou `sudo` aos servidores.
- Acesso SSH aos servidores. A autenticação pode ser com chave pública ou usuário e senha.

### Cluster: Configuração pela Interface Gráfica

- Faça login inserindo o `token` definido em `PG_CONSOLE_AUTHORIZATION_TOKEN`.

![alt text](/assets/autobase.png)

- O próximo passo é criar o cluster. Clique em `Create Cluster`.

![alt text](/assets/autobase-1.png)

- Insira o nome, endereço IP e localização de cada servidor. Por exemplo:

![alt text](/assets/autobase-2.png)

- Método de acesso aos servidores: utilizando chaves (a chave pública já deve ter sido colocada no servidor) ou utilizando usuário e senha.

![alt text](/assets/autobase-4.png)

- Selecionando a opção "Save to console" é possível definir um nome e salvar as credenciais para uso posterior.

- As próximas variáveis são as seguintes:

Cluster VIP address - Se utilizar o `keepalived` deve definir o IP "flutuante" aqui. Nota: esse endereço não deve ser utilizado por nenhum host.
​Load balancers - HAProxy load balancer - Se deve ser instalado um proxy para balancear as requisições entre os hosts que formam o cluster
Environment - Ambiente: produção, desenvolvimento, desempenho
Cluster name* - Nome do cluster (obrigatório)
Description - Descrição do cluster
Postgres version -> Versão do postgres

![alt text](/assets/autobase-5.png)

- Se estiver tudo Ok, o cluster será criado:

![alt text](/assets/autobase-6.png)

- Clicando em `Operations` e `Show logs` é possível ver as tarefas que estão sendo executadas.

![alt text](/assets/autobase-7.png)


- Se os endereços dos hosts não estiverem listados, muito provavelmente ocorreu algum erro.

![alt text](/assets/autobase-8.png)




#### Cluster: Configuração pela Linha de comando
- Faça o clone do projeto:
```bash
    git clone https://github.com/vitabaks/autobase.git
```
- 1) Vamos precisar alterar o arquivo de inventário localizado dentro da pasta `automation` e inserir as variáveis necessárias para acessar os servidores.
```bash
    [cluster-pg]
    192.168.56.101 ansible_user=usuario      ansible_ssh_private_key_file=/caminho/para/a/chave/ssh
    192.168.56.102 ansible_user=usuario      ansible_ssh_private_key_file=/caminho/para/a/chave/ssh
    192.168.56.103 ansible_user=usuario      ansible_ssh_private_key_file=/caminho/para/a/chave/ssh
```
- 2) Editar as variáveis no arquivo `vars/main.yml`.
- Conjunto mínimo de variáveis que devem ser configuradas:
```bash
    proxy_env para baixar pacotes em ambientes sem acesso direto à internet (opcional)
    patroni_cluster_name
    postgresql_version
    postgresql_data_dir
    cluster_vip para fornecer um único ponto de entrada para acesso do cliente aos bancos de dados no cluster (opcional)
    with_haproxy_load_balancing para habilitar o balanceamento de carga (opcional)
    dcs_type "etcd" (padrão) ou "consul"
```


