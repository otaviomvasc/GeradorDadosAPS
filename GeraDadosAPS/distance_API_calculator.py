import pandas as pd
import json
import time
import math
from openrouteservice_internal import ORSMatrixClient
import openrouteservice

API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjE3ZTc0NTA2MjIzOTQ2MTliN2JmN2UwMmY1ODFmYTAzIiwiaCI6Im11cm11cjY0In0="

class DistanceAPICalculator:
    def __init__(self):
        self.json_dist_format = dict()
        self.client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    

    def create_base_json_to_get_full_matrix(self):
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()
        self.data_dist = {"sectors": []}
        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            self.data_dist["sectors"].append({"setor": o_id, "latitude": o_lat, "longitude": o_long})

        self.name_instance_data_matriz = f"{self.mun_name}.json"
        with open(self.name_instance_data_matriz, "w", encoding="utf-8") as f:
            json.dump(self.data_dist, f)

    def get_full_dist_matriz_from_API(self):
        self.mun_name = self.df_setor_censitario.MUNICIPIO.unique().tolist()[0]
        output_file_distance = f"{self.mun_name}_distance_generated.json"
        try:
            # Choose your batching strategy:
            
            # Full cross-batch matrix (ALL possible pairs)
            # Good for: When you need distances between ALL locations
            # Warning: This makes many more API calls!
                    
            # Uncomment the following lines if you want the full matrix:
            results = self.client.process_cross_batch_matrix(
                # input_file="LagoaSanta.json",
                # output_file="LagoaSanta_matrix_results_full_matrix.json",
                # input_file="Divinopolis.json",
                # output_file="Divinopolis_matrix_results_full_matrix.json",
                # input_file="MontesClaros.json",
                # output_file="MontesClaros_matrix_results_full_matrix.json",
                # input_file="Contagem.json",
                # output_file="Contagem_matrix_results_full_matrix.json",
                input_file=self.name_instance_data_matriz,
                output_file=output_file_distance,
                batch_size=10,
                delay_between_batches=2.0  # Longer delay for rate limiting
            )
    
            print(f"\nSimple batching generated {len(results)} origin-destination pairs")
            self.path_jsons_instances = output_file_distance
        # Display first few results
            print("\nSample results:")
            for i, result in enumerate(results[:3]):
                print(f"\nResult {i+1}:")
                print(f"Origin: {result['origin']['setor']}")
                print(f"Destination: {result['destination']['setor']}")
                print(f"Distance: {result.get('distance_km', 'N/A')} km")
                print(f"Duration: {result.get('duration_minutes', 'N/A')} minutes")
                
        except Exception as e:
                print(f"Error: {e}")
                print("\nCommon causes of 400 Bad Request:")
                print("1. Invalid API key")
                print("2. Too many locations per batch")
                print("3. Invalid coordinate format")
                print("4. Coordinates outside service area")
                print("5. Rate limit exceeded")
                print("\nTips for batching:")
                print("- Use batch_size=25 for free tier")
                print("- Use batch_size=50 for paid plans")
                print("- Increase delay_between_batches if you hit rate limits")
                        
    def _get_cached_distance(self, origem, destino):
        key1 = (origem, destino)
        key2 = (destino, origem)

        return (
            self.json_dist_format.get(key1)
            or self.json_dist_format.get(key2)
            )

    def _fetch_distance_with_fallback(self, dt):
        #time.sleep(0.1)  # rate limit

        try:
            #return self.get_distance_in_API(dt)
            return self.get_calculate_aproximated_distance(dt)
        except Exception:
            return self.get_calculate_aproximated_distance(dt)

    def get_distances(self, origin_dest_PHC_SC):
        setores_sem_distancias = list()
        dict_dist_final = list()
        for (sc_origem, sc_destino), dt in origin_dest_PHC_SC.items():
            if sc_origem == sc_destino:
                dist = 0
            else:
                dist = self._get_cached_distance(sc_origem, sc_destino)

                if dist is None:
                    # print(f"fallback_{sc_origem}_{sc_destino}")
                    setores_sem_distancias.append(sc_origem)
                    dist = self._fetch_distance_with_fallback(dt)

            dict_dist_final.append({
                    "origem": sc_origem,
                    "destino": sc_destino,
                    "distancia": dist
            })

        return dict_dist_final, setores_sem_distancias

    def get_calculate_aproximated_distance(self, dados_og):
        origem = (dados_og["origin"]["long"], dados_og["origin"]["lat"])
        destino = (dados_og["destination"]["long"], dados_og["destination"]["lat"])

        lon1, lat1 = map(math.radians, origem)
        lon2, lat2 = map(math.radians, destino)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        raio_terra_m = 6371000  # raio médio da Terra em metros
        distancia_m = raio_terra_m * c
        # print("usando distancia haversine!")
        return int(distancia_m)

    def get_distance_in_API(self, dados_og):
        # Origem e destino (lon, lat)
        origem = (dados_og["origin"]["long"], dados_og["origin"]["lat"])
        destino = (dados_og["destination"]["long"], dados_og["destination"]["lat"])
        client = openrouteservice.Client(key=API_KEY)
        rota = client.directions(
            coordinates=[origem, destino],
            profile='driving-car',
            format='json'
        )

        #dist_m = rota['routes'][0]['summary']['distance']
        dist_m = rota['routes'][0]['segments'][0]['distance']
        print(f"Distancia: {dist_m} metros")
        return dist_m



    # def read_distances_from_json(self):
    #     self.df_json_distances = pd.read_json(self.path_jsons_instances)
    #     self.read_distances_PHC_SC()
    #     self.read_distances_SC_to_all_SC()




class DistanceAPICalculatorBySC(DistanceAPICalculator):
    def __init__(self, path_jsons_instances, df_setor_censitario, mun_name, df_CL):
        self.path_jsons_instances = path_jsons_instances
        self.df_setor_censitario = df_setor_censitario
        self.df_CL = df_CL              # ← ADD
        self.json_dist_format = dict()
        self.client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
        self.mun_name = mun_name
    
    def create_origin_dest_PHC_SC(self):
        # ALL sectors are demand origins
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()

        # Destinations: existing PHC (IS_CL=False, CO_UNIDADE_UBS>0)
        # 17
        df_EL = self.df_setor_censitario[
            (self.df_setor_censitario.CO_UNIDADE_UBS > 0) &
            (self.df_setor_censitario.IS_CL == False)
        ]

        # Destinations: candidate locations — driven by df_CL directly
        # 30
        cl_sectors = set(self.df_CL.id_setor.to_list())
        df_CL_rows = self.df_setor_censitario[
            self.df_setor_censitario.SETOR.isin(cl_sectors)
        ]

        # 47
        df_UBS = pd.concat([df_EL, df_CL_rows]).drop_duplicates(subset="SETOR")

        # df_UBS_mask =  [isinstance(i, str) or i > 0 for i in self.df_setor_censitario.CO_UNIDADE_UBS]
        # df_UBS =  self.df_setor_censitario[df_UBS_mask]

        PHC_id = df_UBS.SETOR.to_list()
        PHC_lat = df_UBS.LAT.to_list()
        PHC_long = df_UBS.LONG.to_list()
        origin_dest_pairs = {}
        # (PHC_id, PHC_lat, PHC_long)  e (SC_id, SC_lat, SC_long)
        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            for d_id, d_lat, d_long in zip(PHC_id, PHC_lat, PHC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_dest_PHC_SC = origin_dest_pairs


    def create_origin_dest_Exist_PHC_to_SC(self):
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()
        

        #como saber qual o setor é existente?
        #self.df_setor_censitario[self.df_setor_censitario.CO_UNIDADE_UBS > 0].CO_UNIDADE_UBS.iloc[0]

        # #Aqui precisa ser: Unidades reais e Setores censitrarios
        # exist_PHC_unds = [isinstance(i, float) and i > 0 for i in self.df_setor_censitario.CO_UNIDADE_UBS]
        # df_UBS =  self.df_setor_censitario[exist_PHC_unds]
        
        # PHC_id = df_UBS.SETOR.to_list()
        # PHC_lat = df_UBS.LAT.to_list()
        # PHC_long = df_UBS.LONG.to_list()

        # Only truly existing PHC — IS_CL=False ensures CL sectors are excluded
        df_EL = self.df_setor_censitario[
            (self.df_setor_censitario.CO_UNIDADE_UBS > 0) &
            (self.df_setor_censitario.IS_CL == False)      # ← was: isinstance(i, float) — WRONG
        ]

        PHC_id = df_EL.SETOR.to_list()
        PHC_lat = df_EL.LAT.to_list()
        PHC_long = df_EL.LONG.to_list()
        
        origin_dest_pairs = {}
        for o_id, o_lat, o_long in zip(PHC_id, PHC_lat, PHC_long):
            for d_id, d_lat, d_long in zip(SC_id, SC_lat, SC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_dest_Exist_PHC_to_SC = origin_dest_pairs

    def create_origin_dest_PHC_to_same_facilities_level(self):
    # Destinations: existing PHC (IS_CL=False, CO_UNIDADE_UBS>0)
        df_EL = self.df_setor_censitario[
            (self.df_setor_censitario.CO_UNIDADE_UBS > 0) &
            (self.df_setor_censitario.IS_CL == False)
        ]

        # Destinations: candidate locations — driven by df_CL directly
        cl_sectors = set(self.df_CL.id_setor.to_list())        
        df_CL = self.df_setor_censitario[
            self.df_setor_censitario.SETOR.isin(cl_sectors)
        ]        
        
        df_UBS = pd.concat([df_EL, df_CL]).drop_duplicates(subset="SETOR")

        # EL_id  = df_EL.SETOR.to_list()
        EL_id  = df_EL.CO_UNIDADE_UBS.astype(int).to_list()
        EL_lat  = df_EL.LAT.to_list()
        EL_long  = df_EL.LONG.to_list()

        CL_id  = df_CL.SETOR.to_list()
        

        # PHC_id = df_UBS.SETOR.to_list()
        PHC_id = EL_id + CL_id
        PHC_lat = df_UBS.LAT.to_list()
        PHC_long = df_UBS.LONG.to_list()
        
        origin_dest_pairs = {}
        # (df_EL > PHC_id)

        for o_id, o_lat, o_long in zip(EL_id, EL_lat, EL_long):
            for d_id, d_lat, d_long in zip(PHC_id, PHC_lat, PHC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }        

        # guarda no objeto para uso posterior
        self.origin_dest_exist_PHC_all_PHC = origin_dest_pairs




    def create_origin_dest_SC_PHC(self):
        # ALL sectors are demand origins
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()


    # Destinations: existing PHC (IS_CL=False, CO_UNIDADE_UBS>0)
        df_EL = self.df_setor_censitario[
            (self.df_setor_censitario.CO_UNIDADE_UBS > 0) &
            (self.df_setor_censitario.IS_CL == False)
        ]

        # Destinations: candidate locations — driven by df_CL directly
        cl_sectors = set(self.df_CL.id_setor.to_list())        
        df_CL = self.df_setor_censitario[
            self.df_setor_censitario.SETOR.isin(cl_sectors)
        ]        
        
        df_UBS = pd.concat([df_EL, df_CL]).drop_duplicates(subset="SETOR")

        # EL_id  = df_EL.SETOR.to_list()
        EL_id  = df_EL.CO_UNIDADE_UBS.astype(int).to_list()
        EL_lat  = df_EL.LAT.to_list()
        EL_long  = df_EL.LONG.to_list()

        CL_id  = df_CL.SETOR.to_list()
        

        # PHC_id = df_UBS.SETOR.to_list()
        PHC_id = EL_id + CL_id
        PHC_lat = df_UBS.LAT.to_list()
        PHC_long = df_UBS.LONG.to_list()
        
        origin_dest_pairs = {}
        # (df_EL > PHC_id)

        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            for d_id, d_lat, d_long in zip(PHC_id, PHC_lat, PHC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }        

        # guarda no objeto para uso posterior
        self.origin_dest_SC_PHC = origin_dest_pairs




    def read_and_format_json(self):
        if not self.path_jsons_instances:
            self.create_base_json_to_get_full_matrix()
            self.get_full_dist_matriz_from_API()

        with open(self.path_jsons_instances, encoding="utf-8") as f:
            json_dist = (json.load(f))


        for item in json_dist:
            o = item["origin"]["setor"]
            d = item["destination"]["setor"]
            self.json_dist_format[(o, d)] = item['distance_meters'] #TODO: Flag nas configuracoes para saber o que usar de distancia!


    def build(self):
        self.create_origin_dest_PHC_SC()
        "ATENCAO: TEM UM ERRO AQUI! - CHECAR SE PRECISO DAS DISTANCIAS ENTRE TODOS OS SETORES CENSITARIOS!"
        self.create_origin_dest_Exist_PHC_to_SC()
        self.create_origin_dest_SC_PHC()
        self.create_origin_dest_PHC_to_same_facilities_level()
        #self.read_and_format_json()
        dist_PHC_SC, setores_sem_distancia_PHC = self.get_distances(self.origin_dest_PHC_SC)
        dist_SC_PHC, setores_sem_distancia_PHC = self.get_distances(self.origin_dest_SC_PHC)
        dist_SC_SC, setores_sem_distancia_SC = self.get_distances(self.origin_dest_Exist_PHC_to_SC)
        dist_Exist_PHC_to_all_PHC, setores_sem_distancia_SC = self.get_distances(self.origin_dest_exist_PHC_all_PHC)        
       
        #Preciso das distancias entre:
            # dist_SC_PHC (origem: setor censitario - destino: todas as unidades PHC)
            # dist_Exist_PHC_to_all_PHC
        
        # return dist_PHC_SC, dist_SC_SC, dist_Exist_PHC_to_all_PHC
        return dist_SC_PHC, dist_Exist_PHC_to_all_PHC
        


class DistanceAPICalculatorByCluster(DistanceAPICalculator):
    def __init__(self,df_agg_cluster, df_full_PHC_locations, mun_name  ):
        self.df_agg_cluster = df_agg_cluster
        self.df_full_PHC_locations = df_full_PHC_locations
        self.mun_name = mun_name

    def read_and_format_json(self):
        """
        Quando for necessario colocar a busca das distancias via API, mover o método 
        read_and_format_json para a classe pai e usar os mesmos em ambas as formas de gerar os dados!
        """
        self.json_dist_format = {}

    def create_origin_dest_demand_points_to_PHC_in_Clusters(self):
        SC_id = self.df_agg_cluster.cluster.to_list()
        SC_lat = self.df_agg_cluster.LAT.to_list()
        SC_long = self.df_agg_cluster.LONG.to_list()
        PHC_id = self.df_full_PHC_locations.CO_UNIDADE.to_list()
        PHC_lat = self.df_full_PHC_locations.LAT.to_list()
        PHC_long = self.df_full_PHC_locations.LONG.to_list()
        origin_dest_pairs = {}
        
        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            for d_id, d_lat, d_long in zip(PHC_id, PHC_lat, PHC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_demand_PHC = origin_dest_pairs


    def create_origin_dest_PHC_to_same_facilities_level(self):
        EL_mask = [True if not isinstance(i, str) else False
                    for i in self.df_full_PHC_locations.CO_UNIDADE.to_list()] #TODO: Receber 2 dfs e usar ISIN

        df_EL = self.df_full_PHC_locations[EL_mask]
        PHC_id = df_EL.CO_UNIDADE.to_list()
        PHC_lat = df_EL.LAT.to_list()
        PHC_long = df_EL.LONG.to_list()

        df_all_UBS_LOC = self.df_full_PHC_locations
        SC_id = df_all_UBS_LOC.CO_UNIDADE.to_list()
        SC_lat = df_all_UBS_LOC.LAT.to_list()
        SC_long = df_all_UBS_LOC.LONG.to_list()
        
        origin_dest_pairs = {}

        for o_id, o_lat, o_long in zip(PHC_id, PHC_lat, PHC_long):
            for d_id, d_lat, d_long in zip(SC_id, SC_lat, SC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_dest_exist_PHC_all_PHC = origin_dest_pairs

    
        



    def build(self):
        self.create_origin_dest_demand_points_to_PHC_in_Clusters()
        self.create_origin_dest_PHC_to_same_facilities_level()
        self.read_and_format_json()
        dist_SC_PHC, setores_sem_distancia_PHC = self.get_distances(self.origin_demand_PHC)
        dist_Exist_PHC_to_all_PHC, setores_sem_distancia_SC = self.get_distances(self.origin_dest_exist_PHC_all_PHC)

        return dist_SC_PHC, dist_Exist_PHC_to_all_PHC
        