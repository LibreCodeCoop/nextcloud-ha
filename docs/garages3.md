# garages3
- garage é um servidor de armazenamento de objetos compatível com a API S3 que pode ser auto-hospedado, semelhante ao [minio](https://min.io/).
- Segundo a documentação:
  ```bash
  - O Garage é um armazenamento de dados geodistribuído leve que implementa o protocolo de armazenamento de objetos Amazon S3.
  - Ele permite que aplicativos armazenem grandes blobs, como fotos, vídeos, imagens, documentos, etc., em uma configuração redundante de vários nós.
  - O S3 é versátil o suficiente para também ser usado para publicar um site estático.
  ```

- O garage é projetado para prover resiliência aos dados utilizando hardware de segunda mão/não topo de linha.

## Requerimentos
  ```bash
    CPU: Qualquer CPU x86_64 dos últimos 10 anos, ARMv7 ou ARMv8
    RAM: 1 GB
    Espaço em disco: Pelo menos 16 GB
    Rede: 200 ms ou menos, 50 Mbps ou mais
    Hardware heterogêneo
    Monte um cluster com quaisquer máquinas de segunda mão disponíveis
  ```
## Instalação
- Veja no [repositório](https://github.com/LibreCodeCoop/garages3) para seguir a instalação.
- Se necessário adicionar algo, adicione um `Pull Request` ou abra uma `Issue`.

# Referências
- https://garagehq.deuxfleurs.fr/
- https://garagehq.deuxfleurs.fr/documentation/quick-start/
