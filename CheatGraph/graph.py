import networkx as nx
import csv
import os

total_data = []
for file in os.listdir('data'):
    if file.endswith('.csv'):
        with open('data/' + file, 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
            total_data.append(data[1:])

G = nx.Graph()
for data in total_data:
    for row in data:
        if not G.has_node(row[0]):
            G.add_node(row[0])
        if not G.has_node(row[1]):
            G.add_node(row[1])
        if not G.has_edge(row[0], row[1]):
            G.add_edge(row[0], row[1], weight=int(row[2]))
        else:
            G[row[0]][row[1]]['weight'] += int(row[2])

nx.write_gexf(G, 'graph.gexf')

edges = sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)
with open('edges.csv', 'w') as f:
    writer = csv.writer(f)
    for edge in edges:
        writer.writerow([edge[0], edge[1], edge[2]['weight']])