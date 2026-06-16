#dados que preciso melhorar:

#C:\GeradorDadosAPS\GeraDadosAPS\Dados\Dados_todos_municipios\census_2000_2010_2022_normalized_indices.csv
#C:\GeradorDadosAPS\GeraDadosAPS\Dados\Dados_todos_municipios\dados_setores_censitarios.xlsx
#setores_com_ubs
#sector_cluster_by_uf
#Estou usando algum dado local ?
# r"C:\aps\GeraDadosAPS\Dados\Dados_todos_municipios\dados_SC_fonte_completa.xlsx"
#NAO


# %%
import pandas as pd
pd.set_option('display.max_columns', None)
# %%

# path_n = r"C:\GeradorDadosAPS\GeraDadosAPS\Dados\Dados_todos_municipios\census_2000_2010_2022_normalized_indices.csv"
path_n = r"Dados\census_2000_2010_2022_normalized_indices.csv"
df = pd.read_csv(path_n)
# %%
DICT_CODE = {"Lagoa Santa": 313760, 
"Divinopolis": 312230, 
"Montes Claros": 314330,
 "Belo Horizonte": 310620, 
 "Contagem": 311860}

mun_list = [313760,312230,314330,310620,311860]
df_export = df[((df.ANO_CENSO == 2022) & (df.CD_MUN_RED.isin(mun_list)))]
df_export.groupby(by=["CD_MUN_RED"]).agg({"CD_MUN_RED": "count"})
# %%
df_export.to_csv("dados_censo_FINAL_reduzido.csv")
# %%
