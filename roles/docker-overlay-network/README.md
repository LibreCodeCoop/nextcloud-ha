Playbook para habilitar o docker swarm e utilizar uma rede overlay no docker para conectar os containers


docker swarm init --advertise-addr=eth1 ou IP
Para ingressar workers: 
docker swarm join --token SWMTKN-1-4zfgonhfkgbwgip9idkiamwkr06sih5szmn2xriv6wzzoy4nus-8t73o7ymg4446ey53ax8hc7rl 192.168.56.101:2377

E se os 3 nós forem managers?
docker swarm join-token manager

