# Gerador de Dados APS - Atenção Primária à Saúde

Ferramenta para geração automatizada de arquivos de dados (`.dat`) para modelos de otimização em AMPL/GLPK, focada em problemas de localização de unidades de saúde e alocação de equipes.

## 📋 Sobre o Projeto

Este projeto faz parte de uma pesquisa do CNPq sobre aumento da cobertura de Atenção Primária à Saúde (PHC) com dimensionamento de equipes. A ferramenta automatiza a criação de arquivos de dados para modelos de otimização que consideram:

- Localização de unidades de saúde fixas e intermediárias
- Alocação de equipes de saúde (eSF, eSB, eMulti, ACS)
- Distâncias entre setores censitários e unidades de saúde
- Encaminhamentos entre níveis de atenção (primário, secundário, terciário)
- Restrições orçamentárias e de capacidade

## 🏗️ Estrutura do Projeto


GeradorDadosAPS/
├── Configuration_data.py          # Classes de configuração e tipos de dados
├── Text_Creator.py               # Geração de arquivos de texto .dat
├── scenario_data_builder.py      # Construção e formatação dos dados
├── distance_API_calculator.py    # Cálculo de distâncias via API
├── openrouteservice_internal.py  # Cliente para API OpenRouteService
├── writer_text_in_file.py        # Escrita dos arquivos de saída
├── create_dat_files.py           # Orquestrador principal
├── Cluster_Converter.py          # Conversão de resultados cluster→setor censitário
├── step_convert_Cluster_in_SC.py # Etapa de conversão de clusters
├── main.py                       # Ponto de entrada principal
└── Dados/                        # Diretório de dados
    └── Dados_todos_municipios/   # Dados compartilhados entre municípios


## 🚀 Funcionalidades

### Principais Características
- **Geração de arquivos .dat** para modelos AMPL/GLPK
- **Suporte a dois modos de agregação**:
  - Por setor censitário (granularidade fina)
  - Por cluster (agrupamento de setores)
- **Cálculo de distâncias** via API OpenRouteService ou fórmula de Haversine
- **Conversão automática** de resultados otimizados de clusters para setores censitários
- **Processamento de múltiplos municípios** (Lagoa Santa, Divinópolis, Montes Claros, Contagem, Belo Horizonte)

### Dados Gerados
- Matrizes de distância entre unidades de saúde
- Dados populacionais e de vulnerabilidade (IVS)
- Configurações de equipes de saúde
- Parâmetros de custo e orçamento
- Restrições de capacidade e cobertura

## 📦 Pré-requisitos

```bash
pip install pandas openpyxl geopandas shapely requests openrouteservice
```

### API OpenRouteService (opcional)
Para cálculos precisos de distância:
1. Cadastre-se em [OpenRouteService](https://openrouteservice.org/dev/#/signup)
2. Obtenha uma chave API gratuita
3. Configure a chave no arquivo `distance_API_calculator.py`

## 🔧 Configuração

### 1. Preparação dos Dados

Coloque os seguintes arquivos no diretório `Dados/`:

| Arquivo | Descrição |
|---------|-----------|
| `dados_censo_FINAL_reduzido.csv` | Dados do censo por setor |
| `dados_IVS.xlsx` | Índice de Vulnerabilidade Social |
| `v02_Equipe.xlsx` | Dados de equipes de saúde |
| `setores_com_ubs.xlsx` | Setores com UBS |
| `Porte_UBS.xlsx` | Porte das unidades |
| `sector_cluster_by_uf.csv` | Mapeamento setor→cluster |
| `Dados_custos_finais_formatados.xlsx` | Dados de custos |
| `dados_SC_fonte_completa.xlsx` | Coordenadas dos setores |
| `v01_UBS.xlsx` | Dados das UBS |

### 2. Configuração do Cenário

Edite `main.py` para configurar o município e parâmetros:

```python
MUNICIPIO = "Lagoa Santa"  # Município a ser processado
tipo_dos_dados = ExecutionDataType.BY_SETOR_CENSITARIO  # ou BY_CLUSTER

configs = ConfigurationDataScenario(
    municipio=MUNICIPIO,
    raios_criticos={"PHC": 5000, "SHC": 30000, "THC": 35000},
    maximo_de_unidades_abertas={"1": 10, "2": 1, "3": 1},
    equipes_saude_primario={"eSF", "eSB", "eMulti", "ACS"},
    equipes_saude_secundario={"EQ2"},
    equipes_saude_terciario={"EQ3"},
    encaminhamentos_primeiro_nivel={"1": 0.71, "2": 0.20, "3": 0.05},
    encaminhamentos_segundo_nivel={"1": 0.65, "2": 0.20, "3": 0.10},
    encaminhamentos_terceiro_nivel={"1": 0.8, "2": 0.1, "3": 0.05},
    maximo_atendimentos_telemedicina={"MAX_TELE_PHC": 0.05, "MAX_TELE_SHC": 0.05, "MAX_TELE_THC": 0.05},
    maximo_deslocamento={"MAX_HOME_PHC": 1, "MAX_HOME_SHC": 0.15, "MAX_HOME_THC": 0.05},
    name_output_file="Lagoa Santa",
    name_output_file_distancias="Lagoa Santa",
    tipo_rodada=tipo_dos_dados
)
```

## 🖥️ Uso

### Geração Básica de Dados

```bash
python main.py
```

### Exemplo de Uso Programático

```python
from create_dat_files import CreatorDatFiles
from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType

# Configurar cenário
config = ConfigurationDataScenario(
    municipio="Lagoa Santa",
    raios_criticos={"PHC": 5000, "SHC": 30000, "THC": 35000},
    maximo_de_unidades_abertas={"1": 10, "2": 1, "3": 1},
    equipes_saude_primario={"eSF", "eSB", "eMulti", "ACS"},
    equipes_saude_secundario={"EQ2"},
    equipes_saude_terciario={"EQ3"},
    encaminhamentos_primeiro_nivel={"1": 0.71, "2": 0.20, "3": 0.05},
    encaminhamentos_segundo_nivel={"1": 0.65, "2": 0.20, "3": 0.10},
    encaminhamentos_terceiro_nivel={"1": 0.8, "2": 0.1, "3": 0.05},
    maximo_atendimentos_telemedicina={"MAX_TELE_PHC": 0.05, "MAX_TELE_SHC": 0.05, "MAX_TELE_THC": 0.05},
    maximo_deslocamento={"MAX_HOME_PHC": 1, "MAX_HOME_SHC": 0.15, "MAX_HOME_THC": 0.05},
    name_output_file="Lagoa Santa",
    name_output_file_distancias="Lagoa Santa",
    tipo_rodada=ExecutionDataType.BY_SETOR_CENSITARIO
)

# Configurar caminhos
paths = PathArquivoDados(
    path_arquivo_setores_censitarios="Dados/dados_censo_FINAL_reduzido.csv",
    path_dados_IVS="Dados/dados_IVS.xlsx",
    path_equipes_PHC="Dados/v02_Equipe.xlsx",
    path_setores_com_UBS="Dados/setores_com_ubs.xlsx",
    path_porte_UBS="Dados/Porte_UBS.xlsx",
    path_cluster_CSV="Dados/sector_cluster_by_uf.csv",
    path_locais_candidatos="Dados/selecao_candidatos_final_Lagoa Santa.xlsx",
    path_dados_custo="Dados/Dados_custos_finais_formatados.xlsx",
    path_dados_poligonos_setor_censitario="Dados/dados_SC_fonte_completa.xlsx",
    path_dados_UBS="Dados/v01_UBS.xlsx",
    path_arquivos_dat_final="Dados/Lagoa Santa/"
)

# Criar arquivos
creator = CreatorDatFiles(
    configuration_data=config,
    path_arquivos_data=paths,
    create_distance_file=True
)
creator.create_file()
```

### Conversão de Resultados (Cluster → Setor Censitário)

```python
from step_convert_Cluster_in_SC import ConvertClusterResults

converter = ConvertClusterResults(
    configuration_data=config,
    path_arquivos_data=paths
)
converter.convert_results()
```

## 📊 Formato de Saída

### Arquivo Principal (.dat)
```ampl
#############################################################################
# Project CNPq: Increasing PHC with team sizing
# Author: João Flávio de Freitas Almeida
# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas
# Departamento de Engenharia de Produção
# Universidade Federal de Minas Gerais - Escola de Engenharia
#############################################################################
# Health Care Facility Location Problem: Considering fixed facilities,
# choose intermediate facilities according a criteria that improve service
# quality. Consider health care teams.
#############################################################################
# glpsol -m aps.mod -d LS.dat --cuts

#############################################################################
# DADOS REFERENTES AO MUNICIPIO DE: 
# Lagoa Santa 
#############################################################################
data;

param BUDGET := 1000000.00; # Overall budget constraint ($/year)
param I_L1 := 50000.00;
param I_L1_exp := 200000.00;

param: K: Dmax :=
1 5000  # PHC: Primary health care (basic care)
2 30000 # SHC: Secondary health care (intermediate care)
3 35000 # THC: Tertiary health care (hospital care)
;

set L[2] := SHC1;
set L[3] := THC1;

# Team cost K1 ($/year)
# Folha mensal Encargos Insumos Transporte Supervisão
# eSF R$ 1.455.500.00 50000 45000 7500 3500 5000
# eSB R$ 640.420.00 22000 19800 3300 1540 2200
# eMulti (1/9) R$ 611.595.56 92000 82800 13800 6440 9200
# Fonte: Planilha APS_dados.xlsx
param CE1:=
eSF 1455500
eSB 640420
eMulti 611596
ACS 120000
;

# of type p at demand point i and 
# vulnerability V (the higher vulnerability, the worse)
# id_setor populacao IVS
param: I: W IVS:= 
1 1500 0.35
2 2300 0.42
# ...
;

param: O1_0 O1_2 O1_3:=
1 0.71 0.20 0.05
2 0.71 0.20 0.05
# ...
;

param: ITEM1 SIZE FC1 VC1:=
1 1 1 80000 .
2 2 2 80000 .
# ...
;

param D0_2:=
1 SHC1 20000
2 SHC1 20000
# ...
;

param D0_3:=
1 THC1 35000
2 THC1 35000
# ...
;

param D1_2:=
123456 SHC1 20000
234567 SHC1 20000
# ...
;

param D1_3:=
123456 THC1 25000
234567 THC1 25000
# ...
;

param D2_3:=
SHC1 THC1 20000;
;

param C3:=
THC1 4000000
;

param U:=
1 10
2 1
3 1
;

param: O2_0 O2_1 O2_3 :=
SHC1 0.65 0.20 0.10
;

param: O3_0 O3_1 O3_2 :=
THC1 0.8 0.1 0.05
;

param MAX_TELE_PHC := 0.05;
param MAX_TELE_SHC := 0.05;
param MAX_TELE_THC := 0.05;

param MAX_HOME_PHC := 1;
param MAX_HOME_SHC := 0.15;
param MAX_HOME_THC := 0.05;

param: ITEM2 FC2 VC2:=
SHC1 1 200000 10
;

param: ITEM3 FC3 VC3:=
THC1 1 300000 20
;

param CNES1(tr): eSF eSB eMulti ACS:=
123456 2 1 0 5
234567 1 0 1 3
# ...
;

set EL[1] := 
123456
234567
# ...
;

end;
```

### Arquivo de Distâncias (.dat)
```ampl
#############################################################################
# Project CNPq: Increasing PHC with team sizing
# Author: João Flávio de Freitas Almeida
# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas
# Departamento de Engenharia de Produção
# Universidade Federal de Minas Gerais - Escola de Engenharia
#############################################################################
# DADOS REFERENTES AO MUNICIPIO DE: 
# Lagoa Santa 
#############################################################################
data;

# Distance matrix between same-level facilities (for team transfer) 
# {EL[1], L[1]} default 0; # Distance between L1 facilities (min) 
param DL1 := 
123456 234567 5000
123456 345678 7500
# ...
;

param D0_1 := 
1 123456 1250.5
1 234567 2300.8
2 123456 3100.2
# ...
;

end;
```

## 🔄 Fluxo de Trabalho Típico

1. **Preparação**: Organizar dados de entrada no diretório `Dados/`
2. **Configuração**: Definir parâmetros do cenário em `main.py`
3. **Geração**: Executar `main.py` para criar arquivos `.dat`
4. **Otimização**: Usar arquivos gerados com AMPL/GLPK:
   ```bash
   glpsol -m aps.mod -d Lagoa_Santa.dat --cuts
   ```
5. **Conversão** (se usar clusters): Converter resultados para setores censitários

## 🧪 Modelos Suportados

A ferramenta gera dados para modelos que incluem:

- **Localização de instalações** com níveis hierárquicos (PHC, SHC, THC)
- **Alocação de equipes** multidisciplinares (eSF, eSB, eMulti, ACS)
- **Fluxo de pacientes** entre níveis de atenção
- **Telemedicina** e atendimento domiciliar
- **Balanceamento** de carga entre unidades
- **Transferência de equipes** entre unidades do mesmo nível
- **Abertura de novas unidades** com restrições orçamentárias

## ⚠️ Observações Importantes

- **API de Distâncias**: O uso da API OpenRouteService tem limites (25 locais por requisição no plano gratuito)
- **Fallback Haversine**: Quando a API falha, o sistema usa automaticamente a fórmula de Haversine para calcular distâncias
- **Codificação**: Arquivos gerados usam codificação UTF-8
- **Dados Faltantes**: Valores ausentes são representados como "." nos arquivos .dat
- **Coordenadas**: As coordenadas geográficas devem estar no formato EPSG:4326 (WGS84)
- **Memória**: Para municípios grandes, o processamento de distâncias pode consumir bastante memória

## 🐛 Solução de Problemas

| Erro | Causa Provável | Solução |
|------|---------------|---------|
| "Código do município não encontrado" | Município não cadastrado no dicionário `code_mun` | Adicionar código IBGE do município em `code_mun` |
| "API Error 400" | Limite de requisições excedido ou coordenadas inválidas | Aumentar `delay_between_batches` ou verificar coordenadas |
| Arquivos de dados não encontrados | Caminhos incorretos ou arquivos ausentes | Verificar estrutura de diretórios e nomes dos arquivos |
| Erro de coordenadas | Formato inválido no JSON de polígonos | Verificar arquivo de polígonos dos setores censitários |
| "FileNotFoundError" | Arquivo de entrada não encontrado | Conferir se todos os arquivos listados na configuração existem |
| Erro de merge de dados | Colunas com nomes diferentes entre arquivos | Padronizar nomes de colunas nos arquivos de entrada |


## 👥 Autores

- **Otávio Martins Vasconcelos** 
- **João Flávio de Freitas Almeida** 
- LEPOINT - Laboratório de Estudos em Planejamento de Operações Integradas
- Departamento de Engenharia de Produção
- Universidade Federal de Minas Gerais - Escola de Engenharia

## 📄 Licença

Este projeto é parte de uma pesquisa acadêmica do CNPq. Consulte os autores para uso e distribuição.

## 🙏 Agradecimentos

- CNPq pelo financiamento da pesquisa
- OpenRouteService pela API de distâncias
- Comunidade GLPK

---
```

