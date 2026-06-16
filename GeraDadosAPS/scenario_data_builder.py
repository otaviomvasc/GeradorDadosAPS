import pandas as pd


from Configuration_data import (
    ConfigurationDataScenario,
    PathArquivoDados,
    ExecutionDataType,
)
from distance_API_calculator import (
    DistanceAPICalculatorBySC,
    DistanceAPICalculatorByCluster,
)
import json
import geopandas as gpd
from shapely.geometry import Point, Polygon


class ScenarioDataBuilder:
    def __init__(
        self,
        configuration_data: ConfigurationDataScenario,
        path_arquivos_data: PathArquivoDados,
        create_distance_data: bool,
        code_mun: dict,
    ) -> None:

        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data
        self.create_distance_data = create_distance_data
        self.code_mun = code_mun
        # Será que vale separar em 3 classes ?

    def match_points_to_sectors(self, df_divi):
        # 1. Converter setores em GeoDataFrame
        def parse_polygon(coord_string):
            # Retorna None se o valor for nulo
            if pd.isna(coord_string):
                return None

            try:
                coords = json.loads(coord_string)
                return Polygon(coords[0])
            except json.JSONDecodeError:
                try:
                    open_brackets = coord_string.count("[") - coord_string.count("]")
                    fixed = coord_string + "]" * open_brackets
                    coords = json.loads(fixed)
                    return Polygon(coords[0])
                except Exception:
                    try:
                        last_complete = coord_string.rfind("],")
                        if last_complete > 0:
                            fixed = coord_string[: last_complete + 1] + "]]"
                            coords = json.loads(fixed)
                            return Polygon(coords[0])
                    except Exception:
                        return None

        self.df_setor_censitario["geometry"] = self.df_setor_censitario[
            "coordinates"
        ].apply(parse_polygon)

        gdf_setores = gpd.GeoDataFrame(
            self.df_setor_censitario, geometry="geometry", crs="EPSG:4326"
        )

        gdf_pontos = gpd.GeoDataFrame(
            df_divi,
            geometry=gpd.points_from_xy(
                df_divi["NU_LONGITUDE"], df_divi["NU_LATITUDE"]
            ),
            crs="EPSG:4326",
        )

        gdf_joined = gpd.sjoin(
            gdf_setores,
            gdf_pontos[["CO_UNIDADE", "geometry"]],
            how="left",
            predicate="contains",
        )
        gdf_joined = gdf_joined[~gdf_joined.index.duplicated(keep="first")]

        self.df_setor_censitario["CO_UNIDADE_UBS"] = gdf_joined["CO_UNIDADE"].values

    def read_and_format_path_arquivo_setores_censitarios(self):
        def parse_lat_lon(value):
            s = str(abs(int(value)))  # "1994370594594150"
            integer_part = s[:2]  # "19"
            decimal_part = s[2:]  # "94370594594150"
            return float(f"{integer_part}.{decimal_part}")

        df = pd.read_csv(self.path_arquivos_data.path_arquivo_setores_censitarios)
        code_mun = self.code_mun.get(self.configuration_data.municipio)
        if (
            code_mun is None
        ):  # TODO: PORQUE NAO ESTOU FAZENDO ISSO NO INIT ? burrice enorme
            codigos_cadastrados = list(self.code_mun.keys())
            raise ValueError(
                f"Código do município 'self.configuration_data.municipio' não encontrado. "
                f"Códigos cadastrados: {codigos_cadastrados}"
            )
        df = df[df.CD_MUN_RED == code_mun].reset_index()
        df["LAT"] = df["LAT"].apply(parse_lat_lon)
        df["LONG"] = df["LONG"].apply(parse_lat_lon)
        df = df.drop(columns=["SETOR"])
        df = df.rename(
            columns={
                "MUNICIPIO": "MUNICIPIO",
                "LAT": "LAT",
                "LONG": "LONG",
                "CD_setor_norm": "SETOR",
                "Indice": "Indice",
            }
        )
        df["SETOR"] = pd.to_numeric(df["SETOR"], errors="coerce").fillna(0).astype(int)

        # df["V01006"] = df["V01006"].apply(lambda x: 0 if isinstance(x, str) else x)
        df["V01006"] = (
            pd.to_numeric(df["V01006"], errors="coerce").fillna(0).astype(int)
        )
        self.df_setor_censitario = df[
            ["MUNICIPIO", "SETOR", "V01006", "LAT", "LONG", "Indice"]
        ].copy()

    def read_and_format_path_setores_com_UBS(self):

        df_full = pd.read_excel(self.path_arquivos_data.path_dados_UBS)
        cod_mun = self.code_mun.get(self.configuration_data.municipio)
        df_divi = df_full[
            df_full.CO_MUNICIPIO_GESTOR == cod_mun
        ].reset_index()  # Lagoa Santa = 313760, Divinopolis = 312230, Montes Claros = 314330 e BH  - 310620, COntagem = 311860
        self.match_points_to_sectors(df_divi)
        self.df_setor_censitario.CO_UNIDADE_UBS = (
            self.df_setor_censitario.CO_UNIDADE_UBS.fillna(0)
        )
        # Check se eu tenho duas unidades no mesmo setor:
        mask = (self.df_setor_censitario["CO_UNIDADE_UBS"] != 0) & (
            self.df_setor_censitario["CO_UNIDADE_UBS"].duplicated(keep="first")
        )

        self.df_setor_censitario.loc[mask, "CO_UNIDADE_UBS"] = 0

        self.df_setor_censitario["CO_UNIDADE_UBS"] = pd.to_numeric(
            self.df_setor_censitario["CO_UNIDADE_UBS"], errors="coerce"
        )
        self.df_setor_censitario["CO_UNIDADE_UBS"] = self.df_setor_censitario[
            "CO_UNIDADE_UBS"
        ].fillna(0)
        self.df_setor_censitario["CO_UNIDADE"] = self.df_setor_censitario[
            "CO_UNIDADE_UBS"
        ]  # TODO: Avaliar isso com calma depois o motivo de ter trocado para CO_UNIDADE_UBS e nao ter quebrado nada!

    def read_and_format_dados_IVS(self):
        df = pd.read_excel(self.path_arquivos_data.path_dados_IVS)
        self.df_setor_censitario = self.df_setor_censitario.merge(
            df[
                ["SETOR", "Capital Humano", "Infra Urbana", "Vulnerab. Saúde", "Indice"]
            ],
            how="left",
            on="SETOR",
        )

    def complete_CO_unidade(self, df):
        dict_aux = {
            cnes: max(df.loc[df.CO_CNES == cnes].CO_UNIDADE.to_list())
            for cnes in df.CO_CNES
        }
        for i, row in df.iterrows():
            if row.CO_UNIDADE != row.CO_CNES:
                continue
            co_unidade_end = dict_aux.get(row.CO_CNES, row.CO_CNES)
            df.loc[i, "CO_UNIDADE"] = co_unidade_end

        return df

    def read_and_format_path_equipes_PHC(self):
        code_mun = self.code_mun.get(self.configuration_data.municipio)
        df = pd.read_excel(self.path_arquivos_data.path_equipes_PHC)
        df = df[df.CO_MUNICIPIO_GESTOR == code_mun][
            ["CO_UNIDADE", "TP_EQUIPE", "CO_CNES"]
        ].reset_index(
            drop=True
        )  # TODO: USAR O MUNICIPIO GESTOR SEM HARDCODE
        df = self.complete_CO_unidade(df)
        df_pivot = (
            df.groupby(["CO_UNIDADE", "TP_EQUIPE"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        self.df_setor_censitario = self.df_setor_censitario.merge(
            df_pivot, how="left", on="CO_UNIDADE"
        )

    def read_and_format_SC_to_cluster_data(self):
        self.df_cluster = pd.read_csv(self.path_arquivos_data.path_cluster_CSV)

    def create_cluster_to_SC_without_agg_cluster(self):
        """
        Tratamento para dados quando nao ha correspondencia nos clusters!

        """
        max_actual_cluster_number = max(self.df_setor_censitario["cluster"])

        nan_mask = self.df_setor_censitario["cluster"].isna()
        nan_indices = self.df_setor_censitario[nan_mask].index

        self.df_setor_censitario.loc[nan_indices, "cluster"] = range(
            int(max_actual_cluster_number) + 1,
            int(max_actual_cluster_number) + 1 + len(nan_indices),
        )

    def merge_cluster_in_SC_data(self):
        self.df_setor_censitario = self.df_setor_censitario.merge(
            self.df_cluster, how="left", right_on="CD_SETOR", left_on="SETOR"
        )
        # self.create_cluster_to_SC_without_agg_cluster()

        self.df_cluster["CD_SETOR_txt"] = self.df_cluster.CD_SETOR.astype(str)
        mask = ["311860" in x for x in self.df_cluster["CD_SETOR_txt"]]
        df_cidade = self.df_cluster[mask]

        self.df_setor_censitario["cluster"] = self.df_setor_censitario[
            "cluster"
        ].astype(int)
        self.df_setor_censitario["cluster"] = self.df_setor_censitario["cluster"].apply(
            lambda x: f"CLU_{int(x)}"
        )

    def agg_populacao_por_cluster(self):
        """
        Premissa de agregacao da populacao:
        Somar a populacao de todos os setores do cluster
        """
        df_agg_pop = (
            self.df_setor_censitario.groupby(by="cluster")
            .agg({"V01006": "sum"})
            .reset_index()
        )
        df_agg_pop["V01006"] = round(df_agg_pop["V01006"], 3)
        return df_agg_pop

    def agg_IVS_por_cluster(self):
        """
        IVS vai ser a média de cada um dos setores normalizados (proporcao da pop)
        Verificar se sao a mesma coisa (Dados do Drive e dados dos cluster)
        """
        df_agg_IVS = (
            self.df_setor_censitario.groupby(by="cluster")
            .agg({"Indice": "mean"})
            .reset_index()
        )
        df_agg_IVS["Indice"] = round(df_agg_IVS["Indice"], 3)
        nan_mask = df_agg_IVS["Indice"].isna()
        nan_indices = df_agg_IVS[nan_mask].index

        df_agg_IVS.loc[nan_indices, "Indice"] = "."
        return df_agg_IVS

    def calcula_centro_cluster(self):
        """
        usei o método da média simples porque depois de uma pesquisa vi que esse é o mais comum e mais eficiente para nossa
        aplicacao. Contudo, verificar explicabilidade do método
        """
        lat_final = list()
        long_final = list()
        cluster_final = list()
        for cl in self.df_setor_censitario.cluster.unique():
            df_aux = self.df_setor_censitario[self.df_setor_censitario.cluster == cl]
            lista_lats = df_aux.LAT.to_list()
            lista_long = df_aux.LONG.to_list()
            lat_central = sum(lista_lats) / len(lista_lats)
            lon_central = sum(lista_long) / len(lista_long)
            lat_final.append(lat_central)
            long_final.append(lon_central)
            cluster_final.append(cl)

        df_agg_coords = pd.DataFrame(
            {"cluster": cluster_final, "LAT": lat_final, "LONG": long_final}
        )
        return df_agg_coords

    def allocate_exists_PHC_in_cluster_and_define_geo_coords(self, df_agg_coords):
        """
        DÚVIDA:
        O modelo de dados hoje considera que as equipes estao em setores censitarios, e nao nas coordenadas das UBS em si.
        Vou manter assim e agrupar por cluster, mas validar se é possivel considerar as UBS sem estar dentro dos setores.
        Outro ponto é que podemos ter imprecisao para saber de onde enviar ou colocar recursos.

        """
        cols_PHC = ["CO_UNIDADE", "cluster", "PORTE_UBS"] + [
            i for i in self.df_setor_censitario.columns if isinstance(i, float)
        ]
        df_PHC = self.df_setor_censitario[
            self.df_setor_censitario["CO_UNIDADE_UBS"] != 0
        ][cols_PHC].reset_index()
        self.df_PHC_by_cluster = df_PHC.merge(df_agg_coords, on="cluster", how="inner")

    def set_cluster_to_be_candidate_locations(self):
        """
        Método que vai definir quais sao os cluster que vao ser locais candidatos
        Aqui deve ser incluído o script ou os dados gerados pelo bruno e claudinele.
        Inicialmente vou considerar todos os cluster como locais candidatos

        #"""
        candidate_locations = self.df_CL.id_setor.to_list()
        self.df_setor_censitario["IS_CL"] = self.df_setor_censitario.SETOR.apply(
            lambda x: True if x in candidate_locations else False
        )
        self.cluster_CL = self.df_setor_censitario[
            self.df_setor_censitario["IS_CL"] == True
        ].cluster.unique()
        # self.df_clusters_candidates_PHC_locations = self.df_agg_cluster[["cluster", "LAT", "LONG"]].copy()
        # #self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = self.df_clusters_candidates_PHC_locations.cluster.apply(lambda x: f"CL_cluster_{int(x)}")
        # self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = self.df_clusters_candidates_PHC_locations.cluster

    def set_full_PHC_locations(self):
        """
        Método que vai gerar o dataframe final com a juncao das PHC existentes com os cluster candidatos.
        Importante lembrar que esse conjunto NAO irá para os .dat porque será concatenado no .mod para ter
        mais um mecanismo de validacao dos dados.
        Porém, para o calculo das distancias, ele será util.
        """
        # PHC existentes: mantemos CO_UNIDADE numérico

        self.df_PHC_by_cluster = self.df_PHC_by_cluster[
            ~self.df_PHC_by_cluster.CO_UNIDADE.isna()
        ].reset_index()
        self.df_PHC_by_cluster["CO_UNIDADE"] = self.df_PHC_by_cluster[
            "CO_UNIDADE"
        ].astype(int)
        # Locais candidatos (clusters) já têm CO_UNIDADE como string (ex.: "CL_cluster_X"),
        # então não convertimos para int para preservar a distinção entre eles.
        self.df_full_PHC_locations = pd.concat(
            [self.df_PHC_by_cluster, self.df_clusters_candidates_PHC_locations],
            ignore_index=True,
        )
        self.df_full_PHC_locations = self.df_full_PHC_locations.fillna(0)

    def convert_setor_censitario_em_cluster(self):
        # TODO: Isso deveria ser uma classe separada ?
        self.read_and_format_SC_to_cluster_data()
        self.merge_cluster_in_SC_data()
        self.set_cluster_to_be_candidate_locations()
        df_agg_pop = self.agg_populacao_por_cluster()
        df_agg_IVS = self.agg_IVS_por_cluster()
        df_agg_coords = self.calcula_centro_cluster()

        # TODO: set this in a method!
        self.df_agg_cluster = df_agg_pop.merge(
            df_agg_IVS, on="cluster", how="inner"
        ).merge(df_agg_coords, on="cluster", how="inner")

        self.allocate_exists_PHC_in_cluster_and_define_geo_coords(df_agg_coords)
        self.cluster_CL_coordinates()
        self.set_full_PHC_locations()

    def cluster_CL_coordinates(self):
        self.df_clusters_candidates_PHC_locations = self.df_agg_cluster[
            self.df_agg_cluster.cluster.isin(self.cluster_CL)
        ][["cluster", "LAT", "LONG"]].copy()
        # self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = self.df_clusters_candidates_PHC_locations.cluster.apply(lambda x: f"CL_cluster_{int(x)}")
        self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = (
            self.df_clusters_candidates_PHC_locations.cluster
        )

    def read_and_format_SIZE_PHC(self):
        df_porte_ubs = pd.read_excel(self.path_arquivos_data.path_porte_UBS)
        df_porte_ubs.rename(columns={"PORTE": "PORTE_UBS"}, inplace=True)
        df_porte_ubs["PORTE_UBS"] = df_porte_ubs["PORTE_UBS"].astype(int)
        df_porte_ubs = df_porte_ubs[df_porte_ubs.CO_UNIDADE > 0]
        self.df_setor_censitario = self.df_setor_censitario.merge(
            df_porte_ubs[["CO_UNIDADE", "PORTE_UBS"]], on="CO_UNIDADE", how="left"
        )
        self.df_setor_censitario.loc[
            (self.df_setor_censitario.CO_UNIDADE > 0)
            & (self.df_setor_censitario.PORTE_UBS.isna()),
            "PORTE_UBS",
        ] = 1

    def read_and_format_CL(self):
        try:
            df_CL = pd.read_excel(
                self.path_arquivos_data.path_locais_candidatos,
                sheet_name="Candidatos_Finais",
            )
        except:
            df_CL = pd.read_excel(
                self.path_arquivos_data.path_locais_candidatos,
                sheet_name="Candidatos Finais",
            )
        self.df_CL = df_CL[["id_setor"]]

    def read_and_format_costs_data(self):
        df = pd.read_excel(self.path_arquivos_data.path_dados_custo)
        self.df_custos = df[df.Municipio == self.configuration_data.municipio]

    def check_all_clusters_has_PHC_in_rad(self, dist_SC_PHC):
        """

        Método checa se todos os clusters tem alguma UBS no raio para ser possível a alocacao.
        Caso nao tenha, ele coloca o cluster como obrigatoriamente local candidato!

        """
        cluster_without_PHC = list()
        df_dist = pd.DataFrame(dist_SC_PHC)
        for cluster in self.df_agg_cluster.cluster.unique():
            dists_cluster = df_dist[df_dist.origem == cluster].distancia.to_list()
            if min(dists_cluster) > self.configuration_data.raios_criticos["PHC"]:
                cluster_without_PHC.append(cluster)
        return cluster_without_PHC

    def add_clusters_to_PHC_candidates(self, clusters_without_PHC):
        final_new_CL_data = list()
        for cl in clusters_without_PHC:
            data = {
                "CO_UNIDADE": cl,
                "cluster": cl,
                "PORTE_UBS": 0,
                "LAT": self.df_agg_cluster[
                    self.df_agg_cluster.cluster == cl
                ].LAT.values[0],
                "LONG": self.df_agg_cluster[
                    self.df_agg_cluster.cluster == cl
                ].LONG.values[0],
            }
            final_new_CL_data.append(data)

        new_CL_df = pd.DataFrame(final_new_CL_data)
        self.df_full_PHC_locations = pd.concat(
            [self.df_full_PHC_locations, new_CL_df], ignore_index=True
        ).reset_index(drop=True)

        self.df_full_PHC_locations = self.df_full_PHC_locations.fillna(0)

    def read_and_format_poligon_coordinates_SC(self):
        df = pd.read_excel(
            self.path_arquivos_data.path_dados_poligonos_setor_censitario
        )
        df["CD_SETOR"] = df["CD_SETOR"].str[:-1].astype(int)
        self.df_setor_censitario = self.df_setor_censitario.merge(
            df[["CD_SETOR", "coordinates"]],
            left_on="SETOR",
            right_on="CD_SETOR",
            how="left",
        )

    def merge_CL_in_SC_data(self):
        def create_fake_Candidate_ID(is_CL, sc, cnes):
            if is_CL == True:
                return sc
            return cnes

        is_cl = [
            i in self.df_CL.id_setor.to_list() for i in self.df_setor_censitario.SETOR
        ]
        self.df_setor_censitario["IS_CL"] = is_cl
        self.df_setor_censitario["CO_UNIDADE_UBS"] = self.df_setor_censitario.apply(
            lambda x: create_fake_Candidate_ID(x.IS_CL, x.SETOR, x.CO_UNIDADE_UBS),
            axis=1,
        )

        cols = [70.0, 71.0, 72.0, 74.0]
        self.df_setor_censitario.loc[self.df_setor_censitario.IS_CL, cols] = (
            self.df_setor_censitario.loc[self.df_setor_censitario.IS_CL, cols].fillna(
                0.0
            )
        )

    def build(self):
        self.read_and_format_path_arquivo_setores_censitarios()
        self.read_and_format_poligon_coordinates_SC()
        self.read_and_format_path_setores_com_UBS()
        self.read_and_format_path_equipes_PHC()
        self.read_and_format_SIZE_PHC()
        self.read_and_format_CL()
        self.read_and_format_costs_data()

        if self.configuration_data.tipo_rodada == ExecutionDataType.BY_CLUSTER:
            self.convert_setor_censitario_em_cluster()
            distance_data_creator = DistanceAPICalculatorByCluster(
                self.df_agg_cluster, self.df_full_PHC_locations, "lalala"
            )
            dist_SC_PHC, dist_Exist_PHC_to_all_PHC = distance_data_creator.build()

            # checar quais cluster nao tem PHC no raio e adicionar cluster nos PHCs candidatos
            # recalcular distancias:
            clusters_without_PHC = self.check_all_clusters_has_PHC_in_rad(dist_SC_PHC)
            if clusters_without_PHC:
                self.add_clusters_to_PHC_candidates(clusters_without_PHC)
                distance_data_creator = DistanceAPICalculatorByCluster(
                    self.df_agg_cluster, self.df_full_PHC_locations, "lalala"
                )
                dist_SC_PHC, dist_Exist_PHC_to_all_PHC = distance_data_creator.build()

            return {
                "df_demanda": self.df_agg_cluster,
                "df_PHC_exists_and_candidadtes": self.df_full_PHC_locations,
                "configurations": self.configuration_data,
                "create_distance_data": self.create_distance_data,
                "dist_SC_PHC": dist_SC_PHC,
                "dist_Exist_PHC_to_all_PHC": dist_Exist_PHC_to_all_PHC,
                "df_dados_custos_e_orcamento": self.df_custos,
            }

        else:
            dist_SC_PHC = None
            dist_Exist_PHC_to_all_PHC = None
            self.merge_CL_in_SC_data()
            if self.create_distance_data:
                distance_data_creator = DistanceAPICalculatorBySC(
                    self.path_arquivos_data.path_json_distances,
                    self.df_setor_censitario,
                    "lala",
                    self.df_CL,  # ← ADD: explicit CL list
                )

                dist_SC_PHC, dist_Exist_PHC_to_all_PHC = distance_data_creator.build()

            return {
                "dfs": self.df_setor_censitario,
                "configurations": self.configuration_data,
                "create_distance_data": self.create_distance_data,
                "dist_SC_PHC": dist_SC_PHC,
                "dist_Exist_PHC_to_all_PHC": dist_Exist_PHC_to_all_PHC,
                "df_dados_custos_e_orcamento": self.df_custos,
            }


class ResultConverterDataBuilder(ScenarioDataBuilder):
    def __init__(
        self,
        configuration_data: ConfigurationDataScenario,
        path_arquivos_data: PathArquivoDados,
    ) -> None:

        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data

    def read_and_format_optimization_results(self):
        # ler dados pertinentes para a relacao
        xls = pd.ExcelFile(self.path_arquivos_data.path_result_optimization)
        self.result_dfs = {aba: xls.parse(aba) for aba in xls.sheet_names}

    def build(self):
        self.read_and_format_path_arquivo_setores_censitarios()
        self.read_and_format_poligon_coordinates_SC()
        self.read_and_format_path_setores_com_UBS()
        self.read_and_format_dados_IVS()
        self.read_and_format_path_equipes_PHC()
        self.read_and_format_SIZE_PHC()
        self.read_and_format_CL()
        self.read_and_format_costs_data()
        self.convert_setor_censitario_em_cluster()
        self.read_and_format_optimization_results()

        return {
            "df_demanda": self.df_agg_cluster,
            "df_PHC_exists_and_candidadtes": self.df_full_PHC_locations,
            "configurations": self.configuration_data,
            "df_relacao_SC_cluster": self.df_setor_censitario,
            "result_dfs": self.result_dfs,
        }
