# Verificação de segurança
- Como saber se o sistema foi comprometido?
- É possível utilizar muito utilitários de linha de comando para fazer uma análise.

## Usuários logados
- O comando `w` ou `who`, mostra quem está logado **atualmente**.
- Já o comando `last`, informa o histórico de quem acesou o servidor.
 

## Histórico de comandos
- No arquivo `.bash_history` ficam registrados os comandos executados.
- Podemos verificar os últimos 100 utilizando o comando abaixo:  
    ```bash
    tail -n 100 ~/.bash_history | more
    ```

## Arquivos que foram modificados recentemente
- Pode-se verificar quais arquivos foram modificados recentemente.
- O comando a baixo mostra quais arquivos foram modificados nos últimos `5` dias.
    ```bash
    sudo find /home /etc /var -mtime -5
    ```


# Verificação de performance
- Antes de fazer a instalação dos serviços no servidor, uma boa prática é conferir se o ambiente entregue está pronto para produção.
- Muitas vezes confiamos no fornecedor cegamente.

- O que podemos testar:
[ ] Velocidade de download/upload
[ ] Velocidade de escrita em disco - IO
[ ] Teste de stress de CPU
[ ] Reputação do IP público


- Velocidade de Download/Upload
    ```bash
    # Utilizando o repositório oficial
    sudo apt-get install curl -y
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
    sudo apt-get install speedtest -y

    # Com docker - utilizando image de terceiros
    docker run --rm wesbragagt/alpine-speedtest
    ```


