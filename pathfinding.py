#!/usr/bin/python3

import sys
import matplotlib.pyplot as plt
import networkx as nx
from csiphash24 import siphash24 as sh24
import utils as u
import route_hijacking as rh
import random as rnd


def sandbox():
	# How many nodes have degree 1, 2, 3, etc. in a formatted table
	u.print_degrees()

	# Print all shortest paths and neighbour nodes
	# u.print_shortest_paths_and_adj_nodes()

	# Print small sample of nodes and edges to explore their format
	# u.print_graph_details()

	# Sample graph that is used to showcase networkX's visualization capabilities.
	# u.visualize_graph_and_print_simple_paths()


'''
1 BTC
= 100.000.000 SAT
= 100.000.000.000 MSAT
'''


HASH = 0xfedcba9876543210  # TODO: Make this random 64-bit values, produced by siphash24
AMOUNT = 1000  # This probably needs to be global so the weight function can read and write it individually for each hop
RISK_FACTOR = 10  # 10 by default
MILLION = 1000000
COUNTER = 0


def cln_weigth(edge):
	fuzz = rnd.randint(0,1000)/10000-0.05  # +- 0.05 by default
	scale = 1 + fuzz*(2*HASH/(2**64 - 1) + 1)
	base_fee = edge["fee_base_msat"]
	prop_fee = edge["fee_proportional_millionths"]*1/MILLION
	delay = 1  # TODO: Find out how this value is determined
	fee = scale*(base_fee + AMOUNT*prop_fee)
	weight = (AMOUNT + fee)*(delay*RISK_FACTOR) + 1
	return weight


def main():
	if len(sys.argv) != 2:
		print("Usage: ./graphml_networkX_demo.py <GRAPHML FILE>")
		exit()

	# sandbox()

	G = u.get_graph("handmade")  # possible options: "graphml", "barabasi", "handmade"
	rnd.seed()

	src, tgt = 0, 3

	# Sets can't be used with lists because they are not hashable
	unique_single_paths_set = set(tuple(p) for p in nx.all_simple_edge_paths(G, src, tgt))

	# Make flattened list from set
	endpoint_list = [ep for sublist in list(unique_single_paths_set) for ep in sublist]
	print(f"Endpoint list:\n{endpoint_list}")

	# Change "weight" attribute of all edges
	for ep in endpoint_list:
		edge = G[ep[0]][ep[1]]
		edge["weight"] = cln_weigth(edge)

	# print(f"All paths from source={src} to target={tgt}:")
	# for p in nx.all_simple_paths(G, source=src, target=tgt):
		# print(p)

	print(f"\nLowest weighted path from source={src} to target={tgt}:")
	print(nx.shortest_path(G, source=src, target=tgt, weight="weight"))

	print(f"\nPath weight from source={src} to target={tgt}:")
	print(nx.dijkstra_path_length(G, src, tgt))

	nx.draw_networkx(G, with_labels=True)
	plt.show()


if __name__ == "__main__":
	main()
