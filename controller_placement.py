import numpy as np
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import networkx as nx
import matplotlib.pyplot as plt

def generate_campus_topology():
    """Define the campus topology as a graph."""
    G = nx.Graph()

    # Add nodes representing switches
    G.add_nodes_from(['core1', 'core2', 'dist1', 'dist2', 'dist3', 'dist4', 'acc1', 'acc2', 'acc3', 'acc4'])

    # Define links between switches based on your campus topology
    edges = [
        ('core1', 'core2'),
        ('core1', 'dist1'), ('core1', 'dist2'),
        ('core2', 'dist3'), ('core2', 'dist4'),
        ('dist1', 'acc1'), ('dist2', 'acc2'),
        ('dist3', 'acc3'), ('dist4', 'acc4')
    ]
    G.add_edges_from(edges)

    return G

def calculate_latencies(graph):
    """Calculate latencies (shortest paths) between all pairs of nodes."""
    nodes = list(graph.nodes)
    latency_matrix = np.zeros((len(nodes), len(nodes)))

    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i != j:
                try:
                    # Use the shortest path as latency
                    latency_matrix[i, j] = nx.shortest_path_length(graph, source=node1, target=node2)
                except nx.NetworkXNoPath:
                    latency_matrix[i, j] = float('inf')  # No path available

    return latency_matrix, nodes

def k_median_clustering(latency_matrix, nodes, k):
    """Perform k-median clustering to find optimal controller placement."""
    coords = np.array(latency_matrix)

    # Use KMeans for clustering (k-median equivalent)
    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
    kmeans.fit(coords)

    # Cluster centers and labels
    cluster_centers = kmeans.cluster_centers_
    labels = kmeans.labels_

    # Map cluster centers back to nodes
    controller_nodes = []
    for center in cluster_centers:
        min_dist = float('inf')
        closest_node = None
        for i, row in enumerate(latency_matrix):
            dist = np.linalg.norm(center - row)
            if dist < min_dist:
                min_dist = dist
                closest_node = nodes[i]
        controller_nodes.append(closest_node)

    return controller_nodes, labels

def visualize_topology(graph, controllers, labels):
    """Visualize the topology and controller placement."""
    pos = nx.spring_layout(graph)
    colors = ['red' if node in controllers else 'blue' for node in graph.nodes]

    # Draw the graph
    nx.draw(graph, pos, with_labels=True, node_color=colors, node_size=500, font_size=10)
    plt.title("Campus Topology with Controller Placement")
    plt.show()

def main():
    # Step 1: Generate the campus topology
    graph = generate_campus_topology()

    # Step 2: Calculate latencies between all pairs of nodes
    latency_matrix, nodes = calculate_latencies(graph)

    # Step 3: Perform k-median clustering for controller placement
    k = 2  # Adjust the number of controllers as needed
    controllers, labels = k_median_clustering(latency_matrix, nodes, k)

    # Step 4: Display results
    print(f"Optimal controller placement: {controllers}")

    # Step 5: Visualize the topology and controller placement
    visualize_topology(graph, controllers, labels)

if __name__ == "__main__":
    main()

