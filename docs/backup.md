# Backup 
- O backup será configurado utilizando utilizando Ansible. Não será necessário realizar backup do código fonte dos softwares, pois serão utilizados imagens Docker disponíveis no `hub` do Docker.


## Rotina de backup
- Por definição, uma rotina de backup é:
```
Rotinas de backup são processos sistemáticos e planejados de criação de cópias de segurança de dados e informações armazenadas em sistemas eletrônicos. 
```

- É possível definir uma rotina de backup global para o servidor ou uma rotina de backup específica para cada sistema.
- Para tornar mais célere o processo de recuperação de dados, é recomendado **uma rotina de backup para cada sistema**

- Usualmente os arquivos que são incluídos na rotina de backup são:
- 1) Diretórios com arquivos de usuários
- 2) Arquivos de `dump` de banco de dados
- 3) Arquivos de configuração

## Ferramentas disponíveis


| Ferramenta | Sistemas Operacionais | Tipo de Backup | Recursos Principais | Facilidade de Uso | Licença |
|------------|----------------------|----------------|---------------------|-------------------|---------|
| Duplicati | Windows, Linux, macOS | Incremental, Completo | Criptografia, Agendamento, Suporte a múltiplos destinos (Cloud, NAS) | Fácil (Interface Web) | LGPL |
| Bacula | Linux, Unix | Completo, Incremental, Diferencial | Backup para empresas, Gerenciamento centralizado, Múltiplos clientes | Moderada | AGPL |
| Clonezilla | Linux, Multiplataforma | Imagem de disco completa | Backup de sistema, Clonagem de disco, Suporte a múltiplos sistemas de arquivos | Intermediária | GPL |
| UrBackup | Windows, Linux | Incremental, Completo (Arquivo e Imagem) | Backup em rede, Interface web, Retenção de versões | Fácil | GPL |
| Amanda | Linux, Unix, Windows | Incremental, Completo | Backup corporativo, Múltiplos destinos, Escalabilidade | Complexa | BSD |
| BackupPC | Linux, Unix | Incremental | Baixo consumo de espaço, Deduplificação, Interface web | Moderada | GPL |



## Política de retenção de dados
- Definir uma política de retenção de dados é fundamental e varia conforme o projeto e espaço disponível para armazenamento dos backups.

- Possíveis configurações:
- 1) Manter todas versões: Nada será excluído.O backup crescerá a cada modificação.
- 2) Excluir backups mais antigos que: Se um novo backup for encontrado, todos os backups anteriores a esta data são excluídos.
- 3) Manter um número específico de backups: Se existir mais backups do que o número especificado, os backups mais antigos serão excluídos.
- 4) Retenção de backup personalizada: reter 1 backup de cada semana, 1 de cada mês e 1 de cada ano.    


## Configurar política de retenção na ferramenta de infra como código
- A política de retenção deverá ser configurada apropriadamente no software de backup.

### Duplicati
- A política de retenção pode ser configurada adicionando o seguinte parâmetro à execução do backup:
    ```bash
    --retention-policy=1W:1D,4W:1W,12M:1M
    ```
- No exemplo acima, a política de retenção é a seguinte: mantém um backup para cada um dos últimos 7 dias, cada uma das últimas 4 semanas e cada um dos últimos 12 meses.


- Onde o comando por completo seria:
> Descrição das variáveis:
> NOME-DO-BUCKET: nome do bucket criado no provedor de armazenamento

> URL-DO-PROVEDOR: URL do provedor de armazenamento utilizada

> LOCATION-DO-ARMAZENAMENTO: localização do bucket criado. Por exemplo: `eu-central-1`

>ACCESS-KEY:chave para acesso ao bucket

>SECRET-KEY: senha de acesso ao bucket

>PASTA-BACKUP: caminho da pasta a ser backupeada. Por exemplo: `/home/user/Documentos`

>NOME-DA-ROTINA: nome da rotina de backup

>NOME-DO-BANCO: nome do banco de dados do Duplicati da rotina de backup

>SENHA-DE-CRIPTOGRAFIA-DOS-ARQUIVOS: senha de encriptação dos arquivos. Só será possível a visualização e recuperação dos dados em posse dessa senha.  

- O comando ficaria assim:
    ```bash
    duplicati-cli backup "s3s://NOME-DO-BUCKET/?s3-server-name=URL-DO-PROVEDOR&s3-location-constraint=LOCATION-DO-ARMAZENAMENTO&s3-storage-class=&s3-client=aws&auth-username=ACCESS-KEY&auth-password=SECRET-KEY" "/PASTA-BACKUP" --backup-name=NOME-DA-ROTINA --dbpath=/data/Duplicati/NOME-DO-BANCO.sqlite --encryption-module=aes --compression-module=zip --dblock-size=50mb --passphrase=SENHA-DE-CRIPTOGRAFIA-DOS-ARQUIVOS --retention-policy=1W:1D,4W:1W,12M:1M --disable-module=console-password-input
    ```

- É preciso adicionar à`crontab` para que o backup seja executado no horário desejado.
- Exemplo de configuração da Cron (executa todos os dia às 1 horas da manhã):
    ```bash
    0 1 * * * duplicati-cli...
    ```