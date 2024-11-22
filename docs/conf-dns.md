# Configurações no DNS
- Essas são as instruções de como configurar o seu registro no DNS apropriadamente
- Você deve possuir um registro. Senão o tiver, [registre o seu!](https://registro.br/)

## Entradas a serem inseridas
A quantidade de entradas configuradas irá depender de quantos servidores vamos utilizar.
- Caso tenhamos 3 servidores, vamos configurar 3 entradas do tipo A, cada qual apontando ao IP público de cada servidor:
Por exemplo:
![image](https://github.com/user-attachments/assets/0e6665dc-0d9a-4a18-8f7a-18d5b24531d6)


## Como validar se a configuração está funcionando
- Utilize o comando a seguir para verificar se:
- 1) o IP-DO-SERVIDOR- está resolvendo o endereço seudominio.com.br
  2) possui certificados válidos
  ```bash
  # Para o servidor 1
  curl https://seudominio.com.br --resolve 'seudominio.com.br:443:IP-DO-SERVIDOR-1'
  # Para o servidor 2
  curl https://seudominio.com.br --resolve 'seudominio.com.br:443:IP-DO-SERVIDOR-2'
  # Para o servidor 3
  curl https://seudominio.com.br --resolve 'seudominio.com.br:443:IP-DO-SERVIDOR-3'
  ```

## Configurar registros para seus servidores
- Adicione um subdomínio para facilitar o acesso ao seu servidor.
- Dessa maneira, o acesso ssh poderia ser feito utilizando o nome do servidor:
  ```bash
  ssh usuario@servidor01.seudominio.com.br
  ```

![image](https://github.com/user-attachments/assets/fa522441-5b14-431d-a5c5-397dabb01e20)
