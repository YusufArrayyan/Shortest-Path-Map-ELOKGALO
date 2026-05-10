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
                    # Menggunakan titik pusat kampus (Rektorat) dengan radius lebih kecil agar cepat di Render
                    center_point = (-3.7589, 102.2722)
                    ox.settings.requests_timeout = 60 # Timeout lebih lama untuk download
                    G = ox.graph_from_point(center_point, dist=900, network_type="walk")
                    G = ox.add_edge_speeds(G)
                    G = ox.add_edge_travel_times(G)
                    
                    # ADVANCED CAMPUS MESH: Tambahkan jaringan jalur tikus menyeluruh
                    # Menghubungkan Rektorat ke pusat kampus dan gedung-gedung lainnya
                    print("Membangun jaringan jalur tikus (Campus Mesh)...")
                    
                    # Titik-titik krusial di jalur putih/gang
                    P = {
                        "rektorat": (-3.75893, 102.27227),
                        "danau_selatan": (-3.75846, 102.27321),
                        "danau_timur": (-3.75776, 102.27364), # Mushola
                        "bundaran": (-3.75685, 102.27443),
                        "perpus": (-3.75640, 102.27508),
                        "pkm": (-3.75628, 102.27581),
                        "gb5": (-3.75553, 102.27646),
                        "fkip": (-3.75618, 102.27747),
                        "gsg": (-3.75751, 102.27652),
                        "ft": (-3.75842, 102.27663),
                        "faperta": (-3.75932, 102.26922),
                        "fh": (-3.76053, 102.26848),
                    }
                    
                    # Hubungkan titik-titik tersebut menjadi jaringan (mesh)
                    mesh_edges = [
                        ("rektorat", "danau_selatan"), ("danau_selatan", "danau_timur"),
                        ("danau_timur", "bundaran"), ("bundaran", "perpus"),
                        ("perpus", "pkm"), ("pkm", "gb5"), ("pkm", "fkip"),
                        ("gb5", "fkip"), ("bundaran", "gsg"), ("gsg", "ft"),
                        ("gsg", "fkip"), ("rektorat", "faperta"), ("rektorat", "fh")
                    ]
                    
                    for s_key, e_key in mesh_edges:
                        start, end = P[s_key], P[e_key]
                        u = ox.distance.nearest_nodes(G, start[1], start[0])
                        v = ox.distance.nearest_nodes(G, end[1], end[0])
                        dist = ox.distance.great_circle(start[0], start[1], end[0], end[1])
                        # Tambahkan edge dua arah dengan bobot rendah agar diprioritaskan
                        G.add_edge(u, v, length=dist, travel_time=dist/1.5, speed_kph=6, manual=True)
                        G.add_edge(v, u, length=dist, travel_time=dist/1.5, speed_kph=6, manual=True)

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
