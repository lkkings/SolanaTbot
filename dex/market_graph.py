from typing import Dict, List, Set

from core.types.dex import Node, Market
from core.base_dex import to_pair_string


class MintMarketGraph:
    nodes: Dict[str, Node] = {}
    edges: Dict[str, List[Market]] = {}

    def add_mint(self, pub_key: str) -> None:
        if pub_key not in self.nodes:
            self.nodes[pub_key] = Node(pub_key, set())

    def add_market(self, mint1: str, mint2: str, market: Market) -> None:
        self.add_mint(mint1)
        self.add_mint(mint2)

        node1 = self.nodes[mint1]
        node2 = self.nodes[mint2]

        node1.neighbours.add(mint2)
        node2.neighbours.add(mint1)

        edge_key = to_pair_string(mint1, mint2)
        if edge_key not in self.edges:
            self.edges[edge_key] = []
        self.edges[edge_key].append(market)

    def get_neighbours(self, pub_key: str) -> Set[str]:
        node = self.nodes.get(pub_key)
        return node.neighbours if node else set()

    def get_markets(self, mint1: str, mint2: str) -> List[Market]:
        edge_key = to_pair_string(mint1, mint2)
        return self.edges.get(edge_key, [])


market_graph = MintMarketGraph()
