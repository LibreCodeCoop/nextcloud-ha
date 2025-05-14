# Nextcloud tolerante a falhas

Este projeto se propõe a definir as melhores práticas para a configuração de uma infraestrutura resiliente a catástrofes, além de elaborar estratégias e diretrizes para que seja possível utilizar-se de diferentes modelos de datacenters nacionais de forma replicável por empresas brasileiras visando fortalecimento da economia nacional com soberania tecnológica.


## Sistemas implementados
- [Nextcloud](https://docs.nextcloud.com/)
- Replicação de dados (GlusterFS ou GarageS3)
- Proxy reverso
- Banco de dados - PostgreSQL
- Redis
- Onlyoffice
  

## Senhas necessárias a serem geradas
- A senha do painel admin do Traefik precisa ser codificada usando MD5, SHA1, or BCrypt.
- O comando abaixo irá encryptar uma senha com BCrypt e sanitizar os caracteres especiais para uso.
```
echo $(htpasswd -nB nome-do-usuário) | sed -e s/\\$/\\$\\$/g
```
