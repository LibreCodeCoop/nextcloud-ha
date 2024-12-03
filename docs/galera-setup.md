# Configuração do cluster MariaDB com Galera


- Após criar o cluster, copie a chave pública para os outros nós.

![alt text](/assets/galera-ssh-keys.png)

- Pode utilizar o playbook `ssh-key-setup.yml`. 
- Crie um arquivo chamado galera-key.pub com a chave pública.
- Execute o playbook: `ansible-playbook ssh-key-setup.yml`
>nota: para utilizar módulos posix, a versão do ansible deve ser maior que 2.14

- Clique na caixa "I have added public key to /root/.ssh/authorized_keys file on all nodes" e "Add Nodes"
- O próximo passo é adicionar os nós que farão parte do cluster
- Clique nos três pontinhos e depois em "Add node":
![alt text](/assets/galera-add-node.png)

- Insira:
> nome do nó
> sistema operacional
> segmento (deixe o valor padrão)
> o endereço de acesso SSH (pode ser o domínio, também)
> a porta do SSH (22 é o padrão, mas pode ser diferente, consulte seu servidor)
![alt text](/assets/galera-add-node-2.png)
- Clique em "Check Access" para verificar a conexão com o servidor.
- Se estiver correto, clique em "close" e depois "Deploy" para realizar a configuração do novo servidor.
![alt text](/assets/galera-check-ssh.png)
- Se tudo ocorrer como esperado na configuração do nó, aparecerá a seguinte tela:
![alt text](/assets/galera-add-node-sucess.png)

- Basta seguir o mesmo processo para a quantidade desejada de nós a serem adicionados. É possível remover, posteriormente.