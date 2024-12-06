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

### Configuração do cluster.
- Pré-requisitos:
- Acesso com privilégios de `root` ou `sudo` aos servidores. 
- Acesso SSH aos servidores. A autenticação pode ser com chaves ou usuário e senha.

