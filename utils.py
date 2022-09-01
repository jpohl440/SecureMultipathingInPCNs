#!/usr/bin/python3

import sys
import matplotlib.pyplot as plt
import networkx as nx


'''
GRAPHML EDGE ATTRIBUTES
attr.name="htlc_maximum_msat" attr.type="long"
attr.name="htlc_minimim_msat" attr.type="long"
attr.name="fee_proportional_millionths" attr.type="long"
attr.name="fee_base_msat" attr.type="long"
attr.name="features" attr.type="string"
attr.name="timestamp" attr.type="long"
attr.name="destination" attr.type="string"
attr.name="source" attr.type="string"
attr.name="scid" attr.type="string"

GRAPHML NODE ATTRIBUTES
attr.name="in_degree" attr.type="long"
attr.name="out_degree" attr.type="long"
attr.name="addresses" attr.type="string"
attr.name="alias" attr.type="string"
attr.name="rgb_color" attr.type="string"
attr.name="features" attr.type="string"
attr.name="timestamp" attr.type="long"
attr.name="id" attr.type="string"
'''

'''
SAMPLE NETWORKX EDGE ATTRIBUTES
(
'0342dd8568081ae1bdd852c0d9440dd22e4bbc432391975e6a1e1f2688e3ca6fc1',
'0242a4ae0c5bef18048fbecf995094b74bfb0f7391418d71ed394784373f41e4f3',
	{
	'scid': '677836x2386x1/1',
	'source': '0342dd8568081ae1bdd852c0d9440dd22e4bbc432391975e6a1e1f2688e3ca6fc1',
	'destination': '0242a4ae0c5bef18048fbecf995094b74bfb0f7391418d71ed394784373f41e4f3',
	'timestamp': 1630848990,
	'fee_base_msat': 1000,
	'fee_proportional_millionths': 1,
	'htlc_minimim_msat': 1000,
	'htlc_maximum_msat': 83517000,
	'cltv_expiry_delta': 40
	}
)

SAMPLE NETWORKX NODE ATTRIBUTES
(
'039a64895e50e2fb4381c908308fe155355ea3332faff5589c8946e1b92f9da7f4',
	{
	'id': '039a64895e50e2fb4381c908308fe155355ea3332faff5589c8946e1b92f9da7f4',
	'timestamp': 1596491959,
	'features': '8000000002aaa2',
	'rgb_color': '039a64',
	'alias': 'PEEVEDDEITY',
	'out_degree': 0,
	'in_degree': 1
	}
)
'''



def print_degrees():
	G = get_graph("graphml")
	deg = nx.degree_histogram(G)

	skip_zero_lines = False
	skip_next = False
	total = sum(deg)
	cumu = 0

	print("DEGR  #NODES".ljust(19, ' ') + "PERC \tCUMULATIVE PERC")
	print("===============================================")
	for i in range(len(deg)):
		if deg[i] == 0 and not skip_zero_lines:
			if not skip_next:
				print("..")
				skip_next = True
		elif deg[i] != 0:
			skip_next = False
			cumu += deg[i]
			print("{0:0>4}: {1}".format(i + 1, deg[i]).ljust(19, ' ') +
			      "{0:0>4}%\t{1}%".format(round(100 * deg[i] / total, 1), round(100 * cumu / total, 1)))

	id = "0342dd8568081ae1bdd852c0d9440dd22e4bbc432391975e6a1e1f2688e3ca6fc1"
	print(f"\nDegree of one particular node identified by id={id}:")
	print(G.degree[id])


def print_shortest_paths_and_adj_nodes():
	G = get_graph("graphml")
	nodes = list(G.nodes(data=True))

	id_1000 = get_node_id(nodes[1000])
	id_2000 = get_node_id(nodes[2000])

	print(f"All shortest paths from id={id_1000} to id={id_2000}:")
	print([(p, len(p)) for p in nx.all_shortest_paths(G, source=id_1000, target=id_2000)])

	p = nx.shortest_path(G, source=id_1000, target=id_2000)
	print(f"One shortest path from id={id_1000} to id={id_2000}:\n{p}")

	adj = G.adj[id_1000]
	print(f"Adjacent nodes of node={id_1000}:\n{adj}")


def print_node_details(n):
	node_dict = n[1]
	for item in node_dict:
		print(f"\t{item}: {node_dict[item]}")
	print("")


def print_edge_details(e):
	edge_dict = e[2]
	for item in edge_dict:
		print(f"\t{item}: {edge_dict[item]}")
	print("")


def print_graph_details():
	G = get_graph("graphml")

	print(f"Number of nodes: {G.number_of_nodes()}")
	print(f"Number of edges: {G.number_of_edges()}")

	nodes = list(G.nodes(data=True))
	print("\nNode details:")
	for i in range(5):
		print(f"[node {i}]")
		print_node_details(nodes[i])

	edges = list(G.edges(data=True))
	print("\nEdge details:")
	for i in range(5):
		print(f"[edge {i}]")
		print_edge_details(edges[i])


# @param type: options are "graphml", "barabasi", "handmade"
def get_graph(graph_type):
	if graph_type == "graphml":
		# GRAPH: read graphml file from console and create an nx graph from it
		f_graphml = sys.argv[1]
		G = nx.read_graphml(f_graphml)
	elif graph_type == "barabasi":
		# GRAPH: Barabasi Albert Graph, similar to LN topology (?)
		G = nx.barabasi_albert_graph(50, 2)
	elif graph_type == "handmade":
		# GRAPH: handmade path graph consisting out of six nodes connected by a set of edges that make
		# the graph an useful sandbox for testing shortest path searches
		G = nx.path_graph(1)
		for i in range(1, 7):
			G.add_node(i, id=i)

		G.add_edge(0, 1, source=0, destination=1, fee_base_msat=2000, fee_proportional_millionths=1)
		G.add_edge(1, 2, source=1, destination=2, fee_base_msat=1000, fee_proportional_millionths=1)
		G.add_edge(2, 3, source=2, destination=3, fee_base_msat=1000, fee_proportional_millionths=1)

		G.add_edge(0, 4, source=0, destination=4, fee_base_msat=1000, fee_proportional_millionths=1)
		G.add_edge(4, 5, source=4, destination=5, fee_base_msat=1000, fee_proportional_millionths=1)
		G.add_edge(5, 3, source=5, destination=3, fee_base_msat=5000, fee_proportional_millionths=1)

		G.add_edge(0, 6, source=0, destination=6, fee_base_msat=1000, fee_proportional_millionths=1)
		G.add_edge(6, 3, source=6, destination=3, fee_base_msat=9000, fee_proportional_millionths=1)
	else:
		print(f"Unknown graph type <{graph_type}>. Falling back onto graphml type.")
		f_graphml = sys.argv[1]
		G = nx.read_graphml(f_graphml)
	return G


# Sample graph that is used to showcase networkX's visualization capabilities.
def visualize_graph_and_print_simple_paths():
	G = get_graph("barabasi")
	print([p for p in nx.all_simple_paths(G, source=20, target=30, cutoff=5)])
	nx.draw(G, with_labels=True)
	plt.hist([v for k, v in nx.degree(G)])
	plt.show()


def get_edge_base_fee(e):
	return e[2]["fee_base_msat"]


def get_edge_prop_fee(e):
	return e[2]["fee_proportional_millionths"]


def get_node_in_degree(n):
	return n[1]["in_degree"]


def get_node_out_degree(n):
	return n[1]["out_degree"]


def get_node_id(n):
	return n[1]["id"]



