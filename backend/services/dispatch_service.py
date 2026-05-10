from concurrent.futures import ThreadPoolExecutor, as_completed
from services.algorithm_service import AlgorithmService

class DispatchService:

    @staticmethod
    def dispatch_all(technicians: list, customer_lat: float, customer_lon: float, algorithm: str = "astar") -> dict:
        results = []

        def calc_route(tech):
            loc = tech['location']
            if algorithm == "astar":
                route = AlgorithmService.astar(
                    loc['latitude'], loc['longitude'],
                    customer_lat, customer_lon
                )
            else:
                route = AlgorithmService.dijkstra(
                    loc['latitude'], loc['longitude'],
                    customer_lat, customer_lon
                )
            return {**tech, "route": route}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(calc_route, t) for t in technicians]
            for future in as_completed(futures):
                results.append(future.result())

        # Filter yang berhasil
        valid = [r for r in results if r['route']['success']]
        if not valid:
            return {"success": False, "error": "Tidak ada rute valid"}

        # Pilih yang terpendek berdasarkan jarak
        best = min(valid, key=lambda r: r['route']['distance_meters'])
        return {
            "success": True,
            "selected": best,
            "all_routes": valid
        }
