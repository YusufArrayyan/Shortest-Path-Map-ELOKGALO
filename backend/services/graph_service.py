import osmnx as ox
import networkx as nx
import pickle
import os
import threading
from shapely.geometry import LineString

IS_PRODUCTION = os.environ.get("RENDER", False)

if IS_PRODUCTION:
    GRAPH_CACHE = "/tmp/unib_campus_graph.pkl"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    GRAPH_CACHE = os.path.join(BASE_DIR, "unib_campus_graph.pkl")

# Koordinat gedung-gedung kampus UNIB (presisi tinggi, titik di jalan terdekat)
CAMPUS_BUILDINGS = {
    "gb5":          (-3.75576, 102.27690),
    "rektorat":     (-3.75893, 102.27220),
    "perpustakaan": (-3.75708, 102.27577),
    "fkip":         (-3.75618, 102.27747),
    "fh":           (-3.76053, 102.26848),
    "feb":          (-3.76166, 102.26855),
    "fmipa":        (-3.75500, 102.27800),
    "ft":           (-3.75842, 102.27663),
    "fp":           (-3.75932, 102.26922),
    "fisip":        (-3.76000, 102.27100),
    "fkip_gd_b":   (-3.75680, 102.27800),
    "pkm":          (-3.75628, 102.27581),
    "gsg":          (-3.75751, 102.27652),
    "masjid":       (-3.75910, 102.27430),
    "lab_fisika":   (-3.75566, 102.27464),
}

# Jalan-jalan internal kampus yang PASTI ADA di OSM
# Urutan titik mengikuti jalan putih yang terlihat di peta
CAMPUS_ROAD_WAYPOINTS = {
    # Jalur Utama: GB5 -> Perpus -> Bundaran -> Mushola -> Rektorat
    "main_corridor": [
        (-3.75576, 102.27690),  # GB5 parkir
        (-3.75593, 102.27689),
        (-3.75687, 102.27676),
        (-3.75689, 102.27655),
        (-3.75703, 102.27657),
        (-3.75708, 102.27577),  # Perpustakaan
        (-3.75727, 102.27494),  # Bundaran
        (-3.75719, 102.27486),
        (-3.75719, 102.27480),
        (-3.75731, 102.27473),
        (-3.75750, 102.27426),
        (-3.75760, 102.27418),
        (-3.75761, 102.27416),
        (-3.75766, 102.27411),
        (-3.75770, 102.27404),
        (-3.75777, 102.27392),  # Mushola
        (-3.75811, 102.27324),
        (-3.75813, 102.27324),
        (-3.75831, 102.27281),
        (-3.75854, 102.27225),
        (-3.75890, 102.27232),
        (-3.75893, 102.27220),  # Rektorat
    ],
}


class GraphService:
    _graph = None
    _lock = threading.Lock()

    @classmethod
    def get_graph(cls):
        with cls._lock:
            if cls._graph is None:
                # Hapus cache lama agar pakai graf baru yang lebih baik
                if os.path.exists(GRAPH_CACHE):
                    with open(GRAPH_CACHE, "rb") as f:
                        cls._graph = pickle.load(f)
                    print("Graf dimuat dari cache.")
                else:
                    print("Mengunduh graf UNIB dari OpenStreetMap...")
                    center_point = (-3.7589, 102.2722)
                    ox.settings.requests_timeout = 60
                    G = ox.graph_from_point(center_point, dist=1000, network_type="walk")
                    G = ox.add_edge_speeds(G)
                    G = ox.add_edge_travel_times(G)

                    # ================================================================
                    # CAMPUS ROAD INJECTION:
                    # Tambahkan node dan edge TEPAT di jalan putih kampus yang
                    # mungkin belum terhubung dengan baik di OSM.
                    # Caranya: buat node baru dengan ID unik, lalu hubungkan
                    # secara berurutan sesuai urutan jalan putih di peta.
                    # ================================================================
                    print("Menyuntikkan jaringan jalan internal kampus...")

                    node_id_counter = max(G.nodes()) + 1

                    for road_name, waypoints in CAMPUS_ROAD_WAYPOINTS.items():
                        prev_node = None
                        for lat, lon in waypoints:
                            # Cek apakah ada node OSM di dekat titik ini (< 20m)
                            nearest = ox.distance.nearest_nodes(G, lon, lat)
                            n_data = G.nodes[nearest]
                            dist = ox.distance.great_circle(lat, lon, n_data['y'], n_data['x'])

                            if dist < 20:
                                # Gunakan node OSM yang sudah ada
                                curr_node = nearest
                            else:
                                # Buat node baru
                                curr_node = node_id_counter
                                node_id_counter += 1
                                G.add_node(curr_node, y=lat, x=lon, osmid=curr_node,
                                           street_count=2, ref='campus_road')

                            if prev_node is not None and prev_node != curr_node:
                                p_data = G.nodes[prev_node]
                                c_data = G.nodes[curr_node]
                                seg_len = ox.distance.great_circle(
                                    p_data['y'], p_data['x'],
                                    c_data['y'], c_data['x']
                                )
                                walk_speed_ms = 1.4  # 5 km/h pedestrian
                                travel_t = seg_len / walk_speed_ms

                                # Edge geometry sebagai LineString
                                geom = LineString([(p_data['x'], p_data['y']),
                                                   (c_data['x'], c_data['y'])])

                                # Tambahkan dua arah
                                for u_n, v_n in [(prev_node, curr_node), (curr_node, prev_node)]:
                                    if not G.has_edge(u_n, v_n):
                                        G.add_edge(u_n, v_n,
                                                   osmid=f"campus_{road_name}",
                                                   name=f"Jalan Kampus UNIB ({road_name})",
                                                   highway="footway",
                                                   length=seg_len,
                                                   speed_kph=5,
                                                   travel_time=travel_t,
                                                   geometry=geom,
                                                   campus_road=True)

                            prev_node = curr_node

                    cls._graph = G
                    try:
                        with open(GRAPH_CACHE, "wb") as f:
                            pickle.dump(G, f)
                        print(f"Graf berhasil disimpan ke cache: {GRAPH_CACHE}")
                    except Exception as e:
                        print(f"Warning: Tidak bisa menyimpan cache: {e}")
        return cls._graph

    @classmethod
    def get_nearest_node(cls, lat: float, lon: float) -> int:
        G = cls.get_graph()
        # Cari node terdekat dengan mempertimbangkan node campus_road kita
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

            # Coba ambil dari edge key 0, fallback ke key lain
            edge_data = None
            if G.has_edge(u, v):
                edge_keys = list(G[u][v].keys())
                edge_data = G[u][v][edge_keys[0]]

            if edge_data and 'geometry' in edge_data:
                geom_coords = list(edge_data['geometry'].coords)
                for lon_c, lat_c in geom_coords[:-1]:
                    coords.append([lat_c, lon_c])
            else:
                u_data = G.nodes[u]
                coords.append([u_data['y'], u_data['x']])

        last_node = path[-1]
        last_data = G.nodes[last_node]
        coords.append([last_data['y'], last_data['x']])

        return coords
