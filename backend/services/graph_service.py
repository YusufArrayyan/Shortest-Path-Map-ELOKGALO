import osmnx as ox
import networkx as nx
import pickle
import os
import threading

# Di Render (production), /tmp adalah satu-satunya direktori yang writable
# Di lokal, simpan di root repo (satu level di atas backend/)
IS_PRODUCTION = os.environ.get("RENDER", False)

if IS_PRODUCTION:
    GRAPH_CACHE = "/tmp/bengkulu_graph.pkl"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    GRAPH_CACHE = os.path.join(BASE_DIR, "bengkulu_graph.pkl")

class GraphService:
    _graph = None
    _lock = threading.Lock()

    @classmethod
    def get_graph(cls):
        with cls._lock:
            if cls._graph is None:
                if os.path.exists(GRAPH_CACHE):
                    with open(GRAPH_CACHE, "rb") as f:
                        cls._graph = pickle.load(f)
                    print("Graf dimuat dari cache.")
                else:
                    print("Mengunduh graf Universitas Bengkulu dari OpenStreetMap...")
                    # Menggunakan titik pusat kampus (Rektorat) dengan radius agar lebih detail
                    center_point = (-3.7589, 102.2722)
                    G = ox.graph_from_point(center_point, dist=1500, network_type="walk")
                    G = ox.add_edge_speeds(G)
                    G = ox.add_edge_travel_times(G)
                    
                    # Tambahkan Manual Shortcuts (Gang-gang/Jalan Tikus)
                    # Sesuai logika Google Maps dan permintaan user
                    shortcuts = [
                        ((-3.7555, 102.2764), (-3.7564, 102.2758)), # GB 5 to PKM
                        ((-3.7564, 102.2758), (-3.7567, 102.2748)), # PKM to Perpus
                        ((-3.7567, 102.2748), (-3.7589, 102.2722)), # Perpus to Rektorat
                        ((-3.7593, 102.2692), (-3.7589, 102.2722)), # Faperta to Rektorat
                        ((-3.7605, 102.2684), (-3.7589, 102.2722)), # FH to Rektorat
                        ((-3.7561, 102.2774), (-3.7575, 102.2765)), # FKIP to GSG
                        ((-3.7575, 102.2765), (-3.7584, 102.2766)), # GSG to FT
                    ]
                    
                    print("Menambahkan jalur tikus manual...")
                    for start, end in shortcuts:
                        u = ox.distance.nearest_nodes(G, start[1], start[0])
                        v = ox.distance.nearest_nodes(G, end[1], end[0])
                        dist = ox.distance.great_circle(start[0], start[1], end[0], end[1])
                        # Tambahkan edge dua arah (pedestrian bisa lewat dua arah)
                        G.add_edge(u, v, length=dist, travel_time=dist/1.1, speed_kph=4, manual=True)
                        G.add_edge(v, u, length=dist, travel_time=dist/1.1, speed_kph=4, manual=True)

                    cls._graph = G
                    try:
                        with open(GRAPH_CACHE, "wb") as f:
                            pickle.dump(G, f)
                        print("Graf berhasil disimpan ke cache.")
                    except Exception as e:
                        print(f"Warning: Tidak bisa menyimpan cache: {e}")
        return cls._graph

    @classmethod
    def get_nearest_node(cls, lat: float, lon: float) -> int:
        G = cls.get_graph()
        return ox.distance.nearest_nodes(G, lon, lat)

    @classmethod
    def get_polyline_coords(cls, path: list) -> list:
        G = cls.get_graph()
        coords = []
        if not path:
            return coords
            
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge_data = G[u][v][0]
            
            if 'geometry' in edge_data:
                for lon, lat in list(edge_data['geometry'].coords)[:-1]:
                    coords.append([lat, lon])
            else:
                u_data = G.nodes[u]
                coords.append([u_data['y'], u_data['x']])
                
        last_node = path[-1]
        last_data = G.nodes[last_node]
        coords.append([last_data['y'], last_data['x']])
        
        return coords
