from dataclasses import dataclass
from re import S
from enum import Enum, auto


class ExecutionDataType(Enum):
    BY_CLUSTER = "cluster"
    BY_SETOR_CENSITARIO = "setor_censitario"

@dataclass
class ConfigurationDataScenario:
    municipio: str
    raios_criticos: dict
    custos_mensais_SHC:dict
    custos_mensais_THC:dict
    equipes_saude_primario: list
    equipes_saude_secundario: list
    equipes_saude_terciario: list
    name_output_file:str
    maximo_de_unidades_abertas: dict
    encaminhamentos_primeiro_nivel:dict
    encaminhamentos_segundo_nivel:dict
    encaminhamentos_terceiro_nivel:dict
    maximo_atendimentos_telemedicina:dict
    maximo_deslocamento: dict
    name_output_file_distancias: str
    tipo_rodada: ExecutionDataType = ExecutionDataType.BY_CLUSTER
    # tipo_rodada: ExecutionDataType = ExecutionDataType.BY_SETOR_CENSITARIO


@dataclass
class PathArquivoDados:
    path_arquivo_setores_censitarios:str
    path_dados_IVS:str
    path_equipes_PHC:str
    path_setores_com_UBS:str
    path_porte_UBS: str
    path_json_distances:str = None
    path_arquivos_dat_final:str = None
    path_cluster_CSV:str = None
    path_locais_candidatos:str = None
    path_dados_custo: str = None
    path_result_optimization: str = None
    path_nome_relatorio_convertido: str = None
    path_dados_poligonos_setor_censitario: str = None
    path_dados_UBS: str = None



