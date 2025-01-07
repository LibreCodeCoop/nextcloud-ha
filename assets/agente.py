import socket
import time
import json
import logging
import random
import threading
import requests
from datetime import datetime
from pathlib import Path
from enum import Enum

class NodeState(Enum):
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'
    LEADER = 'leader'

class RaftNode:
    def __init__(self, node_id, nodes_config, dns_provider=None, load_balancer=None):
        """
        Inicializa um nó Raft
        
        :param node_id: ID deste nó
        :param nodes_config: Dict com configuração de todos os nós
        :param dns_provider: Configuração do DNS (opcional)
        :param load_balancer: Configuração do load balancer (opcional)
        """
        self.node_id = node_id
        self.nodes = nodes_config
        self.dns_provider = dns_provider
        self.load_balancer = load_balancer
        
        # Estado Raft
        self.current_term = 0
        self.voted_for = None
        self.state = NodeState.FOLLOWER
        self.leader_id = None
        self.votes_received = set()
        
        # Log entries
        self.log = []
        self.commit_index = -1
        self.last_applied = -1
        
        # Volatile leader state
        self.next_index = {node: 0 for node in nodes_config}
        self.match_index = {node: -1 for node in nodes_config}
        
        # Timeouts
        self.election_timeout = random.uniform(150, 300) / 1000  # 150-300ms
        self.heartbeat_interval = 0.1  # 100ms
        self.last_heartbeat = time.time()
        
        # Rede
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [Node %(node_id)s] %(message)s',
            handlers=[
                logging.FileHandler(f'/var/log/raft-node-{node_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'node_id': self.node_id})
        
        # Estado persistente
        self.state_file = Path(f"/var/lib/raft/node-{node_id}.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_state()

    def load_state(self):
        """Carrega estado persistente do disco"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_term = state.get('current_term', 0)
                    self.voted_for = state.get('voted_for', None)
                    self.log = state.get('log', [])
            except Exception as e:
                self.logger.error(f"Erro ao carregar estado: {e}")

    def save_state(self):
        """Persiste estado no disco"""
        try:
            with open(self.state_file, 'w') as f:
                state = {
                    'current_term': self.current_term,
                    'voted_for': self.voted_for,
                    'log': self.log
                }
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado: {e}")

    def request_vote(self, term, candidate_id, last_log_index, last_log_term):
        """Processa requisição de voto"""
        if term < self.current_term:
            return {
                'term': self.current_term,
                'vote_granted': False
            }
        
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            self.save_state()
        
        if (self.voted_for is None or self.voted_for == candidate_id) and \
           (len(self.log) == 0 or
            (last_log_term > self.log[-1]['term'] or
             (last_log_term == self.log[-1]['term'] and
              last_log_index >= len(self.log) - 1))):
            self.voted_for = candidate_id
            self.save_state()
            return {
                'term': self.current_term,
                'vote_granted': True
            }
        
        return {
            'term': self.current_term,
            'vote_granted': False
        }

    def append_entries(self, term, leader_id, prev_log_index, prev_log_term,
                      entries, leader_commit):
        """Processa append entries (heartbeat ou novos logs)"""
        if term < self.current_term:
            return {
                'term': self.current_term,
                'success': False
            }
        
        self.last_heartbeat = time.time()
        self.leader_id = leader_id
        
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            self.save_state()
        
        # Verificação de consistência do log
        if prev_log_index >= len(self.log) or \
           (prev_log_index >= 0 and self.log[prev_log_index]['term'] != prev_log_term):
            return {
                'term': self.current_term,
                'success': False
            }
        
        # Adiciona novas entries
        if entries:
            self.log = self.log[:prev_log_index + 1]
            self.log.extend(entries)
            self.save_state()
        
        # Atualiza commit_index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)
        
        return {
            'term': self.current_term,
            'success': True
        }

    def start_election(self):
        """Inicia uma nova eleição"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.save_state()
        
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1]['term'] if self.log else 0
        
        self.logger.info(f"Iniciando eleição para termo {self.current_term}")
        
        # Solicita votos para todos os outros nós
        for node_id, node_config in self.nodes.items():
            if node_id != self.node_id:
                try:
                    response = self.send_request_vote(
                        node_config,
                        self.current_term,
                        last_log_index,
                        last_log_term
                    )
                    
                    if response and response.get('vote_granted'):
                        self.votes_received.add(node_id)
                        
                        # Verifica se ganhou a eleição
                        if len(self.votes_received) > len(self.nodes) / 2:
                            self.become_leader()
                            break
                    
                    elif response and response.get('term') > self.current_term:
                        self.current_term = response['term']
                        self.state = NodeState.FOLLOWER
                        self.voted_for = None
                        self.save_state()
                        break
                        
                except Exception as e:
                    self.logger.error(f"Erro ao solicitar voto de {node_id}: {e}")

    def become_leader(self):
        """Assume o papel de líder"""
        if self.state != NodeState.LEADER:
            self.logger.info("Tornando-se líder")
            self.state = NodeState.LEADER
            self.leader_id = self.node_id
            
            # Inicializa índices
            self.next_index = {node: len(self.log) for node in self.nodes}
            self.match_index = {node: -1 for node in self.nodes}
            
            # Atualiza DNS ou Load Balancer
            self.update_routing()
            
            # Envia heartbeat inicial
            self.send_heartbeat()

    def send_heartbeat(self):
        """Envia heartbeat para todos os seguidores"""
        if self.state == NodeState.LEADER:
            for node_id, node_config in self.nodes.items():
                if node_id != self.node_id:
                    try:
                        prev_log_index = self.next_index[node_id] - 1
                        prev_log_term = self.log[prev_log_index]['term'] if prev_log_index >= 0 else 0
                        
                        entries = self.log[self.next_index[node_id]:]
                        
                        response = self.send_append_entries(
                            node_config,
                            self.current_term,
                            prev_log_index,
                            prev_log_term,
                            entries,
                            self.commit_index
                        )
                        
                        if response:
                            if response.get('success'):
                                if entries:
                                    self.next_index[node_id] = len(self.log)
                                    self.match_index[node_id] = len(self.log) - 1
                            else:
                                self.next_index[node_id] = max(0, self.next_index[node_id] - 1)
                            
                            if response.get('term') > self.current_term:
                                self.current_term = response['term']
                                self.state = NodeState.FOLLOWER
                                self.voted_for = None
                                self.save_state()
                                return
                                
                    except Exception as e:
                        self.logger.error(f"Erro ao enviar heartbeat para {node_id}: {e}")

    def update_routing(self):
        """Atualiza configuração de roteamento (DNS ou Load Balancer)"""
        if self.dns_provider:
            if self.dns_provider['type'] == 'cloudflare':
                self.update_cloudflare_dns()
            elif self.dns_provider['type'] == 'route53':
                self.update_route53_dns()
        
        if self.load_balancer:
            self.update_load_balancer()

    def run(self):
        """Loop principal do nó Raft"""
        # Inicia servidor de rede em thread separada
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        self.logger.info(f"Nó iniciado como {self.state.value}")
        
        while True:
            try:
                current_time = time.time()
                
                if self.state == NodeState.LEADER:
                    if current_time - self.last_heartbeat >= self.heartbeat_interval:
                        self.send_heartbeat()
                        self.last_heartbeat = current_time
                else:
                    # Timeout de eleição para followers e candidates
                    if current_time - self.last_heartbeat >= self.election_timeout:
                        self.start_election()
                        self.last_heartbeat = current_time
                
                time.sleep(0.01)  # Pequena pausa para não sobrecarregar CPU
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                time.sleep(1)

if __name__ == "__main__":
    # Exemplo de configuração
    nodes = {
        'node1': {'ip': '203.0.113.10', 'port': 9000},
        'node2': {'ip': '203.0.113.11', 'port': 9000},
        'node3': {'ip': '203.0.113.12', 'port': 9000}
    }
    
    # Configuração do DNS (opcional)
    dns_config = {
        'type': 'cloudflare',
        'api_key': 'sua_api_key',
        'domain': 'seu_dominio.com',
        'record': 'www'
    }
    
    # Configuração do Load Balancer (opcional)
    lb_config = {
        'api_url': 'https://seu_load_balancer/api',
        'api_key': 'sua_api_key'
    }
    
    # Inicializa e executa o nó
    node = RaftNode(
        'node1',  # Altere para o ID do nó atual
        nodes,
        dns_provider=dns_config,
        load_balancer=lb_config
    )
    
    node.run()