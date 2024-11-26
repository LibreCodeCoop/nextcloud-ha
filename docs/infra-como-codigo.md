# Infraestrutura como código

## Instalação do ansible e módulos necessários
- Consulte [aqui](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html#installing-distros) como instalar o Ansible na sua distribuição.
- Utilizararemos a colletion do docker community, que pode ser instalada com esse comando: `ansible-galaxy collection install community.docker`
- Para verificar a versão do Ansible, no terminal, digite: `ansible --version`

## Dados sensíveis e de configuração não versionados
[Issue#27](https://github.com/LibreCodeCoop/gestao-infraestrutura/issues/27)

## Estrutura de pastas
### Pasta principal

```bash
ansible/
├── ansible.cfg
├── inventory.ini
├── playbook.yml
├── roles/
```

- Onde:
O arquivo `ansible.cfg` contém as configurações do ansible, como por exemplo:
```bash
# https://github.com/ansible/ansible/blob/stable-2.9/examples/ansible.cfg
[defaults]
# O interpretador default
interpreter_python = /usr/bin/python3

# Qual arquivo de inventório utilizar
inventory        = inventory.ini

# Usuário a ser utilizado para se conectar
#remote_user      = vagrant

# Chave privada utilizada para se conectar
private_key_file = /home/user/.ssh/id_rsa

# Argumentos da conexão SSH
#[ssh_connection]
#ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

Exemplo de arquivo de `inventory.ini`:
```bash
[srv-DC1]
192.168.1.10
192.168.1.40
10.17.1.55
200.200.10.143

[srvDC2]
192.168.56.101
192.168.56.102
```

Exemplo de arquivo de `playbook.yml`:
```bash
- name: "Instala pacotes base XYZ nos hosts do srv-DC1"
  hosts: srv-DC1
  become: true
  gather_facts: true
  strategy: free
  roles:
    - role: docker
    - role: role2
    - role: role3

```


- Para cada tarefa a ser realizada será criado um `role` com a seguinte estrutura de pastas, dentro da pasta `roles`:
```bash
nome-do-role/
├── defaults/
│   └── main.yml
├── vars/
│   └── main.yml
├── tasks/
│   └── main.yml
├── handlers/
│   └── main.yml
├── templates/
│   └── arquivo.conf.j2
├── files/
│   └── arquivos_estaticos
├── meta/
│   └── main.yml
└── README.md
```
- Onde:
```bash
tasks/: Tarefas principais da role
handlers/: Handlers para reiniciar serviços
templates/: Arquivos de configuração com Jinja2
files/: Arquivos estáticos
vars/: Variáveis específicas da role
defaults/: Variáveis com baixa precedência
meta/: Metadados e dependências
```

- No arquivo README.md deverá conter informações de como utilizar o `role`.


## Configuração
1. Criar uma chave SSH:
```bash
# Se não especificado o caminho, será criado na pasta /home/usuário/.ssh/
ssh-keygen -t ed25519
```
2. Copiar a chave pública para o servidor remoto:
```bash
ssh-copy-id usuario@ip-do-servidor
```
3. Testar o acesso
```bash
# Não deve pedir senha para acessar o servidor
# Faça isso manualmente para adicionar o servidor ao arquivo known_hosts
ssh usuario@ip-do-servidor
```
4. Utilizando comandos ad-hoc (Sintáxe: ansible [quais computadores] -m [o que fazer] -a "[como fazer]")
- Verificando o acesso às máquinas
```bash
ansible nome-do-grupo-do-inventário -m ping
ansible srv-DC1 -m ping
ansible 192.168.100.10 -m ping 
```

4.1 Atualizando o sistema operacional
```bash
ansible srv-DC1 -m apt -a "upgrade=dist update_cache=yes"
```
4.2 Copiando um arquivo
```bash
ansible src-DC1 -m ansible.builtin.copy -a "src=/caminho/do/arquivo/a/ser/copiado dest=/destino/no/servidor"
```
4.3 Excluindo um arquivo/diretório
```bash
ansible srv-DC1 -m ansible.builtin.file -a "dest=/caminho/para/o/arquivo state=absent"
```
5. Executando a playbook
```bash
ansible-playbook -i inventory.ini playbook.yml
```


# FAQ
1. Qual solução utilizar como Registry?
- Docker Registry.
2. Utilizaremos imagens oficiais Docker?
- Sim, e quando necessário, personalizar as mesmas.
3. O que utilizaremos para versionar a criação das imagens?
- Algum repositório no Registry do Docker
4. Qual ferramentas utilizaremos descobrir novas versões de imagens?
- https://github.com/getwud/wud (a ser testado)
5. Qual ferramenta pode ser utilizada para melhorar a segurança das imagens?
- [Docker Scout](https://docs.docker.com/scout/) (a ser testado)

