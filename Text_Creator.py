import pandas as pd

#TODO: Isso deveria ser uma classe abstrata. Pedir IA PARA REFATORAR e testar depois!
class text_messages_creator():
    def __init__(self, scenario_data):
        self.scenario_data_config = scenario_data["configurations"]
        self.scenario_dfs = scenario_data["dfs"]
        self.create_distance_data = scenario_data["create_distance_data"]
        self.texts_variables = list()
        self.texts_variables_arch_2 = list()
        self.dot_vig = ";\n\n"
        self.dict_dist_PHC_SC = scenario_data.get("dist_PHC_SC")
        self.dict_dist_SC_SC = scenario_data.get("dist_SC_SC")

    
    def create_header_texts(self):
        """
        Método que abre ou cria o arquivo que será escrito.
        
        """
        header_text = (
                    "#############################################################################\n"
                    "# Project CNPq: Increasing PHC with team sizing\n"
                    "# Author: João Flávio de Freitas Almeida <joao.flavio@dep.ufmg.br>\n"
                    "# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas\n"
                    "# Departamento de Engenharia de Produção\n"
                    "# Universidade Federal de Minas Gerais - Escola de Engenharia\n"
                    "#############################################################################\n"
                    "# Health Care Facility Location Problem: Considering fixed facilities,\n"
                    "# choose intermediate facilities according a criteria that improve service\n"
                    "# quality. Consider health care teams.\n"
                    "#############################################################################\n"
                    "# glpsol -m aps.mod -d LS.dat --cuts\n\n"
                )
        second_text = (
        "#############################################################################\n"
        "# DADOS REFERENTES AO MUNICIPIO DE: \n"
        f"# {self.scenario_data_config.municipio} \n"
        "#############################################################################\n"
            )

        data_text = "data;\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(second_text)
        self.texts_variables.append(data_text)

    def create_budgtes_text(self):

        bugdet_value = float(round(self.df_custos_e_orcamento.bugdet.iloc[0], 2))
        I_L1 = float(round(self.df_custos_e_orcamento.Abertura_Unidades.iloc[0], 2))
        I_L1_exp = float(round(self.df_custos_e_orcamento.Expansao_Unidades.iloc[0], 2))
        bugets_data_text = f"param BUDGET := {bugdet_value}; # Overall budget constraint ($/year)\n"
        i_l1_text = f"param I_L1 := {I_L1};\n"
        i_li_exp_text = f"param I_L1_exp := {I_L1_exp};\n"
        self.texts_variables.append(bugets_data_text)
        self.texts_variables.append(i_l1_text)
        self.texts_variables.append(i_li_exp_text)

    def create_critical_rad_text(self):
        header_critical_rad = "param: K: Dmax :=\n"
        phc_critical_rad = f"1         {self.scenario_data_config.raios_criticos["PHC"]} # PHC: Primary health care (basic care)\n"
        shc_critical_rad = f"2         {self.scenario_data_config.raios_criticos["SHC"]} # SHC: Secondary health care (intermediate care)\n"
        thc_critical_rad = f"3         {self.scenario_data_config.raios_criticos["THC"]} # THC: Tertiary health care (hospital care)\n"
        critical_rad_dot = ";\n"

        self.texts_variables.append(header_critical_rad)
        self.texts_variables.append(phc_critical_rad)
        self.texts_variables.append(shc_critical_rad)
        self.texts_variables.append(thc_critical_rad)
        self.texts_variables.append(critical_rad_dot)

    def create_basic_heal_care_unit_teams_SHC_THC_text(self): 
        #TODO: Isso pode ficar hardcoded ?
        #TODO: Porque na tenho o L[1] ?

        set_l1_level = "set L[1] := PHC1;\n"
        set_l2_level = "set L[2] := SHC1;\n"
        set_l3_level = "set L[3] := THC1;\n"

        #self.texts_variables.append(set_l1_level)
        self.texts_variables.append(set_l2_level)
        self.texts_variables.append(set_l3_level)

    # def create_basic_heal_care_unit_teams_PHC_text(self):
    #     description_text = "# Basic health care units teams (PHC)\n"
    #     header_text = "set E[1] :=\n"
    #     self.texts_variables.append(description_text)
    #     self.texts_variables.append(header_text)
    #     for eq in self.scenario_data_config.equipes_saude_primario:
    #         text_aux = f"{eq}\n"
    #         self.texts_variables.append(text_aux)
        
        
    #     self.texts_variables.append(self.dot_vig)

    def create_basic_heal_care_unit_teams_SHC_text(self):
        description_text = "# Intermediate health care units teams (SHC)\n"
        header_text = "set E[2] :=\n"
        self.texts_variables.append(description_text)
        self.texts_variables.append(header_text)
        for eq in self.scenario_data_config.equipes_saude_secundario:
            text_aux = f"{eq}\n"
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_basic_heal_care_unit_teams_THC_text(self):
        header_text = "set E[3] :=\n"
        self.texts_variables.append(header_text)
        for eq in self.scenario_data_config.equipes_saude_terciario:
            text_aux = f"{eq}\n"
            self.texts_variables.append(text_aux)


        self.texts_variables.append(self.dot_vig)

    # def create_existing_health_care_units_FIRST_level(self):
    #     header_text = "set EL[1] := \n"
    #     self.texts_variables.append(header_text)
    #     df_base = self.scenario_dfs[self.scenario_dfs.CO_UNIDADE_UBS > 0].copy()
    #     for _, row in df_base.iterrows():
    #         text_aux = f"{row.SETOR}\n"
    #         self.texts_variables.append(text_aux)

    #     self.texts_variables.append(self.dot_vig)
    
    def create_existing_health_care_units_SECOND_level(self):
        header_text = "set EL[2] := SHC1;\n"
        self.texts_variables.append(header_text)
    
    def create_existing_health_care_units_THIRD_level(self):
        header_text = "set EL[3] := THC1;\n"
        self.texts_variables.append(header_text)

    def create_costs_SHC_teams_text(self):
        text_doc = (
            "# Team cost K2 ($/year)\n"
        )

        header_text = "param CE2:=\n"
        self.texts_variables.append(text_doc)
        self.texts_variables.append(header_text)
        for eq,vl in self.scenario_data_config.custos_mensais_SHC.items():
            text_aux = " ".join([
                        str(eq),
                        str(vl),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        self.texts_variables.append(self.dot_vig)

    def create_costs_THC_teams_text(self):
        text_doc = (
            "# Team cost K3 ($/year)\n"
        )

        header_text = "param CE3:=\n"
        self.texts_variables.append(text_doc)
        self.texts_variables.append(header_text)
        for eq,vl in self.scenario_data_config.custos_mensais_THC.items():
            text_aux = " ".join([
                        str(eq),
                        str(vl),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)
    
    def create_SHC_teams_text(self):
        header_text = "param CNES2: SHC1:=\n"
        text = "EQ2	10\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(text)
        self.texts_variables.append(self.dot_vig)

    def create_THC_teams_text(self):
        header_text = "param CNES3: THC1:=\n"
        text = "EQ3	10\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(text)
        self.texts_variables.append(self.dot_vig)

    def create_param_C2_text(self):
        header_text = "param C2:=\n"
        text = "SHC1	4000000\n" #TODO: Aumentando para nao dar infeasible no modelo. Valor original 40000
        self.texts_variables.append(header_text)
        self.texts_variables.append(text)
        self.texts_variables.append(self.dot_vig)
        
    def create_param_C3_text(self):
        header_text = "param C3:=\n"
        text = "THC1	4000000\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(text)
        self.texts_variables.append(self.dot_vig)

    def create_units_to_open_text(self):
        header_text = "param U:=\n"
        self.texts_variables.append(header_text)

        for lvl, qntd in self.scenario_data_config.maximo_de_unidades_abertas.items():
            text_aux = " ".join([
                        str(lvl),
                        str(qntd),
                        str("\n") 
                    ])
            self.texts_variables.append(text_aux)
            #print(text_aux)
        self.texts_variables.append(self.dot_vig)


    def create_proportion_patients_encm_SHC_text(self):
        header_text = "param:	O2_0   O2_1   O2_3 :=\n"
        self.texts_variables.append(header_text)
        text_aux = " ".join([
                        str("SHC1"),
                        str(self.scenario_data_config.encaminhamentos_segundo_nivel["1"]), #TODO: Isso aqui ta bem estranho!
                        str(self.scenario_data_config.encaminhamentos_segundo_nivel["2"]),
                        str(self.scenario_data_config.encaminhamentos_segundo_nivel["3"]),
                        str("\n")
                    ])
        self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    def create_proportion_patients_encm_THC_text(self):
        header_text = "param:	O3_0   O3_1   O3_2 :=\n"
        self.texts_variables.append(header_text)
        text_aux = " ".join([
                        str("THC1"),
                        str(self.scenario_data_config.encaminhamentos_terceiro_nivel["1"]), #TODO: Isso aqui ta bem estranho!
                        str(self.scenario_data_config.encaminhamentos_terceiro_nivel["2"]),
                        str(self.scenario_data_config.encaminhamentos_terceiro_nivel["3"]),
                        str("\n")
                    ])
        self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    def create_percentual_max_teleatend_text(self):
        header_text = f"param MAX_TELE_PHC := {self.scenario_data_config.maximo_atendimentos_telemedicina['MAX_TELE_PHC']};\n"
        self.texts_variables.append(header_text)

        header_text = f"param MAX_TELE_SHC := {self.scenario_data_config.maximo_atendimentos_telemedicina['MAX_TELE_SHC']};\n"
        self.texts_variables.append(header_text)

        header_text = f"param MAX_TELE_THC := {self.scenario_data_config.maximo_atendimentos_telemedicina['MAX_TELE_THC']};\n"
        self.texts_variables.append(header_text)

    def create_percentual_max_deslocamento_text(self):
        header_text = f"param MAX_HOME_PHC := {self.scenario_data_config.maximo_deslocamento['MAX_HOME_PHC']};\n"
        self.texts_variables.append(header_text)

        header_text = f"param MAX_HOME_SHC := {self.scenario_data_config.maximo_deslocamento['MAX_HOME_SHC']};\n"
        self.texts_variables.append(header_text)

        header_text = f"param MAX_HOME_THC := {self.scenario_data_config.maximo_deslocamento['MAX_HOME_THC']};\n\n"
        self.texts_variables.append(header_text)

    def create_variable_costs_SHC_text(self): 
        header_text = "param:	ITEM2   FC2		VC2:=\n"
        data_text = "SHC1	1       200000		10\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(data_text)
        self.texts_variables.append(self.dot_vig)

    def create_variable_costs_THC_text(self):
        header_text = "param:	ITEM3   FC3		VC3:=\n"
        data_text = "THC1	1       300000		20\n"
        self.texts_variables.append(header_text)
        self.texts_variables.append(data_text)
        self.texts_variables.append(self.dot_vig)


    def create_mutable_texts(self):
        
        self.create_header_texts() #CLASSE PAI
        self.create_budgtes_text() #CLASSE PAI
        self.create_critical_rad_text() #CLASSE PAI

        self.create_basic_heal_care_unit_teams_SHC_THC_text() #CLASSE PAI
        self.create_basic_heal_care_unit_teams_PHC_text() #REVISAR e Refazer! classes filhas! - VAMOS TER SO 3 EQUIPES ?
        self.create_basic_heal_care_unit_teams_SHC_text() #CLASSE PAI
        self.create_basic_heal_care_unit_teams_THC_text() #CLASSE PAI
        self.create_existing_health_care_units_FIRST_level() #CLASSE FILHA!
        self.create_existing_health_care_units_SECOND_level() #CLASSE PAI 
        self.create_existing_health_care_units_THIRD_level() #CLASSE PAI 
        self.create_vulnerability_population_table_text()  #CLASSE FILHA!
        self.create_variable_costs_PHC_text()  #CLASSE FILHA!
        self.create_variable_costs_SHC_text()  #CLASSE PAI 
        self.create_variable_costs_THC_text()  #CLASSE PAI 


        self.create_costs_PHC_teams_text() #REVISAR e Refazer! classes filhas! - VAMOS TER SO 3 EQUIPES ?
        self.create_costs_SHC_teams_text() #CLASSE PAI
        self.create_costs_THC_teams_text() #CLASSE PAI
        
        #Setor censitario - Pontos
        self.create_distance_between_SC_PHC_text() #CLASSE FILHA!
        self.create_distance_between_SC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_SC_THC_text() #CLASSE FILHA!

        # #Nivel primario para secundario e terciario
        self.create_distance_between_PHC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_PHC_THC_text() #CLASSE FILHA!

        # #Secundario para terciario
        self.create_distance_between_SHC_THC_text() #CLASSE PAI



        self.create_PHC_teams_text() #CLASSE FILHA!
        self.create_SHC_teams_text() #CLASSE PAI
        self.create_THC_teams_text() #CLASSE PAI

        # #TODO: Nao sei o que é isso!
        self.create_param_C2_text() #CLASSE PAI!
        self.create_param_C3_text() #CLASSE PAI! 

        self.create_units_to_open_text()  #CLASSE PAI!


        self.create_proportion_patients_encm_PHC_text()  #CLASSE FILHA!
        self.create_proportion_patients_encm_SHC_text()  #CLASSE PAI!
        self.create_proportion_patients_encm_THC_text()  #CLASSE PAI! 

        self.create_percentual_max_teleatend_text()    #CLASSE PAI!
        self.create_percentual_max_deslocamento_text()  #CLASSE PAI!

    def create_header_text_arch_dist(self):
        header_text = (
                    "#############################################################################\n"
                    "# Project CNPq: Increasing PHC with team sizing\n"
                    "# Author: João Flávio de Freitas Almeida <joao.flavio@dep.ufmg.br>\n"
                    "# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas\n"
                    "# Departamento de Engenharia de Produção\n"
                    "# Universidade Federal de Minas Gerais - Escola de Engenharia\n"
                    "#############################################################################\n"
                    "# Health Care Facility Location Problem: Considering fixed facilities,\n"
                    "# choose intermediate facilities according a criteria that improve service\n"
                    "# quality. Consider health care teams.\n"
                    "#############################################################################\n"
                    "# glpsol -m aps.mod -d LS.dat --cuts\n\n"
                )
        second_text = (
        "#############################################################################\n"
        "# DADOS REFERENTES AO MUNICIPIO DE: \n"
        f"# {self.scenario_data_config.municipio} \n"
        "#############################################################################\n"
            )

        data_text = "data;\n"
        self.texts_variables_arch_2.append(header_text)
        self.texts_variables_arch_2.append(second_text)
        self.texts_variables_arch_2.append(data_text)
    
    def create_SC_set_text(self):
        header_text = "set L[1] := \n"
        self.texts_variables_arch_2.append(header_text)
        for _, row in self.scenario_dfs.iterrows():
            text_aux = " ".join([
                        str(row.SETOR),
                        str("\n") 
                    ])
            self.texts_variables_arch_2.append(text_aux)
        
        self.texts_variables_arch_2.append(self.dot_vig)

    def create_distance_between_SHC_THC_text(self):
        header_text = "param D2_3:=\n"
        self.texts_variables.append(header_text)
        text = "SHC1	THC1	20000;\n\n"
        self.texts_variables.append(text)


    def create_costs_PHC_teams_text(self):
        text_doc = (
            "# Team cost K1 ($/year)\n"
            "# 		Folha mensal	Encargos	Insumos	Transporte	Supervisão\n"
            "# eSF	 R$ 1.455.500.00 	50000	45000	7500	3500	5000\n"
            "# eSB	 R$ 640.420.00 	22000	19800	3300	1540	2200\n"
            "# eMulti (1/9)	 R$ 611.595.56 	92000	82800	13800	6440	9200\n"
            "# Fonte: Planilha APS_dados.xlsx\n"
        )

        header_text = "param CE1:=\n"
        self.texts_variables.append(text_doc)
        self.texts_variables.append(header_text)
        text_esf = " ".join([
                        str("eSF"),
                        str(int(round(self.df_custos_e_orcamento.Custo_eSF.iloc[0], 2))),
                        str("\n")
                    ])
    
        text_esb = " ".join([
                        str("eSB"),
                        str(int(round(self.df_custos_e_orcamento.Custo_eSB.iloc[0], 2))),
                        str("\n")
                    ])

        text_eMulti = " ".join([
                        str("eMulti"),
                        str(int(round(self.df_custos_e_orcamento.Custo_eMulti.iloc[0], 2))),
                        str("\n")
                    ])

        text_acs = " ".join([
                        str("ACS"),
                        str(int(round(self.df_custos_e_orcamento.Custo_ACS.iloc[0], 2))),
                        str("\n")
                    ])

        self.texts_variables.append(text_esf)
        self.texts_variables.append(text_esb)
        self.texts_variables.append(text_eMulti)
        self.texts_variables.append(text_acs)

        self.texts_variables.append(self.dot_vig)
    # def create_PHC_SC_text(self):
    #     text_comment = (
    #         "# Distance matrix between same-level facilities (for team transfer) \n"
    #         "# {EL[1], L[1]} default 0; # Distance between L1 facilities (min)  \n"
    #     )
    #     header_text = "param DL1 := \n"

    #     self.texts_variables_arch_2.append(text_comment)
    #     self.texts_variables_arch_2.append(header_text)
    #     for dk in self.dict_dist_PHC_SC:
    #         text_aux = " ".join([
    #                     str(dk["origem"]),
    #                     str(dk["destino"]),
    #                     str(dk["distancia"]),
    #                     str("\n") 
    #                 ])

    #         self.texts_variables_arch_2.append(text_aux)


    #     self.texts_variables_arch_2.append(self.dot_vig)

    def create_SC_SC_text(self):
        header_text = "param D0_1 := \n"

        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_SC_SC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)

    # def create_distances_text(self):
    #     self.create_header_text_arch_dist()
    #     self.create_SC_set_text()
    #     self.create_PHC_SC_text()
    #     self.create_SC_SC_text()
    
    # def create_texts(self):
    #     self.create_mutable_texts()
    #     if self.create_distance_data:
    #         self.create_distances_text()


    def create_basic_heal_care_unit_teams_PHC_text(self):
        description_text = "# Basic health care units teams (PHC)\n"
        header_text = "set E[1] :=\n"
        self.texts_variables.append(description_text)
        self.texts_variables.append(header_text)
        for eq in self.scenario_data_config.equipes_saude_primario:
            text_aux = f"{eq}\n"
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)
    
    #     return self.texts_variables, self.texts_variables_arch_2

    def create_Candidate_locations_text(self):
        header_text = "set CL[1] :=\n"
        self.texts_variables.append(header_text)
        df = self.df_candidates_PHC.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE_UBS).rstrip('.0'),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    def create_SHC_THC_empty_candidate_location(self):
        set_l1_level = "set L[1] := PHC1;\n"
        set_l2_level = "set CL[2] := ;\n"
        set_l3_level = "set CL[3] := ;\n"

        #self.texts_variables.append(set_l1_level)
        self.texts_variables.append(set_l2_level)
        self.texts_variables.append(set_l3_level)

    def create_SC_PHC_text(self):
        header_text = "param D0_1 := \n"

        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_SC_PHC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)

    def create_Exist_PHC_to_all_PHC_text(self):
        text_comment = (
            "# Distance matrix between same-level facilities (for team transfer) \n"
            "# {EL[1], L[1]} default 0; # Distance between L1 facilities (min)  \n"
        )
        header_text = "param DL1 := \n"

        self.texts_variables_arch_2.append(text_comment)
        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_exist_PHC_all_PHC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)


class text_messages_creator_By_SC(text_messages_creator):
    def __init__(self, scenario_data):
        self.scenario_data_config = scenario_data["configurations"]
        self.scenario_dfs = scenario_data["dfs"]
        self.create_distance_data = scenario_data["create_distance_data"]
        self.texts_variables = list()
        self.texts_variables_arch_2 = list()
        self.dot_vig = ";\n\n"
        self.dict_dist_PHC_SC = scenario_data.get("dist_PHC_SC")
        self.dict_dist_SC_SC = scenario_data.get("dist_SC_SC")
        self.df_custos_e_orcamento = scenario_data['df_dados_custos_e_orcamento']
        self.define_EL_and_CL_dataframes()
        self.dict_dist_exist_PHC_all_PHC = scenario_data.get("dist_Exist_PHC_to_all_PHC")
        self.dict_dist_SC_PHC = scenario_data.get("dist_SC_PHC")

    def define_EL_and_CL_dataframes(self):
        # self.EL_mask =  [isinstance(i, float) and i > 0 for i in self.scenario_dfs.CO_UNIDADE_UBS]
        self.EL_mask = [i not in self.scenario_dfs.SETOR.to_list() and i > 0 for i in self.scenario_dfs.CO_UNIDADE_UBS]
        # self.CL_mask =  [isinstance(i, str) for i in self.scenario_dfs.CO_UNIDADE_UBS]        
        self.CL_mask = self.scenario_dfs.IS_CL.to_list()
        self.df_exist_PHC = self.scenario_dfs[self.EL_mask]
        self.df_candidates_PHC = self.scenario_dfs[self.CL_mask]
        # self.df_PHC_EL_plus_EC = self.scenario_dfs[self.EL_mask or self.CL_mask]
        self.df_PHC_EL_plus_EC = pd.concat([self.df_exist_PHC, self.df_candidates_PHC])
        b=0

    def create_SC_SC_text(self):
        header_text = "param D0_1 := \n"

        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_SC_SC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)

    def create_PHC_SC_text(self):
        text_comment = (
            "# Distance matrix between same-level facilities (for team transfer) \n"
            "# {EL[1], L[1]} default 0; # Distance between L1 facilities (min)  \n"
        )
        header_text = "param DL1 := \n"

        self.texts_variables_arch_2.append(text_comment)
        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_PHC_SC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]).rstrip('.0'),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)
    
    def create_vulnerability_population_table_text(self):
        doc_text = (
            "# of type p at demand point i and \n"
            "# vulnerability V (the higher vulnerability, the worse)\n"	
            "# id_setor	populacao	IVS\n"
        )
        header_text = "param: I:       W   IVS:=	\n"
        self.texts_variables.append(doc_text)
        self.texts_variables.append(header_text)

        for _, row in self.scenario_dfs.iterrows():
            text_aux = " ".join([
                        str(row.SETOR).rstrip('.0'),
                        str(row.V01006),
                        str(row["Indice"]),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_proportion_patients_encm_PHC_text(self):
        header_text = "param:	 O1_0    O1_2    O1_3:=\n"
        self.texts_variables.append(header_text)
        df = self.scenario_dfs.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                        str(row.SETOR).rstrip('.0'),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["1"]), #TODO: Isso aqui ta bem estranho!
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["2"]),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["3"]),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    def create_PHC_teams_text(self):
        header_text = "param CNES1(tr):	eSF	eSB	eMulti ACS:=\n"
        self.texts_variables.append(header_text)
        df = self.df_PHC_EL_plus_EC.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE).rstrip('.0'),
                str(int(row.get(70.0, 0))),  # eSF
                str(int(row.get(71.0, 0))),  # eSB
                str((row.get(72.0, 0))),  # eMulti
                str(int(row.get(74.0, 0))),  # ACS
                str("\n")
            ])
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    def create_distance_between_SC_PHC_text(self):
        #TODO: Vai para o arquivo 2
        pass

    def create_distance_between_SC_SHC_text(self):
        header_text = "param D0_2:=\n"
        self.texts_variables.append(header_text)

        for _, row in self.scenario_dfs.iterrows():
            text_aux = " ".join([
                        str(row.SETOR).rstrip('.0'),
                        "SHC1",
                        str(20000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_distance_between_SC_THC_text(self):
        header_text = "param D0_3:=\n"
        self.texts_variables.append(header_text)

        for _, row in self.scenario_dfs.iterrows():
            text_aux = " ".join([
                        str(row.SETOR).rstrip('.0'),
                        "THC1",
                        str(35000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)
    
    def create_distance_between_PHC_SHC_text(self):
        #Distancia entre todos os setores censitarios e as UBS ate a unidade secundaria!
        header_text = "param D1_2:=\n"
        self.texts_variables.append(header_text)

        # for _, row in self.scenario_dfs.iterrows():
        #     text_aux = " ".join([
        #                 str(row.SETOR),
        #                 "SHC1",
        #                 str(20000),
        #                 str("\n")
        #             ])
        #     self.texts_variables.append(text_aux)

        #TODO: Ainda acho que isso está errado!
        for _, row in self.df_PHC_EL_plus_EC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE_UBS).rstrip('.0'),
                        "SHC1",
                        str(20000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_distance_between_PHC_THC_text(self):
        #Distancia entre todos os setores censitarios e as UBS ate a unidade secundaria!
        header_text = "param D1_3:=\n"
        self.texts_variables.append(header_text)

        # for _, row in self.scenario_dfs.iterrows():
        #     text_aux = " ".join([
        #                 str(row.SETOR),
        #                 "THC1",
        #                 str(25000),
        #                 str("\n")
        #             ])
        #     self.texts_variables.append(text_aux)

        #TODO: Ainda acho que isso está errado!
        for _, row in self.df_PHC_EL_plus_EC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE_UBS).rstrip('.0'),
                        "THC1",
                        str(25000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    # def create_costs_PHC_teams_text(self):
    #     text_doc = (
    #         "# Team cost K1 ($/year)\n"
    #         "# 		Folha mensal	Encargos	Insumos	Transporte	Supervisão\n"
    #         "# eSF	 R$ 1.455.500.00 	50000	45000	7500	3500	5000\n"
    #         "# eSB	 R$ 640.420.00 	22000	19800	3300	1540	2200\n"
    #         "# eMulti (1/9)	 R$ 611.595.56 	92000	82800	13800	6440	9200\n"
    #         "# Fonte: Planilha APS_dados.xlsx\n"
    #     )

    #     header_text = "param CE1:=\n"
    #     self.texts_variables.append(text_doc)
    #     self.texts_variables.append(header_text)
    #     for eq,vl in self.scenario_data_config.custos_mensais_PHC.items():
    #         text_aux = " ".join([
    #                     str(eq),
    #                     str(vl),
    #                     str("\n")
    #                 ])
    #         self.texts_variables.append(text_aux)

    #     self.texts_variables.append(self.dot_vig)

    def create_variable_costs_PHC_text(self):
        #Dados ainda nao disponiveis, por isso usei o default 80000
        comentary_text = ("# # Variable cost of PHC j / patient\n")
        header_text = "param:	        ITEM1   SIZE0	FC1		VC1:=\n"
        self.texts_variables.append(comentary_text)
        self.texts_variables.append(header_text)
        df_base = self.scenario_dfs[self.scenario_dfs.CO_UNIDADE_UBS > 0].copy()
        value_item = 1
        #setores censitarios que tem PHC 
        for _, row in df_base.iterrows():
            text_aux = " ".join([
                str(row.SETOR).rstrip('.0'),
                str(value_item), #ITEM 1
                str(1), #SIZE
                str(80000), #FC1
                str("."), #VC1
                str("\n")
            ])
            self.texts_variables.append(text_aux)
            value_item += 1
        
        self.texts_variables.append(self.dot_vig)

    def create_existing_health_care_units_FIRST_level(self):
        header_text = "set EL[1] := \n"
        self.texts_variables.append(header_text)
        df_base = self.df_exist_PHC.copy()
        for _, row in df_base.iterrows():
            # text_aux = f"{row.SETOR}\n"
            text_aux = f"{str(row.CO_UNIDADE_UBS).rstrip('.0')}\n"
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_variable_costs_PHC_text(self):
        #Dados ainda nao disponiveis, por isso usei o default 80000
        comentary_text = ("# # Variable cost of PHC j / patient\n")
        header_text = "param:	        ITEM1   SIZE0	FC1		VC1:=\n"
        self.texts_variables.append(comentary_text)
        self.texts_variables.append(header_text)
        df_base = self.df_exist_PHC.copy()
        value_item = 1
        #setores censitarios que tem PHC #df_candidates_PHC
        for _, row in df_base.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE).rstrip('.0'),
                str(value_item), #ITEM 1
                str(row.get("PORTE_UBS", 1)).rstrip('.0'), #SIZE
                #str(int(10)),
                str(8), #FC1
                str("."), #VC1
                str("\n")
            ])
            self.texts_variables.append(text_aux)
            value_item += 1
        
        #Unidades candidatas nao tem capacidade nem tamanho definido!
        for _, row in self.df_candidates_PHC.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE_UBS),
                str(value_item), #ITEM 1
                str("."), #SIZE
                str("."), #FC1
                str("."), #VC1
                str("\n")
            ])
            self.texts_variables.append(text_aux)
            value_item += 1
        

        self.texts_variables.append(self.dot_vig)

    def create_mutable_texts_by_SC(self):
        self.create_header_texts() #CLASSE PAI
        self.create_budgtes_text() #CLASSE PAI
        self.create_critical_rad_text() #CLASSE PAI


        self.create_basic_heal_care_unit_teams_PHC_text()
        self.create_basic_heal_care_unit_teams_SHC_text() #CLASSE PAI
        self.create_basic_heal_care_unit_teams_THC_text() #CLASSE PAI
        
        
        self.create_existing_health_care_units_FIRST_level() # TODO: Esse preciso alterar!
        self.create_existing_health_care_units_SECOND_level() #CLASSE PAI 
        self.create_existing_health_care_units_THIRD_level() #CLASSE PAI 
        

        self.create_Candidate_locations_text()
        self.create_SHC_THC_empty_candidate_location()


        self.create_vulnerability_population_table_text()  #CLASSE FILHA!


        self.create_variable_costs_PHC_text()  
        self.create_variable_costs_SHC_text()  #CLASSE PAI 
        self.create_variable_costs_THC_text()  #CLASSE PAI 


        self.create_costs_PHC_teams_text() #
        self.create_costs_SHC_teams_text() #CLASSE PAI
        self.create_costs_THC_teams_text() #CLASSE PAI
        
        #Setor censitario - Pontos

        #ARRUMEI AQUI 
        self.create_distance_between_SC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_SC_THC_text() #CLASSE FILHA!

        # #Nivel primario para secundario e terciario
        self.create_distance_between_PHC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_PHC_THC_text() #CLASSE FILHA!

        # #Secundario para terciario
        self.create_distance_between_SHC_THC_text() #CLASSE PAI



        self.create_PHC_teams_text() #CLASSE FILHA! #NORMALIZAR!
        self.create_SHC_teams_text() #CLASSE PAI
        self.create_THC_teams_text() #CLASSE PAI

        # #TODO: Nao sei o que é isso!
        self.create_param_C2_text() #CLASSE PAI!
        self.create_param_C3_text() #CLASSE PAI! 

        self.create_units_to_open_text()  #CLASSE PAI!


        self.create_proportion_patients_encm_PHC_text()  #CLASSE FILHA!
        self.create_proportion_patients_encm_SHC_text()  #CLASSE PAI!
        self.create_proportion_patients_encm_THC_text()  #CLASSE PAI! 

        self.create_percentual_max_teleatend_text()    #CLASSE PAI!
        self.create_percentual_max_deslocamento_text()  

    def create_PHC_SC_text(self):
        text_comment = (
            "# Distance matrix between same-level facilities (for team transfer) \n"
            "# {EL[1], L[1]} default 0; # Distance between L1 facilities (min)  \n"
        )
        header_text = "param DL1 := \n"

        self.texts_variables_arch_2.append(text_comment)
        self.texts_variables_arch_2.append(header_text)
        for dk in self.dict_dist_PHC_SC:
            text_aux = " ".join([
                        str(dk["origem"]).rstrip('.0'),
                        str(dk["destino"]).rstrip('.0'),
                        str(dk["distancia"]).rstrip('.0'),
                        str("\n") 
                    ])

            self.texts_variables_arch_2.append(text_aux)


        self.texts_variables_arch_2.append(self.dot_vig)
    
    def create_distances_text_SC(self):
        self.create_header_text_arch_dist()
        #self.create_SC_set_text()
        # self.create_PHC_SC_text()
        # self.create_SC_SC_text()
        self.create_Exist_PHC_to_all_PHC_text()
        self.create_SC_PHC_text()
    
    def create_texts(self):
        self.create_mutable_texts_by_SC()
        if self.create_distance_data:
            self.create_distances_text_SC()
        return self.texts_variables, self.texts_variables_arch_2


class text_messages_creator_By_Cluster(text_messages_creator):
    def __init__(self, scenario_data):
        self.scenario_data_config = scenario_data["configurations"]
        self.scenario_df_demanda = scenario_data["df_demanda"]
        self.create_distance_data = scenario_data["create_distance_data"]
        self.texts_variables = list()
        self.texts_variables_arch_2 = list()
        self.dot_vig = ";\n\n"
        self.dict_dist_exist_PHC_all_PHC = scenario_data.get("dist_Exist_PHC_to_all_PHC")
        self.dict_dist_SC_PHC = scenario_data.get("dist_SC_PHC")
        self.df_PHC_exists_and_candidadtes = scenario_data['df_PHC_exists_and_candidadtes']
        self.df_exist_PHC = self.df_PHC_exists_and_candidadtes[
            ~self.df_PHC_exists_and_candidadtes["CO_UNIDADE"].apply(lambda x: isinstance(x, str))
            ]
        self.df_candidates_PHC = self.df_PHC_exists_and_candidadtes[
            self.df_PHC_exists_and_candidadtes["CO_UNIDADE"].apply(lambda x: isinstance(x, str))
            ]
        self.df_custos_e_orcamento = scenario_data['df_dados_custos_e_orcamento']


    def create_proportion_patients_encm_PHC_text(self):
        header_text = "param:	 O1_0    O1_2    O1_3:=\n"
        self.texts_variables.append(header_text)
        df = self.df_exist_PHC.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE).rstrip('.0'),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["1"]), #TODO: Isso aqui ta bem estranho!
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["2"]),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["3"]),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        
        
        for _, row in  self.df_candidates_PHC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE_UBS),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["1"]), #TODO: Isso aqui ta bem estranho!
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["2"]),
                        str(self.scenario_data_config.encaminhamentos_primeiro_nivel["3"]),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        

        self.texts_variables.append(self.dot_vig)

    def create_PHC_teams_text(self):
        header_text = "param CNES1(tr):	eSF	eSB	eMulti ACS:=\n"
        self.texts_variables.append(header_text)
        df = self.df_exist_PHC.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE),
                str(int(row.get(70.0, 0))),  # eSF
                str(int(row.get(71.0, 0))),  # eSB
                str((row.get(72.0, 0))),  # eMulti
                str(int(row.get(74.0, 0))),  # ACS
                str("\n")
            ])
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

    # def create_distance_between_SC_PHC_text(self):
    #     #TODO: Vai para o arquivo 2
    #     pass

    def create_distance_between_SC_SHC_text(self):
        header_text = "param D0_2:=\n"
        self.texts_variables.append(header_text)

        for _, row in self.scenario_df_demanda.iterrows():
            text_aux = " ".join([
                        str(row.cluster),
                        "SHC1",
                        str(20000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_distance_between_SC_THC_text(self):
        header_text = "param D0_3:=\n"
        self.texts_variables.append(header_text)

        for _, row in self.scenario_df_demanda.iterrows():
            text_aux = " ".join([
                        str(row.cluster),
                        "THC1",
                        str(25000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)
    
    def create_distance_between_PHC_SHC_text(self):
        #Distancia entre todos os setores censitarios e as UBS ate a unidade secundaria!
        header_text = "param D1_2:=\n"
        self.texts_variables.append(header_text)
        
        for _, row in self.df_exist_PHC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE),
                        "SHC1",
                        str(20000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        #TODO: Ainda acho que isso está errado!
        for _, row in self.df_candidates_PHC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE),
                        "SHC1",
                        str(20000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    def create_distance_between_PHC_THC_text(self):
        header_text = "param D1_3:=\n"
        self.texts_variables.append(header_text)

        for _, row in self.df_exist_PHC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE),
                        "THC1",
                        str(25000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        #TODO: Ainda acho que isso está errado!
        for _, row in self.df_candidates_PHC.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE),
                        "THC1",
                        str(25000),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    # def create_distance_between_SHC_THC_text(self):
    #     header_text = "param D2_3:=\n"
    #     self.texts_variables.append(header_text)
    #     text = "SHC1	THC1	20000;\n"
    #     self.texts_variables.append(text)

    # def create_costs_PHC_teams_text(self):
    #     text_doc = (
    #         "# Team cost K1 ($/year)\n"
    #         "# 		Folha mensal	Encargos	Insumos	Transporte	Supervisão\n"
    #         "# eSF	 R$ 1.455.500.00 	50000	45000	7500	3500	5000\n"
    #         "# eSB	 R$ 640.420.00 	22000	19800	3300	1540	2200\n"
    #         "# eMulti (1/9)	 R$ 611.595.56 	92000	82800	13800	6440	9200\n"
    #         "# Fonte: Planilha APS_dados.xlsx\n"
    #     )

    #     header_text = "param CE1:=\n"
    #     self.texts_variables.append(text_doc)
    #     self.texts_variables.append(header_text)
    #     text_esf = " ".join([
    #                     str("eSF"),
    #                     str(int(round(self.df_custos_e_orcamento.Custo_eSF.iloc[0], 2))),
    #                     str("\n")
    #                 ])
    
    #     text_esb = " ".join([
    #                     str("eSB"),
    #                     str(int(round(self.df_custos_e_orcamento.Custo_eSB.iloc[0], 2))),
    #                     str("\n")
    #                 ])

    #     text_eMulti = " ".join([
    #                     str("eMulti"),
    #                     str(int(round(self.df_custos_e_orcamento.Custo_eMulti.iloc[0], 2))),
    #                     str("\n")
    #                 ])

    #     text_acs = " ".join([
    #                     str("ACS"),
    #                     str(int(round(self.df_custos_e_orcamento.Custo_ACS.iloc[0], 2))),
    #                     str("\n")
    #                 ])

    #     self.texts_variables.append(text_esf)
    #     self.texts_variables.append(text_esb)
    #     self.texts_variables.append(text_eMulti)
    #     self.texts_variables.append(text_acs)

    #     self.texts_variables.append(self.dot_vig)

    def create_variable_costs_PHC_text(self):
        #Dados ainda nao disponiveis, por isso usei o default 80000
        comentary_text = ("# # Variable cost of PHC j / patient\n")
        header_text = "param:	        ITEM1   SIZE0	FC1		VC1:=\n"
        self.texts_variables.append(comentary_text)
        self.texts_variables.append(header_text)
        df_base = self.df_exist_PHC.copy()
        value_item = 1
        #setores censitarios que tem PHC #df_candidates_PHC
        for _, row in df_base.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE).rstrip('.0'),
                str(value_item), #ITEM 1
                str(int(row.get("PORTE_UBS", 1))), #SIZE
                #str(int(10)),
                str(8), #FC1
                str("."), #VC1
                str("\n")
            ])
            self.texts_variables.append(text_aux)
            value_item += 1
        
        #Unidades candidatas nao tem capacidade nem tamanho definido!
        for _, row in self.df_candidates_PHC.iterrows():
            text_aux = " ".join([
                str(row.CO_UNIDADE),
                str(value_item), #ITEM 1
                str("."), #SIZE
                str("."), #FC1
                str("."), #VC1
                str("\n")
            ])
            self.texts_variables.append(text_aux)
            value_item += 1
        

        self.texts_variables.append(self.dot_vig)
    
    def create_existing_health_care_units_FIRST_level(self):
        header_text = "set EL[1] := \n"
        self.texts_variables.append(header_text)
        df_base = self.df_exist_PHC
        for _, row in df_base.iterrows():
            # text_aux = f"{row.CO_UNIDADE}\n"
            text_aux = f"{str(row.CO_UNIDADE).rstrip('.0')}\n"
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)

    # def create_basic_heal_care_unit_teams_PHC_text(self):
    #     description_text = "# Basic health care units teams (PHC)\n"
    #     header_text = "set E[1] :=\n"
    #     self.texts_variables.append(description_text)
    #     self.texts_variables.append(header_text)
    #     for eq in self.scenario_data_config.equipes_saude_primario:
    #         text_aux = f"{eq}\n"
    #         self.texts_variables.append(text_aux)
        
        
    #     self.texts_variables.append(self.dot_vig)
    
    def create_vulnerability_population_table_text(self):
        doc_text = (
            "# of type p at demand point i and \n"
            "# vulnerability V (the higher vulnerability, the worse)\n"	
            "# id_setor	populacao	IVS\n"
        )
        header_text = "param: I:       W   IVS:=	\n"
        self.texts_variables.append(doc_text)
        self.texts_variables.append(header_text)

        for _, row in self.scenario_df_demanda.iterrows():
            text_aux = " ".join([
                        str(row.cluster),
                        str(int(row.V01006)),
                        str(row["Índice"]),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)

        self.texts_variables.append(self.dot_vig)
    
    def create_texts(self):
        self.create_mutable_texts_by_cluster()
        if self.create_distance_data:
            self.create_distances_text_by_cluster()
        return self.texts_variables, self.texts_variables_arch_2

    
    def create_EL_1_locations_text(self):
        header_text = "set EL[1] :=\n"
        self.texts_variables.append(header_text)
        df = self.df_exist_PHC.copy()
        for _, row in df.iterrows():
            text_aux = " ".join([
                        str(row.CO_UNIDADE),
                        str("\n")
                    ])
            self.texts_variables.append(text_aux)
        
        
        self.texts_variables.append(self.dot_vig)

        
    # def create_Candidate_locations_text(self):
    #     header_text = "set CL[1] :=\n"
    #     self.texts_variables.append(header_text)
    #     df = self.df_candidates_PHC.copy()
    #     for _, row in df.iterrows():
    #         text_aux = " ".join([
    #                     str(row.CO_UNIDADE),
    #                     str("\n")
    #                 ])
    #         self.texts_variables.append(text_aux)
        
        
    #     self.texts_variables.append(self.dot_vig)

    # def create_SHC_THC_empty_candidate_location(self):
    #     set_l1_level = "set L[1] := PHC1;\n"
    #     set_l2_level = "set CL[2] := ;\n"
    #     set_l3_level = "set CL[3] := ;\n"

    #     #self.texts_variables.append(set_l1_level)
    #     self.texts_variables.append(set_l2_level)
    #     self.texts_variables.append(set_l3_level)

    def create_mutable_texts_by_cluster(self):
        self.create_header_texts() #CLASSE PAI
        self.create_budgtes_text() #CLASSE PAI
        self.create_critical_rad_text() #CLASSE PAI

        self.create_Candidate_locations_text()
        self.create_SHC_THC_empty_candidate_location()

       # self.create_basic_heal_care_unit_teams_SHC_THC_text() #CLASSE PAI
        self.create_basic_heal_care_unit_teams_PHC_text() #REVISAR e Refazer! classes filhas! - VAMOS TER SO 3 EQUIPES ?
        self.create_basic_heal_care_unit_teams_SHC_text() #CLASSE PAI
        self.create_basic_heal_care_unit_teams_THC_text() #CLASSE PAI
        self.create_existing_health_care_units_FIRST_level() #CLASSE FILHA!
        self.create_existing_health_care_units_SECOND_level() #CLASSE PAI 
        self.create_existing_health_care_units_THIRD_level() #CLASSE PAI 
        self.create_vulnerability_population_table_text()  #CLASSE FILHA!
        self.create_variable_costs_PHC_text()  #CLASSE FILHA!
        self.create_variable_costs_SHC_text()  #CLASSE PAI 
        self.create_variable_costs_THC_text()  #CLASSE PAI 


        self.create_costs_PHC_teams_text() #REVISAR e Refazer! classes filhas! - VAMOS TER SO 3 EQUIPES ?
        self.create_costs_SHC_teams_text() #CLASSE PAI
        self.create_costs_THC_teams_text() #CLASSE PAI
        
        #Setor censitario - Pontos
        #self.create_distance_between_SC_PHC_text() #CLASSE FILHA!
        self.create_distance_between_SC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_SC_THC_text() #CLASSE FILHA!

        # #Nivel primario para secundario e terciario
        self.create_distance_between_PHC_SHC_text() #CLASSE FILHA!
        self.create_distance_between_PHC_THC_text() #CLASSE FILHA!

        # #Secundario para terciario
        self.create_distance_between_SHC_THC_text() #CLASSE PAI



        self.create_PHC_teams_text() #CLASSE FILHA! 
        self.create_SHC_teams_text() #CLASSE PAI
        self.create_THC_teams_text() #CLASSE PAI

        # #TODO: Nao sei o que é isso!
        self.create_param_C2_text() #CLASSE PAI!
        self.create_param_C3_text() #CLASSE PAI! 

        self.create_units_to_open_text()  #CLASSE PAI!


        self.create_proportion_patients_encm_PHC_text()  #CLASSE FILHA!
        self.create_proportion_patients_encm_SHC_text()  #CLASSE PAI!
        self.create_proportion_patients_encm_THC_text()  #CLASSE PAI! 

        self.create_percentual_max_teleatend_text()    #CLASSE PAI!
        self.create_percentual_max_deslocamento_text()  #CLASSE PAI!

    # def create_SC_PHC_text(self):
    #     header_text = "param D0_1 := \n"

    #     self.texts_variables_arch_2.append(header_text)
    #     for dk in self.dict_dist_SC_PHC:
    #         text_aux = " ".join([
    #                     str(dk["origem"]),
    #                     str(dk["destino"]),
    #                     str(dk["distancia"]),
    #                     str("\n") 
    #                 ])

    #         self.texts_variables_arch_2.append(text_aux)


    #     self.texts_variables_arch_2.append(self.dot_vig)

    # def create_Exist_PHC_to_all_PHC_text(self):
    #     text_comment = (
    #         "# Distance matrix between same-level facilities (for team transfer) \n"
    #         "# {EL[1], L[1]} default 0; # Distance between L1 facilities (min)  \n"
    #     )
    #     header_text = "param DL1 := \n"

    #     self.texts_variables_arch_2.append(text_comment)
    #     self.texts_variables_arch_2.append(header_text)
    #     for dk in self.dict_dist_exist_PHC_all_PHC:
    #         text_aux = " ".join([
    #                     str(dk["origem"]),
    #                     str(dk["destino"]),
    #                     str(dk["distancia"]),
    #                     str("\n") 
    #                 ])

    #         self.texts_variables_arch_2.append(text_aux)


    #     self.texts_variables_arch_2.append(self.dot_vig)

    def create_distances_text_by_cluster(self):
        self.create_header_text_arch_dist()
        #self.create_SC_set_text() # Por cluster nao tem o conjunto L[1]
        #self.create_PHC_SC_text()
        self.create_Exist_PHC_to_all_PHC_text()
        self.create_SC_PHC_text()