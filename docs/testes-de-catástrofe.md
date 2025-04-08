# Procedimentos para homologação de testes de catástrofes

- Este documento tem por objetivo elencar quais cenários o ambiente foi testado e quanto tempo cada etapa consumiu de tempo.

Legenda:
- S1 = servidor 1
- S2 = servidor 2

Cenário 1)
- Considerando um ambiente sem a utilização de certificados wildcard.
- Projetos replicados: nginx-proxy, nextcloud-docker, postgres
- Dados replicados: nextcloud, postgres
- Serviços ativos no S1: todos
- Serviços ativos no S2: todos menos o nginx-proxy

Procedimento para evaluação:
    1. Desligar S1
    2. Atualizar no DNS a entrada tipo A utilizando o IP do S2
    3. No S2, inicializar projeto nginx-proxy

Procedimento para retorno ao S1:
    1. Verificar integridade dos serviços e dados em S1
    2. Colocar em manutenção aplicação em S2
    3. Atualizar no DNS a entrada tipo A utilizando o IP do S1
    4. Inicializar projeto nginx-proxy em S1


Cenário 2)
- Considerando ambiente com a utilização de certificados wildcard.
- Projetos replicados: nginx-proxy, nextcloud-docker, postgres
- Dados replicados: nginx-proxy,nextcloud, postgres
- Serviços ativos no S1: todos
- Serviços ativos no S2: todos

