# Interconexão entre instâncias
- A comunicação entre os servidores pode ser feita utilizando ferramentas como o `Secure Shell`, ou `WireGuard`, entreanto,
são mais comumente utilizadas para acessar os servidores onde estão as aplicações ou conectar diferentes localidades.
- Neste projeto será utilizado o gerenciador de containers `Docker`, o qual oferece a opção de interconectar os servidores utilizando
as redes [`overlay`](https://docs.docker.com/engine/network/drivers/overlay/).
- Sendo nativo ao Docker, será a opção utilizada.
- Abaixo outras alternativas que acrescentam uma camada extra de segurança.

## Outras opções disponíveis
- SSH
- Wireguard
- Tailscale
- Zerotier
- Nebula
- DefGuard
- Strongswan


### SSH
- Utilizando SSH e tuneis reversos, é possível fazer uma arquitetura que interconecte os servidores.
- Na maneira diagramada abaixo, tanto o servidor inicia uma conexão quanto recebe uma.

```mermaid
graph TD
    subgraph "Servidor A"
        A1[Servidor A]
    end
    
    subgraph "Servidor B"
        B1[Servidor B]
    end
    
    subgraph "Servidor C"
        C1[Servidor C]
    end

    A1 -->|"SSH Tunnel A → B"| B1
    B1 -->|"SSH Tunnel B → A"| A1
    
    B1 -->|"SSH Tunnel B → C"| C1
    C1 -->|"SSH Tunnel C → B"| B1
    
    C1 -->|"SSH Tunnel C → A"| A1
    A1 -->|"SSH Tunnel A → C"| C1

    classDef server fill:#f9f,stroke:#333,stroke-width:4px;
    classDef tunnel stroke:#333,stroke-dasharray:5 2;
    
    class A1,B1,C1 server;
```

### Wireguard
- É possível realizar a mesma arquiteturacom o Wireguard.
- Para automatizar a distribuição dos arquivos de configurações entre os hosts, utiliza-se esse [projeto](https://github.com/k4yt3x/wg-meshconf)

```mermaid
graph TD
    subgraph "Servidor A"
        A1[Servidor A]
        A1IP[IP Virtual: 10.0.0.1/24]
    end
    
    subgraph "Servidor B"
        B1[Servidor B]
        B1IP[IP Virtual: 10.0.0.2/24]
    end
    
    subgraph "Servidor C"
        C1[Servidor C]
        C1IP[IP Virtual: 10.0.0.3/24]
    end

    A1 -->|"WireGuard Tunnel A ↔ B"| B1
    B1 -->|"WireGuard Tunnel B ↔ C"| C1
    C1 -->|"WireGuard Tunnel C ↔ A"| A1

    classDef server fill:#e6f3ff,stroke:#0066cc,stroke-width:2px;
    classDef ip fill:#f0f0f0,stroke:#666,stroke-dasharray:5 2;
    
    class A1,B1,C1 server;
    class A1IP,B1IP,C1IP ip;

```

### Zerotier
- Zerotier é uma solução de rede definida por software e VPN. Segundo informações no site:
    ```bash
    ZeroTier é um switch Ethernet programável inteligente para o planeta Terra. 
    Ele permite que todos os dispositivos em rede, VMs, contêineres e aplicativos se comuniquem como se todos residissem no mesmo data center físico ou região de nuvem.
    ```
- O agente que é instalado nas máquinas é responsável por escolher o melhor caminho até o destino.
- Por exemplo, se duas máquinas na mesma rede estiverem na mesma rede do zerotier, elas serão acessíveis diretamente, sem trafegar pela internet.
- Para adicionar os nós na rede, é possível utilizar o controlador da fabricante ou [forks da mesma](https://github.com/sinamics/ztnet)


### Tailscale
- Oferece uma solução Web mais amigável para gerência dispositivos. Executa o protocolo Wireguard.

### Nebula

- Segundo a documentação: "Nebula é uma rede definida por software peer-to-peer mutuamente autenticada com base no Noise Protocol Framework. Nebula usa certificados para afirmar o endereço IP, nome e associação de um nó dentro de grupos definidos pelo usuário. Os grupos definidos pelo usuário do Nebula permitem filtragem de tráfego independente do provedor entre nós."
