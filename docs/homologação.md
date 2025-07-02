# Procedimentos para homologação de testes de catástrofes
- Este documento tem por objetivo elencar quais cenários o ambiente foi testado e quanto tempo cada etapa consumiu de tempo.

Legenda:
- S1 = servidor 1
- S2 = servidor 2

## Cenário 1)
- Considerando um ambiente sem a utilização de certificados wildcard.
- Projetos replicados: nginx-proxy, nextcloud-docker, postgres
- Dados replicados: nextcloud, postgres
- Serviços ativos no servidor 1: todos
- Serviços ativos no servidor 2: todos menos o nginx-proxy

Procedimento para validação:

    1. Desligar S1
    2. Atualizar no DNS a entrada tipo A utilizando o IP do S2
    3. No S2, promover postgres a principal: 
        1. pg_ctl promote ou pg_promote
            1. docker compose exec -upostgres postgres-replica pg_ctl promote
    4. No S2, inicializar projeto nginx-proxy
        1. cd nginx-proxy && docker compose up -d
    5. Testar acesso via web (nextcloud já deve estar em execução)


