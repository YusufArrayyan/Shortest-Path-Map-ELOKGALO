import networkx as nx
import osmnx as ox
from services.graph_service import GraphService

class AlgorithmService:

    @staticmethod
    def astar(source_lat, source_lon, target_lat, target_lon) -> dict:
        G = GraphService.get_graph()
        source_node = GraphService.get_nearest_node(source_lat, source_lon)
        target_node = GraphService.get_nearest_node(target_lat, target_lon)

        def heuristic(u, v):
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            return ox.distance.great_circle(
                u_data['y'], u_data['x'],
                v_data['y'], v_data['x']
            )

        try:
            path = nx.astar_path(
                G, source_node, target_node,
                heuristic=heuristic,
                weight='travel_time'
            )
            distance = sum(
                G[u][v][0].get('length', 0)
                for u, v in zip(path[:-1], path[1:])
            )
            duration = sum(
                G[u][v][0].get('travel_time', 0)
                for u, v in zip(path[:-1], path[1:])
            )
            polyline = GraphService.get_polyline_coords(path)
            return {
                "algorithm": "astar",
                "path_nodes": path,
                "distance_meters": round(distance, 2),
                "duration_seconds": round(duration, 2),
                "polyline": polyline,
                "success": True
            }
        except nx.NetworkXNoPath:
            return {"success": False, "error": "Rute tidak ditemukan"}

    @staticmethod
    def dijkstra(source_lat, source_lon, target_lat, target_lon) -> dict:
        G = GraphService.get_graph()
        source_node = GraphService.get_nearest_node(source_lat, source_lon)
        target_node = GraphService.get_nearest_node(target_lat, target_lon)

        try:
            path = nx.dijkstra_path(G, source_node, target_node, weight='length')
            distance = nx.dijkstra_path_length(G, source_node, target_node, weight='length')
            duration = sum(
                G[u][v][0].get('travel_time', 0)
                for u, v in zip(path[:-1], path[1:])
            )
            polyline = GraphService.get_polyline_coords(path)
            return {
                "algorithm": "dijkstra",
                "path_nodes": path,
                "distance_meters": round(distance, 2),
                "duration_seconds": round(duration, 2),
                "polyline": polyline,
                "success": True
            }
        except nx.NetworkXNoPath:
            return {"success": False, "error": "Rute tidak ditemukan"}
