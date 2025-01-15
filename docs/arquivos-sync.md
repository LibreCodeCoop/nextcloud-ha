# Sincronização de arquivos
- Uma ferramenta para sincronização dos arquivos deve ser adotada, de maneira a replicar os dados de um servidor para os demais participantes.
- Essa ferramenta deve: a) Detectar mudanças instantaneamente; b) Minimizar overhead de rede; c) Oferece ecanismos eficientes de transferência; d) Suportam delta-transfer (só enviam as partes modificadas); Entre outras.

- O que levar em conta ao escolher uma tecnologia de sincronização:
- Taxa de transferência
- IOPS
- Escalabilidade
- Resiliência
- Tempo de Recuperação e Plano de recuperação em desastres
- Estratégias de replicação
- Overhead
- Replicação Geográfica

## Ferramentas disponíveis
- Algumas ferramentas para sincronizar dados:

    - [GlusterFS](https://www.gluster.org/)
    - [RBD: https](https://linbit.com/drbd/)
    - [Unison](https://github.com/bcpierce00/unison)
    - [Lsyncd](https://lsyncd.github.io/lsyncd/)


- É possível configurar o Nextcloud para utilizar armazenamento em objeto como seu [primeiro armazenamento](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/primary_storage.html#configuring-object-storage-as-primary-storage
), dispensando o uso de uma pasta localmente.
- Também é possível configurar [múltiplos buckets](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/primary_storage.html#multibucket-object-store) a serem utilizado.

- A fazer: configurar duas ou mais instâncias para utilizar múltiplos buckets.
- Opções object storage:
    - [Seaweedfs](https://github.com/seaweedfs/seaweedfs?tab=readme-ov-file#introduction)
    - [Garage S3](https://garagehq.deuxfleurs.fr/)
    - [MooseFS](https://github.com/moosefs/moosefs)


- Abaixo, uma tabela comparativa produzida por [Grey Skipwith, 2023](https://aaltodoc.aalto.fi/server/api/core/bitstreams/4b0dd60c-cba2-4c01-9972-3dafd81708a4/content)

| | Ceph | GlusterFS | HDFS |
|---|---|---|---|
| Arquitetura | Distribuída | Descentralizada | Centralizada |
| Gerenciamento de Metadados | Múltiplos MDSs | Sem MDS | Um MDS |
| Método de Armazenamento Subjacente | Baseado em Objeto | Baseado em Arquivo | Baseado em Bloco |
| Modelo de Escalabilidade | Horizontal | Horizontal | Horizontal |
| Caso de Uso Principal | Armazenamento Unificado | Sistema de Arquivos | Armazenamento de Big Data |
| Interface de Armazenamento | Arquivo, Bloco, Objeto | Arquivo | Arquivo |



### Garage S3
- "Garage é um armazenamento de dados geodistribuído leve que implementa o protocolo de armazenamento de objetos Amazon S3. Ele permite que aplicativos armazenem grandes blobs, como fotos, vídeos, imagens, documentos, etc., em uma configuração redundante de vários nós. O S3 é versátil o suficiente para também ser usado para publicar um site estático"
- Características do GarageS3:
a) Habilitado para Internet: feito para vários sites (por exemplo, datacenters, escritórios, residências, etc.) interconectados por meio de conexões regulares de Internet.
b) Autocontido e leve: funciona em qualquer lugar e se integra bem em ambientes existentes para atingir infraestruturas hiperconvergentes.
c) Altamente resiliente: altamente resiliente a falhas de rede, latência de rede, falhas de disco, falhas de administrador de sistema.
d) Simples: simples de entender, simples de operar, simples de depurar.
e) Desempenhos extremos: altos desempenhos restringem muito o design e a infraestrutura; buscamos desempenhos apenas por meio do minimalismo.
f) Extensividade de recursos: não planejamos adicionar recursos adicionais em comparação aos fornecidos pela API S3.
g) Otimizações de armazenamento: codificação de apagamento ou qualquer outra técnica de codificação aumentam a dificuldade de colocar dados e sincronizar; nos limitamos à duplicação.
h) Compatibilidade POSIX/Sistema de arquivos: não pretendemos ser compatíveis com POSIX ou emular qualquer tipo de sistema de arquivos. De fato, em um ambiente distribuído, tais sincronizações são traduzidas em mensagens de rede que impõem restrições severas à implantação.

- Ponto negativo: não faz a checagem de integridade dos dados.

#### Configuração
1 - Copiar a

- Após fazer a instalação, configurar o cluster e adicionar uma chave de acesso ao bucket criado, configure os registros DNS.
- Por exemplo: 
- Entrada 1: 20.180.0.10 -> garage.dominio.com.br.
- Entrada 2: 20.180.0.30 -> garage.dominio.com.br.
- Entrada 3: 20.180.0.60 -> garage.dominio.com.br.