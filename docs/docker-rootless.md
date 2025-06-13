# Docker Rootless: Guia de Configuração

## Introdução

Este documento detalha o processo de configuração do Docker em modo *rootless*, permitindo que o daemon do Docker seja executado como um usuário não-root. 

Essa abordagem aumenta a segurança do sistema, isolando o daemon do Docker de privilégios de superusuário e mitigando potenciais vulnerabilidades. 

O Docker Rootless é uma funcionalidade que permite a execução do daemon e dos contêineres sem a necessidade de privilégios de root no host, utilizando *namespaces* de usuário para isolar os processos.

## Pré-requisitos

Antes de iniciar a configuração, certifique-se de que seu sistema atenda aos pré-requisitos abaixo:

*   **Sistema Operacional:** Distribuição Linux baseada em Debian (como Ubuntu) ou RPM (como Fedora, CentOS) com `systemd`.
*   **Acesso à Internet:** Para download de pacotes e dependências.
*   **Conhecimento Básico:** Familiaridade com o terminal Linux e comandos básicos.

## 1. Criação de um usuário regular

Para operar o Docker em modo *rootless*, é fundamental utilizar um usuário sem privilégios de root. 

Se você já possui um usuário regular que deseja utilizar, pode pular esta etapa. 

Caso contrário, crie um novo usuário:

```bash
useradd -m -d /home/semroot -s $(which bash) semroot
```

**Explicação:**
*   `useradd`: Comando para adicionar um novo usuário.
*   `-m`: Cria o diretório *home* do usuário se ele não existir.
*   `-d /home/semroot`: Define `/home/semroot` como o diretório *home* do usuário.
*   `-s $(which bash)`: Define `bash` como o *shell* padrão do usuário.
*   `semroot`: Nome do novo usuário.

## 2. Instalação das dependências

As seguintes dependências são necessárias para o funcionamento adequado do Docker Rootless. 

```bash
# Para sistemas baseados em Debian/Ubuntu
apt-get install uidmap dbus-user-session systemd-container docker-ce-rootless-extras
```

**Explicação das dependências:**
*   `uidmap`: Fornece os utilitários `newuidmap` e `newgidmap`, essenciais para o mapeamento de IDs de usuário e grupo em *namespaces* de usuário.
*   `dbus-user-session`: Habilita o *daemon* D-Bus por usuário, necessário para a comunicação entre processos de usuário.
*   `systemd-container`: Contém utilitários para gerenciar contêineres e *namespaces* de usuário com `systemd`.
*   `docker-ce-rootless-extras`: Pacote que inclui ferramentas e componentes adicionais específicos para o modo *rootless* do Docker.

## 3. Verificação da versão do `slirp4netns`

O Docker Rootless requer uma versão específica do `slirp4netns` para o correto funcionamento da rede, especialmente quando o `vpnkit` não está instalado. Certifique-se de que a versão instalada é superior à `v0.4.0`:

```bash
slirp4netns --version
```

## 4. Desabilitando o daemon docker do sistema

Se você já possui uma instalação tradicional do Docker (daemon em todo o sistema) em execução, é recomendável desabilitá-la para evitar conflitos com a configuração *rootless*:

```bash
sudo systemctl disable --now docker.service docker.socket
sudo rm /var/run/docker.sock
```

**Cuidado:** Esta etapa irá parar e desabilitar o daemon Docker. Certifique-se de que não há outras aplicações dependendo dele antes de prosseguir.

## 5. Instalação do docker rootless

Para Docker versão 20.10 ou posterior, o script `dockerd-rootless-setuptool.sh` é fornecido para facilitar a configuração. 

Execute-o como o usuário não-root que você criou anteriormente ou deseja utilizar para o Docker Rootless:

```bash
dockerd-rootless-setuptool.sh install
```

**Observação:** Este comando configura o ambiente do usuário para executar o daemon Docker em modo *rootless*, incluindo a criação de arquivos de serviço `systemd` específicos do usuário.

## 6. Login para usuários sem login

Se o usuário configurado para o Docker Rootless **não for um usuário com login interativo** (por exemplo, um usuário de serviço), você pode precisar usar `machinectl` para logar-se e permitir que o `systemd --user` inicie o daemon:

```bash
machinectl shell semroot@
```

**Explicação:** `machinectl` é uma ferramenta para controlar máquinas virtuais e contêiners, e pode ser usada para gerenciar sessões de usuário `systemd`.

## 7. Habilitando e iniciando o daemon docker rootless

Após a instalação, habilite e inicie o daemon Docker Rootless usando os comandos `systemctl` específicos do usuário:

```bash
systemctl --user enable docker
sudo loginctl enable-linger $(whoami)
```

**Explicação:**
*   `systemctl --user enable docker`: Habilita o serviço `docker.service` para o usuário atual, garantindo que ele inicie automaticamente após o login do usuário.
*   `sudo loginctl enable-linger $(whoami)`: Permite que os processos do usuário continuem em execução mesmo após o logout. Isso é crucial para que o daemon Docker Rootless permaneça ativo em segundo plano.

Para iniciar o daemon imediatamente:

```bash
sudo systemctl start docker.service
```

## 8. Expondo Portas Privilegiadas (Opcional)

Por padrão, usuários não-root não podem vincular a portas menores que 1024 (portas privilegiadas). 

Para permitir que o Docker Rootless exponha contêineres em portas privilegiadas, use o comando `setcap`:

```bash
sudo setcap cap_net_bind_service=ep $(which rootlesskit)
systemctl --user restart docker
```

**Cuidado:** A utilização de `setcap` concede permissões elevadas ao executável `rootlesskit`. Avalie os riscos de segurança antes de aplicar esta configuração.

## 9. Configuração da Variável de Ambiente `DOCKER_HOST`

Para que o cliente Docker (CLI) se comunique corretamente com o daemon Docker Rootless, é necessário definir a variável de ambiente `DOCKER_HOST`. 

Adicione a seguinte linha ao seu arquivo `~/.bashrc` (ou arquivo de configuração de *shell* equivalente).


```bash
export DOCKER_HOST=unix:///run/user/1000/docker.sock
```

**Observação:** O `1000` no caminho `unix:///run/user/1000/docker.sock` refere-se ao UID do seu usuário. Você pode verificar seu UID com o comando `id -u`.

Após adicionar a linha, recarregue o arquivo de configuração do *shell* para que a alteração tenha efeito:

```bash
source ~/.bashrc
```

## 10. Limitação de recursos (cgroups v2)

A limitação de recursos (CPU, memória, etc.) para contêineres no Docker Rootless é totalmente suportada apenas com `cgroups v2`. Para verificar qual versão do `cgroup` seu sistema está utilizando, execute:

```bash
docker info | grep "Cgroup Driver"
```

Se a saída indicar `Cgroup Driver: systemd`, isso significa que o `cgroups v1` está em uso, e a limitação de recursos pode não funcionar como esperado para todos os tipos de recursos.

Para habilitar a delegação de `cgroups` para o `systemd --user` e permitir a limitação de recursos com `cgroups v2`, adicione as seguintes configurações ao systemd:

```bash
sudo mkdir -p /etc/systemd/system/user@.service.d
sudo cat > /etc/systemd/system/user@.service.d/delegate.conf << EOF
[Service]
Delegate=cpu cpuset io memory pids
EOF
sudo systemctl daemon-reload
```

**Explicação:**
*   Este trecho de código cria um arquivo de configuração para o serviço `user@.service` do `systemd`, que é responsável por gerenciar a sessão de usuário. A diretiva `Delegate` permite que o `systemd --user` gerencie os `cgroups` para os recursos especificados (cpu, cpuset, io, memory, pids), o que é essencial para a limitação de recursos em `cgroups v2`.
*   `sudo systemctl daemon-reload`: Recarrega as configurações do `systemd` para que as alterações no arquivo `delegate.conf` sejam aplicadas.

## Conclusão

Ao seguir este guia, você terá configurado com sucesso o Docker em modo *rootless*, proporcionando um ambiente mais seguro e isolado para o desenvolvimento e execução de contêineres. 

Se não for possível seguir o tutorial acima, considere acessar o daemon do Docker à partir de um usuário não-root. Instruções de como fazer [aqui.](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)

## Referências
- https://docs.docker.com/engine/security/rootless/#rootless-docker-in-docker

