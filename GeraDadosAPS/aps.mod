#############################################################################
# Project CNPq: Increasing PHC with team sizing
# Author: João Flávio de Freitas Almeida <joao.flavio@dep.ufmg.br>
# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas
# Departmento de Engenharia de Produção
# Universidade Federal de Minas Gerais - Escola de Engenharia
#############################################################################
# Health Care Facility Location Problem with Team Reallocation
# >> Teams with excess capacity can be reassigned to locations with deficits
# >> Minimizes team displacement distance and need for new teams
#############################################################################

# Before running: CHECK: 
# py check_data_consistency.py foo.dat
# py check_data_consistency.py foo.dat dist.dat
# py check_data_consistency.py *.dat
# py check_data_consistency.py foo.dat > report.txt
# py check_data_consistency.py foo.dat dist.dat > report.txt

# py check_data_consistency.py LS.dat LS_distdur.dat
# py check_data_consistency.py LS_CLU.dat LS_CLU_distdur.dat
# py check_data_consistency.py Div_CLU.dat Div_CLU_distdur.dat
# py check_data_consistency.py MC_CLU.dat MC_CLU_distdur.dat
# py check_data_consistency.py Cont_CLU.dat Cont_CLU_distdur.dat
# py check_data_consistency.py BH_CLU.dat BH_CLU_distdur.dat
# py check_data_consistency.py BH.dat BH_distdur.dat > report_BH.txt


# glpsol -m aps.mod -d aps.dat -d city.dat --mipgap 0.01 --cuts --check --wmps aps.mps
# glpsol -m aps.mod -d aps.dat --mipgap 0.01 --cuts --check --wmps aps.mps
# highs --model_file .\aps.mps --aps options.opt 
# glpsol -m aps.mod -d aps.dat -d city.dat -r aps.sol


# https://ergo-code.github.io/HiGHS/dev/options/definitions/
# https://github.com/JuliaBinaryWrappers/HiGHSstatic_jll.jl/releases

# #----------------------------------------------------------------------------------------------------------------------------------------------#
# param now:= gmtime() -3*3600;
# param time, symbolic, := time2str(now, "%d de %b de 20%y as %T");
# #----------------------------------------------------------------------------------------------------------------------------------------------#

set I; # The set of demand points (Setor Censistário -> Clusters).
set C; # CNES codes


set K; # Health care levels (PHC, SHC, THC)


param Dmax{K}; # Maximal distance (or travel time)


set E{K}; # Health care team from level k 

# set L{k in K}; # Todos os destinos em cada nível (Existentes e candidatos)
# set EL{k in K} within L[k]; # EXISTING health care units on three levels (Cluster > CNES)
# set CL{k in K} := L[k] diff EL[k]; # CANDIDATE health care LOCATIONS on three levels (Cluster)
# set CL{k in K} within L[k]; # CANDIDATE health care LOCATIONS on three levels

set EL{k in K}; # (código CNES dentro de um cluster)
set CL{k in K} within I; # (código dos clusters candidatos)
set L{k in K} := EL[k] union CL[k]; 



param POP_PER_TEAM := 3000; # patients served per full team  (integer)
param COST_SCALE := 1e6;    # report in M R$

################################################
# BUDGET PARAMETER
param BUDGET >= 0; # Overall budget constraint ($/year)
param BUDGET_s          := BUDGET  / COST_SCALE;
param BUDGET_OVERRUN_MULT default 1e4;
# Penalty multiplier per M R$ of overrun in the objective.
# 1e4 means each R$1 overspent costs R$10,000 in the objective —
# the solver will only use budget_slack when truly forced to.
# Lower this (e.g. 100) if you want to observe trade-offs more freely.
################################################

param CE1{c1 in E[1]}; # Team cost K1 ($/year)
param CE2{c2 in E[2]}; # Team cost K2 ($/year)
param CE3{c3 in E[3]}; # Team cost K3 ($/year)

param CE1_s{c1 in E[1]} := CE1[c1] / COST_SCALE;
param CE2_s{c2 in E[2]} := CE2[c2] / COST_SCALE;
param CE3_s{c3 in E[3]} := CE3[c3] / COST_SCALE;

# Team relocation cost (per professional per distance unit)
param RC1{E[1]} default 20; # Relocation cost for PHC team ($/prof/min)
param RC2{E[2]} default 20; # Relocation cost for SHC team ($/prof/min)
param RC3{E[3]} default 20; # Relocation cost for THC team ($/prof/min)

param RC1_s{c1 in E[1]} := RC1[c1] / COST_SCALE;
param RC2_s{c2 in E[2]} := RC2[c2] / COST_SCALE;
param RC3_s{c3 in E[3]} := RC3[c3] / COST_SCALE;

param CKM:= 1;  # Custo por km
param M_TO_KM := 0.001; # Conversão metros para km

# Se existir um D0_1 com fora do raio proposto, e.g. 16 km, inserir uma distância muito 
# grande para não ser considerada no modelo
# set OD := I cross L[1];
# display OD;
param D0_1{i in I,j1 in L[1]}; # := 10;    # The travel distance between i and level-1 PCF.   (meters)
param D0_2{I,L[2]};    # The travel distance between i and level-2 SCF.   (meters)
param D0_3{I,L[3]};    # The travel distance between i and level-3 TCF.   (meters)
param D1_2{L[1],L[2]}; # The travel distance between candidate L1 and L2. (meters)
param D1_3{L[1],L[3]}; # The travel distance between candidate L1 and L3. (meters)
param D2_3{L[2],L[3]}; # The travel distance between candidate L2 and L3. (meters)

param D0_1_KM{i in I, j1 in L[1]} := D0_1[i,j1] * M_TO_KM;
param D0_2_KM{i in I, j2 in L[2]} := D0_2[i,j2] * M_TO_KM;
param D0_3_KM{i in I, j3 in L[3]} := D0_3[i,j3] * M_TO_KM;
param D1_2_KM{j1 in L[1], j2 in L[2]} := D1_2[j1,j2] * M_TO_KM;
param D1_3_KM{j1 in L[1], j3 in L[3]} := D1_3[j1,j3] * M_TO_KM;
param D2_3_KM{j2 in L[2], j3 in L[3]} := D2_3[j2,j3] * M_TO_KM;



# display min{i in I,j1 in L[1]}(D0_1[i,j1]);
# display max{i in I,j1 in L[1]}(D0_1[i,j1]);

# display min{i in I,j2 in L[2]}(D0_2[i,j2]);
# display max{i in I,j2 in L[2]}(D0_2[i,j2]);

# display min{i in I,j3 in L[3]}(D0_3[i,j3]);
# display max{i in I,j3 in L[3]}(D0_3[i,j3]);


param D1_0{j1 in L[1], i in I} := D0_1[i,j1];    # The travel distance between i and level-1 PCF.   (meters)
param D2_0{j2 in L[2], i in I} := D0_2[i,j2];    # The travel distance between i and level-2 SCF.   (meters)
param D3_0{j3 in L[3], i in I} := D0_3[i,j3];    # The travel distance between i and level-3 TCF.   (meters)
param D2_1{j2 in L[2], j1 in L[1]} := D1_2[j1,j2]; # The travel distance between candidate L1 and L2. (meters)
param D3_1{j3 in L[3], j1 in L[1]} := D1_3[j1,j3]; # The travel distance between candidate L1 and L3. (meters)
param D3_2{j3 in L[3], j2 in L[2]} := D2_3[j2,j3]; # The travel distance between candidate L2 and L3. (meters)

param D1_0_KM{j1 in L[1], i in I} := D0_1_KM[i,j1];
param D2_0_KM{j2 in L[2], i in I} := D0_2_KM[i,j2];
param D3_0_KM{j3 in L[3], i in I} := D0_3_KM[i,j3];
param D2_1_KM{j2 in L[2], j1 in L[1]} := D1_2_KM[j1,j2];
param D3_1_KM{j3 in L[3], j1 in L[1]} := D1_3_KM[j1,j3];
param D3_2_KM{j3 in L[3], j2 in L[2]} := D2_3_KM[j2,j3];
# set OD := EL[1] cross L[1];
# display OD;
# set OD := EL[2] cross L[2];
# display OD;
# Distance matrix between same-level facilities (for team transfer)

param DL1{e1 in EL[1], j1 in L[1]}; # Distance between L1 facilities (meters)
param DL2{EL[2], L[2]}  default (sum{e1 in EL[1], j1 in L[1]} DL1[e1,j1]) / (card(EL[1])*card(L[1])); # Distance between L2 facilities (meters)
param DL3{EL[3], L[3]}  default (sum{e1 in EL[1], j1 in L[1]} DL1[e1,j1]) / (card(EL[1])*card(L[1])); # Distance between L3 facilities (meters)

param DL1_KM{e1 in EL[1], j1 in L[1]} := DL1[e1,j1] * M_TO_KM;
param DL2_KM{e2 in EL[2], j2 in L[2]} := DL2[e2,j2] * M_TO_KM;
param DL3_KM{e3 in EL[3], j3 in L[3]} := DL3[e3,j3] * M_TO_KM;


# display min{i in EL[1],j1 in L[1]}(DL1[i,j1]);
# display max{i in EL[1],j1 in L[1]}(DL1[i,j1]);

# display min{i in EL[2],j2 in L[2]}(DL2[i,j2]);
# display max{i in EL[2],j2 in L[2]}(DL2[i,j2]);

# display min{i in EL[3],j3 in L[3]}(DL3[i,j3]);
# display max{i in EL[3],j3 in L[3]}(DL3[i,j3]);

param W{I}; # The population size at demand point i (pop) (pop cluster)

# # GLPK only: Cluster com população > 3.000 habitantes
# set CLU_gt_3K := {i in I: W[i]>3000};
# display card(CLU_gt_3K);

# Service operating capacity at IHC j
# The capacity of a level-1 PCF in K. (pop)
param SIZE0{L[1]}, default 3, <= 5; # Porte da UBS  # original values
param SIZEX{i in L[1]} default 0; # Exceptions UBS with very high demand
param SIZE{i in L[1]}:= if SIZEX[i] > 0 then SIZEX[i] else SIZE0[i];
# display SIZE;
param C1{j1 in L[1]} := SIZE[j1]*POP_PER_TEAM; 
# display C1;
param C2{L[2]}; # The capacity of a level-2 PCF in J.   (pop)
param C3{L[3]}; # The capacity of a level-3 PCF in J.   (pop)


# set Link01 dimen 2:= setof{i in I, j1 in L[1]: D0_1[i,j1] <= Dmax[1]}(i,j1);
# set Link10 dimen 2:= setof{j1 in L[1], i in I: D1_0[j1,i] <= Dmax[1]}(j1,i);
# NOTE: EL[1] capacity filter uses the maximum possible expanded capacity (SIZE=5 → 15000)
# so that demand points only reachable after expansion are included in the link sets.

# Per-demand adaptive distance (minimum to guarantee at least one link)
param adap_Dmax1{i in I} := max(Dmax[1], min{j1 in L[1]} D0_1[i,j1]);
param Dmax1 := max{i in I} adap_Dmax1[i];
# display Dmax1;
# display{i in I: adap_Dmax1[i] > Dmax[1]} adap_Dmax1[i];

set Link01 := { (i,j1) in I cross L[1]: D0_1[i,j1] <= adap_Dmax1[i] and
    (if j1 in EL[1] then SIZE[j1]*POP_PER_TEAM else C1[j1]) >= W[i] };
set Link10 := { (j1,i) in L[1] cross I: D1_0[j1,i] <= adap_Dmax1[i] and
    (if j1 in EL[1] then SIZE[j1]*POP_PER_TEAM else C1[j1]) >= W[i] };

# check{i in I}:  card({j1 in L[1] : (i,j1) in Link01}) >= 1;

# display card(Link01);
# display{i in I, j1 in L[1]: (i,j1) in Link01} D0_1[i,j1], W[i], C1[j1];

set Link02 dimen 2:= setof{i in I, j2 in L[2]: D0_2[i,j2] <= Dmax[2]}(i,j2);
set Link20 dimen 2:= setof{j2 in L[2], i in I: D2_0[j2,i] <= Dmax[2]}(j2,i);
set Link12 dimen 2:= setof{j1 in L[1], j2 in L[2]: D1_2[j1,j2] <= Dmax[2]}(j1,j2);
set Link21 dimen 2:= setof{j2 in L[2], j1 in L[1]: D2_1[j2,j1] <= Dmax[2]}(j2,j1);

set Link03 dimen 2:= setof{i in I, j3 in L[3]: D0_3[i,j3] <= Dmax[3]}(i,j3);
set Link30 dimen 2:= setof{j3 in L[3], i in I: D3_0[j3,i] <= Dmax[3]}(j3,i);
set Link13 dimen 2:= setof{j1 in L[1], j3 in L[3]: D1_3[j1,j3] <= Dmax[3]}(j1,j3);
set Link31 dimen 2:= setof{j3 in L[3], j1 in L[1]: D3_1[j3,j1] <= Dmax[3]}(j3,j1);
set Link23 dimen 2:= setof{j2 in L[2], j3 in L[3]: D2_3[j2,j3] <= Dmax[3]}(j2,j3);
set Link32 dimen 2:= setof{j3 in L[3], j2 in L[2]: D3_2[j3,j2] <= Dmax[3]}(j3,j2);

# set H1:= setof{i in I,j1 in L[1]: D0_1[i,j1] <= Dmax[1]} j1;
set H1:= setof{i in I,j1 in L[1]: (i,j1) in Link01} j1;

# set H2:= setof{j1 in L[1], j2 in L[2]: D1_2[j1,j2] <= Dmax[2]} j2;
set H2:= setof{j1 in L[1], j2 in L[2]: (j1,j2) in Link12} j2;

# set H3:= setof{j2 in L[2], j3 in L[3]: D2_3[j2,j3] <= Dmax[3]} j3;
set H3:= setof{j2 in L[2], j3 in L[3]: (j2,j3) in Link23} j3;

set L1:= L[1] inter H1;
set L2:= L[2] inter H2;
set L3:= L[3] inter H3;

# display Link01;
# display Link10;

# display Link02;
# display Link20;
# display Link12;
# display Link21;

# display Link03;
# display Link30;
# display Link13;
# display Link31;
# display Link23;
# display Link32;

# display L1;
# display L2;
# display L3;


# # ==== CHECK: Connectivity ==================================
# # FOR GLPK, only
# check{i in I} card({j1 in L[1]: (i,j1) in Link01}) > 0 ;
# check{i in I} card({j1 in L[1]: (j1,i) in Link10}) > 0 ;
# check{j1 in L[1]} card({j2 in L[2]: (j1,j2) in Link12}) > 0;
# check{j1 in L[1]} card({j2 in L[2]: (j2,j1) in Link21}) > 0;
# check{j2 in L[2]} card({j3 in L[3]: (j2,j3) in Link23}) > 0;
# check{j2 in L[2]} card({j3 in L[3]: (j3,j2) in Link32}) > 0;
# #############################################################

# display{i in I}: card({j1 in L[1]: (i,j1) in Link1});
# # display{i in I, j1 in L[1]: (i,j1) in Link1} (i,j1);
# display{j1 in L[1]}: card({j2 in L[2]: (j1,j2) in Link2});
# display{j2 in L[2]}: card({j3 in L[3]: (j2,j3) in Link3});



################################################
# param TC1{I,L[1]}; # Travel cost/pat  from demand point i to L1   ($/min)
# param TC2{L[1],L[2]}; # Travel cost/pat  from L1 to L2            ($/min)
# param TC3{L[2],L[3]}; # Travel cost/pat  from L2 to L3            ($/min)

param TC0_1{i in I,j1 in L[1]}:= (D0_1_KM[i,j1])*CKM; # Travel cost/pat  from demand point i to L1   ($/min)
param TC0_2{i in I,j2 in L[2]}:= (D0_2_KM[i,j2])*CKM; # Travel cost/pat  from demand point i to L1   ($/min)
param TC0_3{i in I,j3 in L[3]}:= (D0_3_KM[i,j3])*CKM; # Travel cost/pat  from demand point i to L1   ($/min)
param TC1_2{j1 in L[1], j2 in L[2]}:= (D1_2_KM[j1,j2])*CKM; # Travel cost/pat  from L1 to L2            ($/min)
param TC1_3{j1 in L[1], j3 in L[3]}:= (D1_3_KM[j1,j3])*CKM; # Travel cost/pat  from L1 to L2            ($/min)
param TC2_3{j2 in L[2], j3 in L[3]}:= (D2_3_KM[j2,j3])*CKM; # Travel cost/pat  from L2 to L3            ($/min)

param TC0_1_s{i in I,j1 in L[1]}:= TC0_1[i,j1] / COST_SCALE;
param TC0_2_s{i in I,j2 in L[2]}:= TC0_2[i,j2] / COST_SCALE;
param TC0_3_s{i in I,j3 in L[3]}:= TC0_3[i,j3] / COST_SCALE;
param TC1_2_s{j1 in L[1], j2 in L[2]}:= TC1_2[j1,j2] / COST_SCALE;
param TC1_3_s{j1 in L[1], j3 in L[3]}:= TC1_3[j1,j3] / COST_SCALE;
param TC2_3_s{j2 in L[2], j3 in L[3]}:= TC2_3[j2,j3] / COST_SCALE;


# Fonte: Tabela APS.dat.xlsx
param VC1{L[1]},  default 3; # := 3; # Variable cost of PHC j / pop h ($/pop)
param VC2{L[2]}; # := 0; # Variable cost of SHC j / pop h ($/pop)
param VC3{L[3]}; # := 0; # Variable cost of THC j / pop h ($/pop)

param VC1_s{j1 in L[1]} := VC1[j1] / COST_SCALE;
param VC2_s{j2 in L[2]} := VC2[j2] / COST_SCALE;
param VC3_s{j3 in L[3]} := VC3[j3] / COST_SCALE;

# Fixed cost per period for operating PHC j    ($/year)
# Fonte: https://cbc2022.abcustos.org.br/rest/artigo/98/semFolhaDeRosto/pdf?chaveDeAcessoNaoAutenticado=97827de5f831bdf92b6c6bd603308190ea2769c6
param FC1{j1 in L[1]} default SIZE[j1]*3000; # 100000; # Custos administrativos: 100 mil/ano ($/year): Dado de 2022 ajustado pela inflação
param FC2{L[2]}; # := 0; # Fixed cost per period for operating SHC j    ($/year)
param FC3{L[3]}; # := 0; # Fixed cost per period for operating THC j    ($/year)

param FC1_s{j1 in L[1]}  := FC1[j1]  / COST_SCALE;
param FC2_s{j2 in L[2]}  := FC2[j2]  / COST_SCALE;
param FC3_s{j3 in L[3]}  := FC3[j3]  / COST_SCALE;

# ############## Amortização anual para Investimento em nova UBS ############## 
param R:=0.04;   # Taxa de desconto anual
param N:=25;     # Vida útil (anos)
param I_L1; # 1000; # 3818078; # Investimento (custo de implantação) na nova UBS: Obra, reforma e equipamentos
# Fonte: https://www.gov.br/saude/pt-br/assuntos/novo-pac-saude/unidades-basicas-de-saude/faq-ubs/analise-habilitacao-e-selecao-das-propostas/valores-para-construcao-de-nova-ubs
param I_L2:= 0; # Investimento (custo de implantação) na nova UBS: Obra, reforma e equipamentos
param I_L3:= 0; # Investimento (custo de implantação) na nova UBS: Obra, reforma e equipamentos
# Annualized Investment for operating NEW PHC j    ($/year)
param IA1{CL[1]} := round(I_L1*(R*(1+R)^N)/((1+R)^N-1),0); 
# display IA1;
param IA1_s{j1 in CL[1]} := IA1[j1]  / COST_SCALE;

# Annualized Investment for operating NEW SHC j    ($/year)
param IA2{CL[2]}:= round(I_L2*(R*(1+R)^N)/((1+R)^N-1),0); 
# display IA2;
param IA2_s{j2 in CL[2]} := IA2[j2]  / COST_SCALE;

# Annualized Investment for operating NEW THC j    ($/year)
param IA3{CL[3]}:= round(I_L3*(R*(1+R)^N)/((1+R)^N-1),0); 
# display IA3;
param IA3_s{j3 in CL[3]} := IA3[j3]  / COST_SCALE;
# ##############################################################################

# ############## Amortização anual para Expansão de UBS EXISTENTE ##############
# Investment cost per extra SIZE unit to physically expand an existing EL[1] PHC
# (renovation / reform cost; typically less than full new-build I_L1)
param I_L1_exp;  # ($/SIZE unit)
# Annualized expansion investment per SIZE unit at an existing EL[1] facility
param IA1_exp_unit := round(I_L1_exp*(R*(1+R)^N)/((1+R)^N-1),0);
# Incremental annual operating cost per extra SIZE unit (mirrors FC1 = SIZE*3000 formula)
param IA1_exp_unit_s := IA1_exp_unit / COST_SCALE;

param FC1_exp_unit := 3000;  # ($/year per extra SIZE unit)
param FC1_exp_unit_s := FC1_exp_unit / COST_SCALE;
# ###############################################################################

param IVS{I}, default 0.5; # Índice de Vulnerabildade em Saude at demand point i (pop)
#################################################################
# Criando FAIXAS PROPORCIONAIS de IVS para cada município
#################################################################

# COUNT how many IVS[i] <= IVS[j] for each j
# param COUNT_IVS{j in I} := sum{i in I} (IVS[i] <= IVS[j]);
param COUNT_IVS{j in I} := sum{i in I} (if IVS[i] <= IVS[j] then 1 else 0);

# Select thresholds as the smallest IVS[j] reaching each rank
# ranks for 33%, 66%, 100%
param LOW_IVS := min{j in I : COUNT_IVS[j] >= ceil(card(I) * 0.33) } IVS[j];
param MED_IVS := min{j in I : COUNT_IVS[j] >= ceil(card(I) * 0.66) } IVS[j];
param HIG_IVS := min{j in I : COUNT_IVS[j] >= card(I) } IVS[j];

# # (prof/pop)
# param PROF_POP{i in I} := 
#     if IVS[i] <= LOW_IVS then 1/3500 # 2500 > 3500
#         else if IVS[i] <= MED_IVS then 1/3000
#         else if IVS[i] <= HIG_IVS then 1/2500 # 3500 > 2500
#         else "ERROR";

# IVS-adjusted population-per-team for each IVS bin
param POP_IVS{i in I} :=
    if IVS[i] <= LOW_IVS then 3500
    else if IVS[i] <= MED_IVS then 3000
    else if IVS[i] <= HIG_IVS then 2500
    else POP_PER_TEAM;   # safe default for missing IVS
    
# # Display IVS
# # =================================================
# display LOW_IVS, MED_IVS, HIG_IVS;
# display {i in I} i, IVS[i], W[i], PROF_POP[i];
# # =================================================

# param PROP{e1 in E[1]} :=
#     if e1 = "eSF" then 1
#     else if e1 = "eSB" then 1
#     else if e1 = "eMulti" then 1/9
#     else if e1 = "ACS" then 4 # (seria uma equipe de 4 ACS)
#     else 0;

# eMulti = 1 full team per 9 PHC teams -> 1 eMulti covers 9 × POP_PER_TEAM patients
param MULTI_SIZE := 9;   # integer: one eMulti team per MULTI_SIZE eSF teams

# Scaling coefficient: POP_PER_TEAM / POP_IVS[i] — ranges [0.86, 1.20] for eSF/eSB,
# and [0.095, 0.133] for eMulti (still small but 300x larger than before)

# Ministry of Health parameter for requirements PHC (prof/pop)
# >>> To avoid numerical instability <<<, se separate terms in the model
# param MS0_1{i in I, e1 in E[1]} := round(PROP[e1] * PROF_POP[i],5);
# display MS0_1;
# param TEAM_SCALE{i in I, e in E[1]} := PROP[e] * (POP_PER_TEAM / POP_IVS[i]);
param TEAM_SCALE0_1{i in I, e in E[1]} :=
    if e = "eMulti" then 1.0 / (MULTI_SIZE * POP_IVS[i])
    else if e = "ACS"    then 4.0 / POP_IVS[i]
    else                      1.0 / POP_IVS[i]; # eSF, eSB

# (prof/patient)
# param PROF_PAT := round(1/3000,5);
# param POP_PER_TEAM := 3000;   # (já declarado) patients served per full team  (integer)

# param MS1{e1 in E[1]} := round(PROP[e1]*PROF_PAT, 6);
# param MS2{E[2]} := round(1/3000,5); # Ministry of Health parameter for requirements SHC (prof/pop)
# param MS3{E[3]} := round(1/3000,5); # Ministry of Health parameter for requirements THC (prof/pop)
# >>> To avoid numerical instability <<<, se separate terms in the model

# MS1 is now only used inside ceil() for MAX_NEW_HIRE — use exact integer division
# param MS1{e1 in E[1]} := round(PROP[e1]*PROF_PAT, 6);
param TEAM_SCALE1{e in E[1]} :=
    if e = "eMulti" then 1 / (MULTI_SIZE * POP_PER_TEAM) # exact 1/9, no rounding
    else if e = "ACS"    then 4.0 / POP_PER_TEAM
    else                      1.0 / POP_PER_TEAM; # eSF, eSB

# POP_PER_TEAM-scaled versions for TeamBalance constraints.
# Multiplying the balance equation by POP_PER_TEAM converts tiny TEAM_SCALE coefficients
# (≈3e-5 for eMulti) into O(1) values, improving numerical conditioning dramatically.
#   TSCALE0_1_POP['eSF',i]   = POP_PER_TEAM / POP_IVS[i]     ∈ [0.857, 1.2]
#   TSCALE0_1_POP['eMulti',i]= POP_PER_TEAM / (9*POP_IVS[i]) ∈ [0.095, 0.133]
#   TSCALE0_1_POP['ACS',i]   = 4*POP_PER_TEAM / POP_IVS[i]   ∈ [3.43, 4.8]
#   TSCALE1_POP['eSF']   = 1.0,   TSCALE1_POP['eMulti'] = 1/9, TSCALE1_POP['ACS'] = 4.0
param TSCALE0_1_POP{i in I, e in E[1]} := TEAM_SCALE0_1[i,e] * POP_PER_TEAM;
param TSCALE1_POP{e in E[1]}           := TEAM_SCALE1[e]      * POP_PER_TEAM;

# param MS2{E[2]} := round(1/3000,5); # Ministry of Health parameter for requirements SHC (prof/pop)
# param MS3{E[3]} := round(1/3000,5); # M

param CNES1{E[1],EL[1]}; # Health professional teams PHC at location L1 (prof)
param CNES2{E[2],EL[2]}; # Health professional teams PHC at location L2 (prof)
param CNES3{E[3],EL[3]}; # Health professional teams PHC at location L3 (prof)


# For EL[1]: use max expanded capacity (SIZE=5 → 15000) so hiring is never capped
# below what a fully-expanded facility would require.
param MAX_NEW_HIRE1{e1 in E[1], j1 in L[1]} :=
    # if j1 in EL[1] then ceil(5*3000*MS1[e1])
    # else ceil(C1[j1]*MS1[e1]);
    if e1 = "eMulti" then ceil(5 * POP_PER_TEAM / (MULTI_SIZE * POP_PER_TEAM)) # = ceil(5/9) = 1
    else if e1 = "ACS" then ceil(5 * POP_PER_TEAM * 4 / POP_PER_TEAM) # = 20
    else                    ceil(5);   # eSF/eSB: 1 team per POP_PER_TEAM exactly

# param MAX_NEW_HIRE2{e2 in E[2], j2 in L[2]} := ceil(C2[j2]*MS2[e2]);
# param MAX_NEW_HIRE3{e3 in E[3], j3 in L[3]} := ceil(C3[j3]*MS3[e3]);
param MAX_NEW_HIRE2{e2 in E[2], j2 in L[2]} := ceil(C2[j2] / POP_PER_TEAM);
param MAX_NEW_HIRE3{e3 in E[3], j3 in L[3]} := ceil(C3[j3] / POP_PER_TEAM);

# display MAX_NEW_HIRE1;
# display MAX_NEW_HIRE2;
# display MAX_NEW_HIRE3;

# param O1{L[1]}; # The proportion of patients in a L-1 to a L-2 PCF. (%)
# param O2{L[2]}; # The proportion of patients in a L-2 to a L-3 SCF. (%)

# Primary care facility (PCF)
param O1_0{L[1]}; # The proportion of patients in a L-1 to a home i PCF. (%)
param O1_2{L[1]}; # The proportion of patients in a L-1 to a L-2 PCF. (%)
param O1_3{L[1]}; # The proportion of patients in a L-1 to a L-3 PCF. (%)
# Secondary care facility (SCF)
param O2_0{L[2]}; # The proportion of patients in a L-2 to a home i SCF. (%)
param O2_1{L[2]}; # The proportion of patients in a L-2 to a L-1 SCF. (%)
param O2_3{L[2]}; # The proportion of patients in a L-2 to a L-3 SCF. (%)
# Tertiary care facility (TCF)
param O3_0{L[3]}; # The proportion of patients in a L-3 to home i TCF. (%)
param O3_1{L[3]}; # The proportion of patients in a L-3 to a L-1 TCF. (%)
param O3_2{L[3]}; # The proportion of patients in a L-3 to a L-2 TCF. (%)

# # FOR GLPK, only
# check {j1 in L[1]}: O1_0[j1] + O1_2[j1] + O1_3[j1] <= 1;
# check {j1 in L[1]}: O1_0[j1] + O1_2[j1] + O1_3[j1] >= 0.9;
# check {j2 in L[2]}: O2_0[j2] + O2_1[j2] + O2_3[j2] <= 1;
# check {j2 in L[2]}: O2_0[j2] + O2_1[j2] + O2_3[j2] >= 0.9;
# check {j3 in L[3]}: O3_0[j3] + O3_1[j3] + O3_2[j3] <= 1;
# check {j3 in L[3]}: O3_0[j3] + O3_1[j3] + O3_2[j3] >= 0.9;

# # =================================================================================
# # Total DemandToL1,L2,L3 <= CapacityL1,L2,L3
# check: sum{i in I: card({j1 in L[1]: (i,j1) in Link01}) > 0} W[i] <= sum{j1 in L[1]} C1[j1];
# check: sum{i in I: card({j1 in L[1]: (i,j1) in Link01}) > 0} W[i]*max(max{j1 in L[1]}O1_2[j1], max{j3 in L[3]}O3_2[j3]) <= sum{j2 in L[2]} C2[j2];
# check: sum{i in I: card({j1 in L[1]: (i,j1) in Link01}) > 0} W[i]*max(max{j1 in L[1]}O1_3[j1], max{j2 in L[2]}O2_3[j2]) <= sum{j3 in L[3]} C3[j3];
# # =================================================================================


param U{K}; # The number of UNITS level-k to be established. (unit)


# display sum{i in I}W[i];            # Total demand for PHC
# display sum{j1 in EL[1]} C1[j1];    # Existing capacity
# display min{j1 in CL[1]}C1[j1]*U[1];    # Expansion possibility

# display sum{i in I}W[i] * max(max{j1 in L[1]}O1_2[j1], max{j3 in L[3]}O3_2[j3]); # Total demand for SHC
# display sum{j2 in EL[2]} C2[j2];     # Existing capacity
# # display min{j2 in CL[2]} C2[j2]*U[2];     # Expansion possibility

# display sum{i in I}W[i] * max(max{j1 in L[1]}O1_3[j1], max{j2 in L[2]}O2_3[j2]); # Total demand for THC
# display sum{j3 in EL[3]} C3[j3];      # Existing capacity
# # display min{j3 in CL[3]} C3[j3]*U[3];      # Expansion possibility

# Percentual maximo de Atendimentos Telemedicina de casa > PHC, SHC, THC
param MAX_TELE_PHC, <= 1.0;
param MAX_TELE_SHC, <= 1.0;
param MAX_TELE_THC, <= 1.0;

# Percentual maximo de deslocamentos Casa > PHC, SHC, THC 
param MAX_HOME_PHC, <= 1.0;
param MAX_HOME_SHC, <= 1.0;
param MAX_HOME_THC, <= 1.0;

################################################
# BUDGET PREPROCESSING
param MinCostPerNewPHC := if card(CL[1] inter L1) > 0 then
    min{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1] + sum{c1 in E[1]}CE1[c1]) else 0;
param MinCostPerNewSHC := if card(CL[2] inter L2) > 0 then
    min{j2 in CL[2] inter L2}(FC2[j2]+IA2[j2] + sum{c2 in E[2]}CE2[c2]) else 0;
param MinCostPerNewTHC := if card(CL[3] inter L3) > 0 then
    min{j3 in CL[3] inter L3}(FC3[j3]+IA3[j3] + sum{c3 in E[3]}CE3[c3]) else 0;

param ExistingCost := 
    sum{j1 in EL[1] inter L1}FC1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e] +  
    sum{j2 in EL[2] inter L2}FC2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] + 
    sum{j3 in EL[3] inter L3}FC3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e];

# display MinCostPerNewPHC;
# display MinCostPerNewSHC;
# display MinCostPerNewTHC;

# # BUDGET ANALYSIS
# # ====================================================
# display BUDGET;
# display ExistingCost;
# # FOR GLPK, only
# check: BUDGET >= ExistingCost;
# # ====================================================

param AvailableBudget := max(0, BUDGET - ExistingCost);
# param AvailableBudget := BUDGET - ExistingCost;

# param MaxNewPHC := if card(CL[1] inter L1) > 0 and MinCostPerNewPHC > 0 then 
#                    min(U[1], floor(AvailableBudget / MinCostPerNewPHC)) else 0;
# param MaxNewSHC := if card(CL[2] inter L2) > 0 and MinCostPerNewSHC > 0 then 
#                    min(U[2], floor(AvailableBudget / MinCostPerNewSHC)) else 0;
# param MaxNewTHC := if card(CL[3] inter L3) > 0 and MinCostPerNewTHC > 0 then 
#                    min(U[3], floor(AvailableBudget / MinCostPerNewTHC)) else 0;

param MaxNewPHC := if card(CL[1] inter L1) > 0 and MinCostPerNewPHC > 0 then 
                   U[1] else 0;
param MaxNewSHC := if card(CL[2] inter L2) > 0 and MinCostPerNewSHC > 0 then 
                   U[2] else 0;
param MaxNewTHC := if card(CL[3] inter L3) > 0 and MinCostPerNewTHC > 0 then 
                   U[3] else 0;

# display MaxNewPHC;
# display MaxNewSHC;
# display MaxNewTHC;

# ===============================================
# #  For GLPK, only
# ===============================================
# printf "\n=== PROBLEMATIC SECTORS ===\n";
# for {i in I: W[i] > 10 and card({j1 in L[1]: (i,j1) in Link01})==0} {
#     printf "%s  Pop=%3d  IVS=%.3f  Links_PHC=%d\n", 
#         i, W[i], IVS[i], 
#         card({j1 in L[1]: (i,j1) in Link01});
# }
# printf "Links_W_PHC: %d\n", card(Link01);
# printf "Links_W_SPHC: %d\n", card(Link02);
# printf "Links_W_THC: %d\n\n", card(Link03);
# ===============================================


# ===============================================
# #  For GLPK, only
# ===============================================
# printf: "\n========================================\n";
# printf: "BUDGET PREPROCESSING\n";
# printf: "========================================\n";
# printf: "Overall Budget:\t\t$%10.2f\n", BUDGET;
# printf: "Existing Cost:\t\t$%10.2f\n", ExistingCost;
# printf: "Available Budget:\t$%10.2f\n", AvailableBudget;
# printf: "========================================\n";
# printf: "Min Cost per New Facility:\n";
# printf: "  PHC:\t\t\t$%10.2f\n", MinCostPerNewPHC;
# printf: "  SHC:\t\t\t$%10.2f\n", MinCostPerNewSHC;
# printf: "  THC:\t\t\t$%10.2f\n", MinCostPerNewTHC;
# printf: "========================================\n";
# printf: "Budget-Adjusted Max New Units:\n";
# printf: "  PHC:\t\t\t%d (original: %d)\n", MaxNewPHC, U[1];
# printf: "  SHC:\t\t\t%d (original: %d)\n", MaxNewSHC, U[2];
# printf: "  THC:\t\t\t%d (original: %d)\n", MaxNewTHC, U[3];
# printf: "========================================\n\n";
# # ===============================================

# # ================================================================
# # For GLPK, only  MINIMUM NUMBER OF NEW (CL[1]) NEEDED
# # ================================================================
# # 1. Total Population of the municipality
# param Total_Population := sum{i in I} W[i];

# # 2. Current PHC Capacity from EXISTING facilities (based on eSF teams)
# param Current_PHC_Capacity := 
#     sum{j1 in EL[1]} CNES1["eSF", j1] * POP_PER_TEAM;

# # 3. Population deficit (that must be covered by new facilities or expansion)
# param Population_Deficit := Total_Population - Current_PHC_Capacity;

# # 4. Capacity provided by ONE new candidate location (default SIZE = 1)
# param Capacity_Per_New_CL := 1 * POP_PER_TEAM;   # 3000

# # 5. Minimum number of new Candidate Locations required
# param Min_New_CL := ceil( max(0, Population_Deficit) / Capacity_Per_New_CL );

# # ================================================================
# printf "\n=== PHC CAPACITY GAP ANALYSIS ===\n";
# printf "Total Population                  : %12d\n", Total_Population;
# printf "Current Capacity (eSF teams)      : %12d\n", Current_PHC_Capacity;
# printf "Population Deficit                : %12d\n", Population_Deficit;
# printf "Capacity per new CL (SIZE=1)      : %12d\n", Capacity_Per_New_CL;
# printf "MINIMUM NEW CANDIDATE LOCATIONS   : %12d\n\n", Min_New_CL;
# printf "Currently declared CL[1]          : %12d\n", card(CL[1]);
# # ================================================================



# Penalties (Automaticaly sized to the problem) P1 (surplus or deficit PHC)
param P1:= min((sum{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1]) + sum{j1 in L1, c1 in E[1]}CE1[c1])*10, sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to} RC1[e1]*DL1[from,to]*CE1[e1]);
# param P2:= min(sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to} RC2[e2]*DL2[from,to]*CE2[e2],P1);
# param P3:= min(sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to} RC3[e3]*DL3[from,to]*CE3[e3],P1);

# AFTER (safe for any number of locations):
param P2_raw := sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to} RC2[e2]*DL2[from,to]*CE2[e2];
param P2 := if P2_raw > 0 then min(P2_raw, P1) else P1;

param P3_raw := sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to} RC3[e3]*DL3[from,to]*CE3[e3];
param P3 := if P3_raw > 0 then min(P3_raw, P1) else P1;

param P1_s := P1 / COST_SCALE;
param P2_s := P2 / COST_SCALE;
param P3_s := P3 / COST_SCALE;

param P1_d := (P1 / COST_SCALE)*10;
param P2_d := (P2 / COST_SCALE)*10;
param P3_d := (P3 / COST_SCALE)*10;

# display P1;
# display (sum{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1]) + sum{j1 in L1, c1 in E[1]}CE1[c1])*10;
# display P2;
# display P3;

# Facility Order (number: for constraints: (forces one direction))
param ITEM1{L[1]}; 
param ITEM2{L[2]}; 
param ITEM3{L[3]}; 

# #############################################################
# # Check: New hiring costs must be higher than transfer costs
# #############################################################
#  # Cost of NEW teams hired    
# display sum{j1 in L1, c1 in E[1]}CE1[c1];
# display sum{j2 in L2, c2 in E[2]}CE2[c2];
# display sum{j3 in L3, c3 in E[3]}CE3[c3];

# # Team relocation costs (should be much less that New hired teams)
# display sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to} RC1[e1]*(DL1[from,to]/1000);
# display sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to} RC2[e2]*(DL2[from,to]/1000);
# display sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to} RC3[e3]*(DL3[from,to]/1000);

# # FOR GLPK, only
# check sum{j1 in L1, c1 in E[1]}CE1[c1] >= sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to} RC1[e1]*(DL1[from,to]/1000);

# check sum{j2 in L2, c2 in E[2]}CE2[c2] >= sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to} RC2[e2]*(DL2[from,to]/1000);

# check sum{j3 in L3, c3 in E[3]}CE3[c3] >= sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to} RC3[e3]*(DL3[from,to]/1000);


#################################################
# DECISION VARIABLES
#################################################

# Patient allocation
# var y{i in I, j1 in L1}, >=0, binary; # 1, if Pop is ASSIGNED to L-1 PCF
# REMOVED y0_1, y0_2, y0_3: these were fully determined by R0e/f/g:
#   y0_k = (u_k + ut_k) / W[i]
# They carry no new information and merely double linking constraints.
# R0a (sum y0_k = 1) is equivalent to DemandOut (already present).
# FlowImpliesLink_Out (u0_1 <= W*y0_1 = u0_1+ut1) is trivially true since ut1 >= 0.
# FlowImpliesLink_In is restated below without y0_1.
var y1{j1 in L1}, >=0, binary; # 1, if a L-1 PCF is used
var y2{j2 in L2}, >=0, binary; # 1, if a L-2 SCF is used
var y3{j3 in L3}, >=0, binary; # 1, if a L-3 TCF is used

# ---------------------------------------------------------------
# PHC CAPACITY EXPANSION (existing EL[1] facilities only)
# extra_size1[j1] = number of additional SIZE units built at j1
# Effective capacity becomes C1[j1] + extra_size1[j1]*3000
# Bound: SIZE[j1] + extra_size1[j1] <= 5  (max real size = 5)
# ---------------------------------------------------------------
# var extra_size1{j1 in EL[1] inter L1}, integer, >= 0, <= 3; # - SIZE[j1];
var extra_size1{j1 in L[1] inter L1}, integer, >= 0, <= 5 - SIZE0[j1];
# var extra_size1{j1 in EL[1] inter L1}, integer, >= 0;


# Binary assignment: 1 if origin i sends patients to PHC j1, 0 otherwise
# var z0_1{i in I, j1 in L1: (i,j1) in Link01}, binary; # 1 if i uses PHC j1

# Patient flows “fluxo de ida”
var u0_1{i in I, j1 in L1: (i,j1) in Link01}, >=0, <= W[i];  # The flow between demand point i and L1 (pop)
# per-node bounds derived from problem structure
param MaxFlow1{j1 in L1} := sum{i in I: (i,j1) in Link01} W[i];
var u1_2{j1 in L1, j2 in L2: (j1,j2) in Link12}, >=0, <= MaxFlow1[j1];  # The flow between L1 and L2 (pop)

param MaxFlow2{j2 in L2} := sum{i in I: (i,j2) in Link02} W[i];
var u2_3{j2 in L2, j3 in L3: (j2,j3) in Link23}, >=0, <= MaxFlow2[j2];  # The flow between L2 and L3 (pop)

var u0_2{i in I, j2 in L2: (i,j2) in Link02} >= 0, <= W[i];  # Casa → Clínica (bypass UBS)
var u0_3{i in I, j3 in L3: (i,j3) in Link03} >= 0, <= W[i];  # Casa → Hospital (bypass UBS e clínica)
var u1_3{j1 in L1, j3 in L3: (j1,j3) in Link13} >= 0, <= MaxFlow1[j1];  # UBS → Hospital (encaminhamento direto)

# Fluxos de “passo inverso” (step-down)
param MaxFlow3{j3 in L3} := sum{i in I: (i,j3) in Link03} W[i];
var u3_2{j3 in L3, j2 in L2: (j3,j2) in Link32} >= 0, <= MaxFlow3[j3];  # Alta hospitalar → clínica
var u3_1{j3 in L3, j1 in L1: (j3,j1) in Link31} >= 0, <= MaxFlow3[j3];  # Alta hospitalar → UBS
var u2_1{j2 in L2, j1 in L1: (j2,j1) in Link21} >= 0, <= MaxFlow2[j2];  # Retorno da clínica → UBS

var u3_0{j3 in L3, i in I: (j3,i) in Link30} >= 0, <= MaxFlow3[j3];  # Alta hospitalar → Casa
var u2_0{j2 in L2, i in I: (j2,i) in Link20} >= 0, <= MaxFlow2[j2];  # Retorno Clínica → Casa
var u1_0{j1 in L1, i in I: (j1,i) in Link10} >= 0, <= MaxFlow1[j1];  # Alta UBS → Casa


# fluxos de telemedicina (Casa -> unidade que presta teleconsulta)
var ut1{i in I, j1 in L1: (i,j1) in Link01} >= 0;   # tele: domicílio -> UBS (tele atendido por profissional na UBS)
var ut2{i in I, j2 in L2: (i,j2) in Link02} >= 0;   # tele: domicílio -> Clínica (tele atendido por profissional na clínica)
var ut3{i in I, j3 in L3: (i,j3) in Link03} >= 0;   # tele: domicílio -> Hospital (tele atendido por profissional no hospital)

# Team variables (positive = deficit/need, negative = excess/surplus)
# REMOVED <= 1 caps: in the integer problem, newhire/transfer may round down, requiring
# deficit > 1 to satisfy the balance equality. Capping at 1 causes MIP infeasibility.
# The large penalty P*_s in the objective drives deficit to 0 without an artificial cap.
var deficit1{E[1], L1}, >=0; # Deficit of professional e on location L1 (teams)
var deficit2{E[2], L2}, >=0; # Deficit of professional e on location L2 (teams)
var deficit3{E[3], L3}, >=0; # Deficit of professional e on location L3 (teams)

# var surplus1{E[1],EL[1] inter L1}, >= 0; # Surplus of prof e at existing L1 (prof)
# var surplus2{E[2],EL[2] inter L2}, >= 0; # Surplus of prof e at existing L2 (prof)
# var surplus3{E[3],EL[3] inter L3}, >= 0; # Surplus of prof e at existing L3 (prof)

var surplus1{E[1], L1}, >= 0; # Surplus of prof e at existing L1 (prof)
var surplus2{E[2], L2}, >= 0; # Surplus of prof e at existing L2 (prof)
var surplus3{E[3], L3}, >= 0; # Surplus of prof e at existing L3 (prof)


# Team transfer variables (from existing location to any location with deficit)
var transfer1{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}, integer, >= 0, <= CNES1[e1,from] + MAX_NEW_HIRE1[e1,to];
var transfer2{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}, integer, >= 0, <= CNES2[e2,from] + MAX_NEW_HIRE2[e2,to];
var transfer3{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}, integer, >= 0, <= CNES3[e3,from] + MAX_NEW_HIRE3[e3,to];


# Variables (add to variable section)
var HasTransferOut1{e1 in E[1], j1 in EL[1] inter L1}, binary;
var HasTransferOut2{e2 in E[2], j2 in EL[2] inter L2}, binary;
var HasTransferOut3{e3 in E[3], j3 in EL[3] inter L3}, binary;

# New teams hired (only for candidate locations or to cover remaining deficits)
# New professionals hired at L1, L2, L3 (prof)
var newhire1{e1 in E[1], j1 in L1}, integer, >= 0, <= MAX_NEW_HIRE1[e1,j1]; 
var newhire2{e2 in E[2], j2 in L2}, integer, >= 0, <= MAX_NEW_HIRE2[e2,j2]; 
var newhire3{e3 in E[3], j3 in L3}, integer, >= 0, <= MAX_NEW_HIRE3[e3,j3]; 


################################################
# BUDGET SLACK (soft budget constraint)
# Allows spending beyond BUDGET when needed for feasibility.
# Minimized in the objective via a large penalty multiplier.
################################################
# Amount by which costs may exceed BUDGET (M R$, same scale as BUDGET_s)
var budget_slack >= 0;  

# param USERVED_PENALTY := P1_s; # Or 1e8/COST_SCALE
# var unserved_slack{i in I} >= 0; # Patients that can not be routed

# var Total_Costs_APS, >=0; # Aux variable for report
var Total_Costs_APS_s, >=0; # Aux variable for report

#################################################
# CONSTRAINTS
#################################################
# Fix variables of EXISTING locations (they must remain open)
s.t. F1{j1 in EL[1] inter L1}: y1[j1] = 1; 
s.t. F2{j2 in EL[2] inter L2}: y2[j2] = 1; 
s.t. F3{j3 in EL[3] inter L3}: y3[j3] = 1;

# Maximum surplus of prof e at existing L (prof): Surplus can not exceed CNEs
s.t. Surplus1LimEx{e1 in E[1],j1 in EL[1] inter L1}: surplus1[e1,j1] <= CNES1[e1,j1]; 
s.t. Surplus2LimEx{e2 in E[2],j2 in EL[2] inter L2}: surplus2[e2,j2] <= CNES2[e2,j2]; 
s.t. Surplus3LimEx{e3 in E[3],j3 in EL[3] inter L3}: surplus3[e3,j3] <= CNES3[e3,j3]; 


# # #################################################################
# # # High Service Level! : New hire in case of minimum deficit. 
# # # (Problem becomes very difficult or infeasible)
# # # Medium Service Level: Deactivate this constraint
# # # Deficit can be covered by hiring OR by receiving transfers
# # #################################################################
# s.t. NewHire1_HighSL{e1 in E[1]}: sum{j1 in EL[1]} deficit1[e1,j1] <= sum{j1 in EL[1]} newhire1[e1,j1];
# s.t. NewHire2_HighSL{e2 in E[2]}: sum{j2 in EL[2]} deficit2[e2,j2] <= sum{j2 in EL[2]} newhire2[e2,j2];
# s.t. NewHire3_HighSL{e3 in E[3]}: sum{j3 in EL[3]} deficit3[e3,j3] <= sum{j3 in EL[3]} newhire3[e3,j3];


# Population assignment

# Cada origem i é atribuída a exatamente 1 UBS j1
# R0a REMOVED: sum{y0_k} = 1 is identical to DemandOut / W[i], already enforced below.
# s.t. R0a{i in I}: sum y0_1 + sum y0_2 + sum y0_3 = 1;

# Patients assigned to closest health unit (>>> HARD CONSTRAINT!<<<)
# s.t. R0b (>>> HARD CONSTRAINT!<<<)
# s.t. R0b{i in I, j1 in L1: (i,j1) in Link01}: sum{k1 in L1: (i,k1) in Link01 and D0_1[i,k1]>D0_1[i,j1]}y0_1[i,k1] + y1[j1] <= 1;

# s.t. R0c{i in I, j2 in L2: (i,j2) in Link02}: sum{k2 in L2: D0_2[i,k2]>D0_2[i,j2]}y0_2[i,k2] + y2[j2] <= 1;
# s.t. R0d{i in I, j3 in L3: (i,j3) in Link03}: sum{k3 in L3: D0_3[i,k3]>D0_3[i,j3]}y0_3[i,k3] + y3[j3] <= 1;

# FlowImpliesLink_Out REMOVED: u0_1 <= W*y0_1 = u0_1+ut1 is trivially true (ut1>=0).
# FlowImpliesLink_In restated without y0_1:
# Substituting y0_1 = (u0_1 + ut1)/W[i] gives: u1_0[j1,i] <= u0_1[i,j1] + ut1[i,j1]
s.t. FlowImpliesLink_In {i in I, j1 in L1: (i,j1) in Link01}:
    u1_0[j1,i] <= u0_1[i,j1] + ut1[i,j1];


# R0e/R0f/R0g REMOVED: these defined y0_k = (u_k + ut_k)/W[i].
# Since y0_k variables are removed entirely, these definitions are no longer needed.
# The flow totals are enforced directly by DemandOut below.

# Percentual maximo de Atendimentos Telemedicina de casa > PHC, SHC, THC
s.t. R0h{i in I, j1 in L1: (i,j1) in Link01}: ut1[i,j1] <= MAX_TELE_PHC * u0_1[i,j1];
s.t. R0i{i in I, j2 in L2: (i,j2) in Link02}: ut2[i,j2] <= MAX_TELE_SHC * u0_2[i,j2];
s.t. R0j{i in I, j3 in L3: (i,j3) in Link03}: ut3[i,j3] <= MAX_TELE_THC * u0_3[i,j3];

# Percentual maximo de deslocamentos Casa > PHC, SHC, THC 
s.t. R0k{i in I, j1 in L1: (i,j1) in Link01}: u0_1[i,j1] <= MAX_HOME_PHC * W[i];
s.t. R0l{i in I, j2 in L2: (i,j2) in Link02}: u0_2[i,j2] <= MAX_HOME_SHC * W[i];
s.t. R0m{i in I, j3 in L3: (i,j3) in Link03}: u0_3[i,j3] <= MAX_HOME_THC * W[i];



# Balanceamento da demanda na origem i (todas as saídas = W[i])
# (Somam-se todos os tipos de saída do domicílio: presencial para L1/L2/L3 
# e tele para L1/L2/L3.)
s.t. DemandOut{i in I}:
    sum{j1 in L1: (i,j1) in Link01} u0_1[i,j1]
  + sum{j2 in L2: (i,j2) in Link02} u0_2[i,j2]
  + sum{j3 in L3: (i,j3) in Link03} u0_3[i,j3]
  + sum{j1 in L1: (i,j1) in Link01} ut1[i,j1]
  + sum{j2 in L2: (i,j2) in Link02} ut2[i,j2]
  + sum{j3 in L3: (i,j3) in Link03} ut3[i,j3]
#   + unserved_slack[i]
  = W[i];

# Demanda retornando para a origem i (todas as entradas de step-down = W[i])
# (As altas / retornos de cada nível devolvem pacientes à sua origem; somam-se e igualam W[i].)
s.t. DemandIn{i in I}:
    sum{j1 in L1: (j1,i) in Link10} u1_0[j1,i] # O1_0[j1]*
  + sum{j2 in L2: (j2,i) in Link20} u2_0[j2,i] # O2_0[j2]*
  + sum{j3 in L3: (j3,i) in Link30} u3_0[j3,i] # O3_0[j3]*
  = W[i];


# Flow balance PHC > SHC > THC
s.t. R1{j1 in L1}: 
    # Outflows
    sum{i in I: (j1,i) in Link10} u1_0[j1,i]         # L1 → Home # O1_0[j1]*
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]     # L1 → L2    # O1_2[j1]*
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3] =   # L1 → L3    # O1_3[j1]*
    # Inflows
    sum{i in I: (i,j1) in Link01}u0_1[i,j1]                   # Home → L1
    + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{i in I: (i,j1) in Link01} ut1[i,j1];                # Telemedicine → L1

s.t. R1a{j1 in L1}: 
    # Outflows
    O1_0[j1]*
    (sum{i in I: (j1,i) in Link10}u1_0[j1,i]         # L1 → Home
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]     # L1 → L2
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3]) <=   # L1 → L3
    sum{i in I: (j1,i) in Link10}u1_0[j1,i];     # L1 → Home

s.t. R1b{j1 in L1}: 
    # Outflows
    O1_2[j1]*
    (sum{i in I: (j1,i) in Link10}u1_0[j1,i]         # L1 → Home
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]     # L1 → L2
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3]) <=   # L1 → L3
    sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2];     # L1 → L2

s.t. R1c{j1 in L1}: 
    # Outflows
    O1_3[j1]*
    (sum{i in I: (j1,i) in Link10}u1_0[j1,i]         # L1 → Home
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]     # L1 → L2
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3]) <=   # L1 → L3
    sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3];     # L1 → L3


s.t. R2{j2 in L2}: 
    # Outflows
    sum{i in I: (j2,i) in Link20} u2_0[j2,i]              # O2_0[j2]*
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]          # O2_1[j2]*
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3] =        # O2_3[j2]*
    # Inflows
    sum{i in I: (i,j2) in Link02}u0_2[i,j2] 
    + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
    + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]
    + sum{i in I: (i,j2) in Link02} ut2[i,j2];

s.t. R2a{j2 in L2}: 
    # Outflows
    O2_0[j2]*
    (sum{i in I: (j2,i) in Link20}u2_0[j2,i]         # L2 → Home
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]     # L2 → L1
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3]) <=   # L2 → L3
    sum{i in I: (j2,i) in Link20}u2_0[j2,i];     # L2 → Home

s.t. R2b{j2 in L2}: 
    # Outflows
    O2_1[j2]*
    (sum{i in I: (j2,i) in Link20}u2_0[j2,i]         # L2 → Home
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]     # L2 → L1
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3]) <=   # L2 → L3
    sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1];     # L2 → L1

s.t. R2c{j2 in L2}: 
    # Outflows
    O2_3[j2]*
    (sum{i in I: (j2,i) in Link20}u2_0[j2,i]         # L2 → Home
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]     # L2 → L1
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3]) <=   # L2 → L3
    sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3];     # L2 → L3

s.t. R3{j3 in L3}: 
    # Outflows
    sum{i in I: (j3,i) in Link30} u3_0[j3,i] # O3_0[j3]*
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]  # O3_1[j3]*
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2] = # O3_2[j3]*
    # Inflows
    sum{i in I: (i,j3) in Link03} u0_3[i,j3] 
    + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
    + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]
    + sum{i in I: (i,j3) in Link03} ut3[i,j3];

s.t. R3a{j3 in L3}: 
    # Outflows
    O3_0[j3]*
    (sum{i in I: (j3,i) in Link30}u3_0[j3,i]         # L3 → Home
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]     # L3 → L1
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2]) <=   # L3 → L2
    sum{i in I: (j3,i) in Link30}u3_0[j3,i];     # L3 → Home

s.t. R3b{j3 in L3}: 
    # Outflows
    O3_1[j3]*
    (sum{i in I: (j3,i) in Link30}u3_0[j3,i]         # L3 → Home
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]     # L3 → L1
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2]) <=   # L3 → L2
    sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1];     # L3 → L1

s.t. R3c{j3 in L3}: 
    # Outflows
    O3_1[j3]*
    (sum{i in I: (j3,i) in Link30}u3_0[j3,i]         # L3 → Home
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]     # L3 → L1
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2]) <=   # L3 → L2
    sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2];     # L3 → L1


#################################################
# PREVENT CIRCULAR TRANSFERS
#################################################
# Prevent transfers from higher to lower order (forces one direction)
s.t. DirectedTransfer1{e1 in E[1], from in EL[1] inter L1, to in L1: 
    from != to and ITEM1[from] > ITEM1[to]}:
    transfer1[e1,from,to] = 0;

s.t. DirectedTransfer2{e2 in E[2], from in EL[2] inter L2, to in L2: 
    from != to and ITEM2[from] > ITEM2[to]}:
    transfer2[e2,from,to] = 0;

s.t. DirectedTransfer3{e3 in E[3], from in EL[3] inter L3, to in L3: 
    from != to and ITEM3[from] > ITEM3[to]}:
    transfer3[e3,from,to] = 0;


#################################################
# PREVENT CHAIN TRANSFERS (Transitive Reduction)
#################################################
# If location A transfers to B, and B transfers to C,
# then A should transfer directly to C instead.
# This prevents: A→B→C and enforces: A→C
#
# IMPLEMENTATION: If j is already sending teams out (HasTransferOut = 1),
# no other location may send teams INTO j.
# This replaces the cubic NoChainTransfer*_Strong enumeration
# (O(|E|×|EL|²×|L|) constraints → O(|E|×|EL|) constraints)
# and is mathematically equivalent for integer transfer variables.
#
# Proof of equivalence:
#   NoChainTransfer_Strong said: for every triple (A,B,C) with ITEM(A)<ITEM(B)<ITEM(C),
#     transfer[e,A,B] + transfer[e,B,C] ≤ 1.
#   Since transfers are integers ≥ 0, this means:
#     if B sends to any C  (HasTransferOut[e,B] = 1), then A→B must be 0 for all A.
#   This is exactly: sum(transfers INTO B) ≤ CNES[e,B] × (1 - HasTransferOut[e,B]).

s.t. NoChainTransfer1_Strong{e1 in E[1], j1 in EL[1] inter L1}:
    sum{from in EL[1] inter L1: from != j1 and ITEM1[from] < ITEM1[j1]}
        transfer1[e1,from,j1]
    <= CNES1[e1,j1] * (1 - HasTransferOut1[e1,j1]);

s.t. NoChainTransfer2_Strong{e2 in E[2], j2 in EL[2] inter L2}:
    sum{from in EL[2] inter L2: from != j2 and ITEM2[from] < ITEM2[j2]}
        transfer2[e2,from,j2]
    <= CNES2[e2,j2] * (1 - HasTransferOut2[e2,j2]);

s.t. NoChainTransfer3_Strong{e3 in E[3], j3 in EL[3] inter L3}:
    sum{from in EL[3] inter L3: from != j3 and ITEM3[from] < ITEM3[j3]}
        transfer3[e3,from,j3]
    <= CNES3[e3,j3] * (1 - HasTransferOut3[e3,j3]);

#################################################
# Strict: Incoming XOR Outgoing (not both)
#################################################
# "You can only send out teams if you haven't received any teams in."
# If you receive 1 eMulti team, then CNES[eMulti,j1] - 1 is the maximum you can send out. If CNES was 0, then 0 - 1 = -1 means you cannot send any (constraint violated if you try).

s.t. NoSendIfReceivePHC{e1 in E[1], j1 in EL[1] inter L1}:
    sum{to in L1: to != j1 and ITEM1[j1] < ITEM1[to]} transfer1[e1,j1,to] 
    <= CNES1[e1,j1] - sum{from in EL[1] inter L1: from != j1 and ITEM1[from] < ITEM1[j1]} transfer1[e1,from,j1];

s.t. NoSendIfReceiveSHC{e2 in E[2], j2 in EL[2] inter L2}:
    sum{to in L2: to != j2 and ITEM2[j2] < ITEM2[to]} transfer2[e2,j2,to] 
    <= CNES2[e2,j2] - sum{from in EL[2] inter L2: from != j2 and ITEM2[from] < ITEM2[j2]} transfer2[e2,from,j2];

s.t. NoSendIfReceiveTHC{e3 in E[3], j3 in EL[3] inter L3}:
    sum{to in L3: to != j3 and ITEM3[j3] < ITEM3[to]} transfer3[e3,j3,to] 
    <= CNES3[e3,j3] - sum{from in EL[3] inter L3: from != j3 and ITEM3[from] < ITEM3[j3]} transfer3[e3,from,j3];


#################################################
# TEAM BALANCE CONSTRAINTS - LEVEL 1 (PHC)
#################################################
# CNES (existente) - Necessário + Transferências OUT - Transferências IN + Novas Contratações = Excesso - Déficit
# For EXISTING locations: calculate surplus/deficit
# s.t. TeamBalance1e{j1 in EL[1] inter L1, e1 in E[1]}:
#     CNES1[e1,j1]  # Existing teams
#     # Required teams based on patient flow    
#     - (sum{i in I: (i,j1) in Link01} (u0_1[i,j1]+ut1[i,j1])*MS0_1[i,e1] 
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]*MS1[e1] 
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]*MS1[e1])
#     + sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
#     - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
#     + newhire1[e1,j1]  # New teams hired
#     = surplus1[e1,j1] - deficit1[e1,j1];

s.t. TeamBalance1e{j1 in EL[1] inter L1, e1 in E[1]}:
    # Multiplied through by POP_PER_TEAM to eliminate tiny TEAM_SCALE coefficients.
    # Mathematically identical to original; all sides scaled by the same constant.
    CNES1[e1,j1] * POP_PER_TEAM
    - (sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1])  * TSCALE0_1_POP[i,e1]
    + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1]               * TSCALE1_POP[e1]
    + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1]               * TSCALE1_POP[e1])
    + POP_PER_TEAM * sum{from in EL[1] inter L1: from != j1} transfer1[e1,from,j1]
    - POP_PER_TEAM * sum{to   in L1:             to   != j1} transfer1[e1,j1,to]
    + POP_PER_TEAM * newhire1[e1,j1]
    = POP_PER_TEAM * (surplus1[e1,j1] - deficit1[e1,j1]);

# s.t. TeamBalance1e{j1 in EL[1] inter L1, e1 in E[1]}:    
#     POP_PER_TEAM * CNES1[e1,j1]
#     - sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1])  * (TEAM_SCALE0_1[i,e1]*POP_IVS[i])
#     - sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1]               * (TEAM_SCALE1[e1]* POP_PER_TEAM)
#     - sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1]               * (TEAM_SCALE1[e1]* POP_PER_TEAM)    
#     + POP_PER_TEAM * sum{from in EL[1] inter L1: from != j1} transfer1[e1,from,j1]
#     - POP_PER_TEAM * sum{to   in L1:             to   != j1} transfer1[e1,j1,to]
#     + POP_PER_TEAM * newhire1[e1,j1]
#     = POP_PER_TEAM * (surplus1[e1,j1] - deficit1[e1,j1]);



# # For CANDIDATE locations: only new hires and transfers IN
# s.t. TeamBalance1c{j1 in CL[1] inter L1, e1 in E[1]}:
#     # Required teams
#     - (sum{i in I: (i,j1) in Link01} (u0_1[i,j1]+ut1[i,j1])*MS0_1[i,e1] + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]*MS1[e1] + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]*MS1[e1])
#     + sum{from in EL[1] inter L1}transfer1[e1,from,j1]  # Transfers IN
#     + newhire1[e1,j1]  # New hires
#     = surplus1[e1,j1] - deficit1[e1,j1];

s.t. TeamBalance1c{j1 in CL[1] inter L1, e1 in E[1]}:
    # No CNES term (candidates start with zero teams). Scaled by POP_PER_TEAM.
    - (sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1]) * TSCALE0_1_POP[i,e1]
    + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1]               * TSCALE1_POP[e1]
    + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1]               * TSCALE1_POP[e1])
    + POP_PER_TEAM * sum{from in EL[1] inter L1} transfer1[e1,from,j1]
    + POP_PER_TEAM * newhire1[e1,j1]
    = POP_PER_TEAM * (surplus1[e1,j1] - deficit1[e1,j1]);

# s.t. TeamBalance1c{j1 in CL[1] inter L1, e1 in E[1]}:
#     # No CNES term (candidates start with zero teams)
#     - sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1])  * (TEAM_SCALE0_1[i,e1]*POP_IVS[i])
#     - sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1]               * (TEAM_SCALE1[e1]* POP_PER_TEAM)
#     - sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1]               * (TEAM_SCALE1[e1]* POP_PER_TEAM)
#     + POP_PER_TEAM * sum{from in EL[1] inter L1} transfer1[e1,from,j1]
#     + POP_PER_TEAM * newhire1[e1,j1]
#     = POP_PER_TEAM * (surplus1[e1,j1] - deficit1[e1,j1]);

# Surplus can only come from existing locations with teams
s.t. SurplusLimit1{e1 in E[1], j1 in EL[1] inter L1}:
    surplus1[e1,j1] <= CNES1[e1,j1];

# Teams transferred OUT <= CNES
s.t. TransfOut1_lt_CNES{e1 in E[1], j1 in EL[1], to in L1: to != j1}: transfer1[e1,j1,to] <= CNES1[e1,j1]; 


#################################################
# MINIMUM STAFFING REQUIREMENT FOR eSF
#################################################
# Every existing PHC must maintain at least 1 eSF team
# (eSF is the core family health team - cannot be completely removed)
s.t. MinimumeSF_AtExisting{j1 in EL[1] inter L1}:
    CNES1['eSF',j1]  # Existing eSF teams
    + sum{from in EL[1] inter L1: from != j1}transfer1['eSF',from,j1]  # Transfers IN
    - sum{to in L1: to != j1}transfer1['eSF',j1,to]  # Transfers OUT    
    + newhire1['eSF',j1]  # New hires
    >= 1;
    

# ########################################################################
# # Result eSF = Result eSB (CNES + Transfers IN - transferred OUT + new hire)
# # >> ATENÇÃO: Se proporção de paciente/pop de eSF e eSB for diferente, INFEASIBLE!
# ########################################################################
s.t. Team_SF_equal_SBe{j1 in EL[1] inter L1}: 
    CNES1['eSF',j1] 
        + sum{from in EL[1] inter L1: from != j1}transfer1['eSF',from,j1] # Transfers IN
        - sum{to in L1: to != j1}transfer1['eSF',j1,to] # Teams transferred OUT
        + newhire1['eSF',j1] =
    CNES1['eSB',j1] 
        + sum{from in EL[1] inter L1: from != j1}transfer1['eSB',from,j1] # Transfers IN
        - sum{to in L1: to != j1}transfer1['eSB',j1,to] # Teams transferred OUT
        + newhire1['eSB',j1];

# s.t. Team_SF_equal_SBc{j1 in CL[1] inter L1}:     
#         sum{from in EL[1] inter L1: from != j1}transfer1['eSF',from,j1] # Transfers IN        
#         + newhire1['eSF',j1] =    
#         + sum{from in EL[1] inter L1: from != j1}transfer1['eSB',from,j1] # Transfers IN        
#         + newhire1['eSB',j1];

# ########################################################################
# # Result eSF = Result eSB (CNES + Transfers IN - transferred OUT + new hire)
# # >> ATENÇÃO:  O problema fica muito difícil, mas TEM SOLUÇÃO!
# ########################################################################
# s.t. Team_SF_equal_SBe{j1 in EL[1] inter L1}: 
#     CNES1['eSF',j1] 
#         + sum{from in EL[1] inter L1: from != j1}transfer1['eSF',from,j1] # Transfers IN
#         - sum{to in L1: to != j1}transfer1['eSF',j1,to] # Teams transferred OUT
#         + newhire1['eSF',j1] - surplus1['eSF',j1] + deficit1['eSF',j1] =
#     CNES1['eSB',j1] 
#         + sum{from in EL[1] inter L1: from != j1}transfer1['eSB',from,j1] # Transfers IN
#         - sum{to in L1: to != j1}transfer1['eSB',j1,to] # Teams transferred OUT
#         + newhire1['eSB',j1] - surplus1['eSB',j1] + deficit1['eSB',j1];

s.t. Team_SF_equal_SBc{j1 in CL[1] inter L1}:     
        sum{from in EL[1] inter L1: from != j1}transfer1['eSF',from,j1] # Transfers IN        
        + newhire1['eSF',j1] - surplus1['eSF',j1] + deficit1['eSF',j1] =    
        + sum{from in EL[1] inter L1: from != j1}transfer1['eSB',from,j1] # Transfers IN        
        + newhire1['eSB',j1] - surplus1['eSB',j1] + deficit1['eSB',j1];


# We can not transfer OUT and Hire teams
# Constraints for Level 1 (PHC)
#################################################
# PREVENT TRANSFER-OUT + HIRE-BACK PATTERN
#################################################
# If location j transfers OUT team e, it should NOT hire new team e
# Instead, hire directly at the destination
# Prevents: PHC1→PHC10 (transfer) + hire at PHC1
# Enforces: hire at PHC10 directly
s.t. DetectTransferOut1a{e1 in E[1], j1 in EL[1] inter L1}:
    # sum{to in L1: to != j1}transfer1[e1,j1,to] >= 0.01 * HasTransferOut1[e1,j1];
    sum{to in L1: to != j1}transfer1[e1,j1,to] >= HasTransferOut1[e1,j1];

s.t. DetectTransferOut1b{e1 in E[1], j1 in EL[1] inter L1}:
    sum{to in L1: to != j1}transfer1[e1,j1,to] <= CNES1[e1,j1] * HasTransferOut1[e1,j1];

s.t. NoHireIfTransferOut1{e1 in E[1], j1 in EL[1] inter L1}:
    newhire1[e1,j1] <= MAX_NEW_HIRE1[e1,j1] * (1 - HasTransferOut1[e1,j1]);


#################################################
# TEAM BALANCE CONSTRAINTS - LEVEL 2 (SHC)
#################################################
# # CNES (existente) - Necessário + Transferências OUT - Transferências IN + Novas Contratações = Excesso - Déficit
# s.t. TeamBalance2e{j2 in EL[2] inter L2, e2 in E[2]}:
#     CNES2[e2,j2] # Existing teams
#     # Required teams based on patient flow    
#     - (sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])*MS2[e2]
#     + sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
#     - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
#     + newhire2[e2,j2]
#     = surplus2[e2,j2] - deficit2[e2,j2];

s.t. TeamBalance2e{j2 in EL[2] inter L2, e2 in E[2]}:
    # All flow coefficients = 1  (MS2 × POP_PER_TEAM = 1)
    CNES2[e2,j2]
    - (sum{i  in I:  (i,j2)  in Link02} (u0_2[i,j2]  + ut2[i,j2])   
    + sum{j1 in L1: (j1,j2) in Link12}  u1_2[j1,j2]                 
    + sum{j3 in L3: (j3,j2) in Link32}  u3_2[j3,j2]) * (1/POP_PER_TEAM) 
    + sum{from in EL[2] inter L2: from != j2} transfer2[e2,from,j2]
    - sum{to   in L2:             to   != j2} transfer2[e2,j2,to]
    + newhire2[e2,j2]
    = (surplus2[e2,j2] - deficit2[e2,j2]);

# s.t. TeamBalance2e{j2 in EL[2] inter L2, e2 in E[2]}:
#     # All flow coefficients = 1  (MS2 × POP_PER_TEAM = 1)
#     POP_PER_TEAM * CNES2[e2,j2]
#     - sum{i  in I:  (i,j2)  in Link02} (u0_2[i,j2]  + ut2[i,j2]) #* (1/POP_PER_TEAM) # coeff = 1
#     - sum{j1 in L1: (j1,j2) in Link12}  u1_2[j1,j2]              #* (1/POP_PER_TEAM)  # coeff = 1
#     - sum{j3 in L3: (j3,j2) in Link32}  u3_2[j3,j2]              #* (1/POP_PER_TEAM) # coeff = 1
#     + POP_PER_TEAM * sum{from in EL[2] inter L2: from != j2} transfer2[e2,from,j2]
#     - POP_PER_TEAM * sum{to   in L2:             to   != j2} transfer2[e2,j2,to]
#     + POP_PER_TEAM * newhire2[e2,j2]
#     = POP_PER_TEAM * (surplus2[e2,j2] - deficit2[e2,j2]);


# s.t. TeamBalance2c{j2 in CL[2] inter L2, e2 in E[2]}:
#     # Required teams based on patient flow 
#     - (sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])*MS2[e2]
#     + sum{from in EL[2] inter L2}transfer2[e2,from,j2] # Teams transferred IN
#     + newhire2[e2,j2]
#     = surplus2[e2,j2] - deficit2[e2,j2];

s.t. TeamBalance2c{j2 in CL[2] inter L2, e2 in E[2]}:
    - (sum{i  in I:  (i,j2)  in Link02} (u0_2[i,j2]  + ut2[i,j2]) 
    + sum{j1 in L1: (j1,j2) in Link12}  u1_2[j1,j2]              
    + sum{j3 in L3: (j3,j2) in Link32}  u3_2[j3,j2] ) * (1/POP_PER_TEAM)
    + sum{from in EL[2] inter L2} transfer2[e2,from,j2]
    + newhire2[e2,j2]
    = (surplus2[e2,j2] - deficit2[e2,j2]);

# s.t. TeamBalance2c{j2 in CL[2] inter L2, e2 in E[2]}:
#     - sum{i  in I:  (i,j2)  in Link02} (u0_2[i,j2]  + ut2[i,j2]) #* (1/POP_PER_TEAM)
#     - sum{j1 in L1: (j1,j2) in Link12}  u1_2[j1,j2]              #* (1/POP_PER_TEAM) 
#     - sum{j3 in L3: (j3,j2) in Link32}  u3_2[j3,j2]              #* (1/POP_PER_TEAM)
#     + POP_PER_TEAM * sum{from in EL[2] inter L2} transfer2[e2,from,j2]
#     + POP_PER_TEAM * newhire2[e2,j2]
#     = POP_PER_TEAM * (surplus2[e2,j2] - deficit2[e2,j2]);

s.t. SurplusLimit2{e2 in E[2], j2 in EL[2] inter L2}:
    surplus2[e2,j2] <= CNES2[e2,j2];

# Teams transferred OUT <= CNES
s.t. TransfOut2_lt_CNES{e2 in E[2], j2 in EL[2], to in L2: to != j2}: transfer2[e2,j2,to] <= CNES2[e2,j2]; 


# Constraints for Level 2 (SHC)
s.t. DetectTransferOut2a{e2 in E[2], j2 in EL[2] inter L2}:
    sum{to in L2: to != j2}transfer2[e2,j2,to] >= HasTransferOut2[e2,j2];

s.t. DetectTransferOut2b{e2 in E[2], j2 in EL[2] inter L2}:
    sum{to in L2: to != j2}transfer2[e2,j2,to] <= CNES2[e2,j2] * HasTransferOut2[e2,j2];

s.t. NoHireIfTransferOut2{e2 in E[2], j2 in EL[2] inter L2}:
    newhire2[e2,j2] <= MAX_NEW_HIRE2[e2,j2] * (1 - HasTransferOut2[e2,j2]);


#################################################
# TEAM BALANCE CONSTRAINTS - LEVEL 3 (THC)
#################################################
# # CNES (existente) - Necessário + Transferências OUT - Transferências IN + Novas Contratações = Excesso - Déficit
# s.t. TeamBalance3e{j3 in EL[3] inter L3, e3 in E[3]}:
#     CNES3[e3,j3] # Existing teams
#     # Required teams based on patient flow 
#     - (sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])*MS3[e3]
#     + sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
#     - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
#     + newhire3[e3,j3]
#     = surplus3[e3,j3] - deficit3[e3,j3];

s.t. TeamBalance3e{j3 in EL[3] inter L3, e3 in E[3]}:
    CNES3[e3,j3]
    - (sum{i  in I:  (i,j3)  in Link03} (u0_3[i,j3]  + ut3[i,j3])
    + sum{j1 in L1: (j1,j3) in Link13}  u1_3[j1,j3]              
    + sum{j2 in L2: (j2,j3) in Link23}  u2_3[j2,j3]) * (1/POP_PER_TEAM)
    + sum{from in EL[3] inter L3: from != j3} transfer3[e3,from,j3]
    - sum{to   in L3:             to   != j3} transfer3[e3,j3,to]
    + newhire3[e3,j3]
    = (surplus3[e3,j3] - deficit3[e3,j3]);

# s.t. TeamBalance3e{j3 in EL[3] inter L3, e3 in E[3]}:
#     POP_PER_TEAM * CNES3[e3,j3]
#     - sum{i  in I:  (i,j3)  in Link03} (u0_3[i,j3]  + ut3[i,j3]) #* (1/POP_PER_TEAM)
#     - sum{j1 in L1: (j1,j3) in Link13}  u1_3[j1,j3]              #* (1/POP_PER_TEAM)
#     - sum{j2 in L2: (j2,j3) in Link23}  u2_3[j2,j3]              #* (1/POP_PER_TEAM)
#     + POP_PER_TEAM * sum{from in EL[3] inter L3: from != j3} transfer3[e3,from,j3]
#     - POP_PER_TEAM * sum{to   in L3:             to   != j3} transfer3[e3,j3,to]
#     + POP_PER_TEAM * newhire3[e3,j3]
#     = POP_PER_TEAM * (surplus3[e3,j3] - deficit3[e3,j3]);

    

    

# s.t. TeamBalance3c{j3 in CL[3] inter L3, e3 in E[3]}: 
#     # Required teams based on patient flow 
#     - (sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])*MS3[e3]
#     + sum{from in EL[3] inter L3}transfer3[e3,from,j3] # Teams transferred IN
#     + newhire3[e3,j3]
#     = surplus3[e3,j3] - deficit3[e3,j3];

s.t. TeamBalance3c{j3 in CL[3] inter L3, e3 in E[3]}:
    # BUG FIX: flow terms must be divided by POP_PER_TEAM (consistent with TeamBalance2c
    # and TeamBalance3e). Without this, flows are in population units but transfers/newhire
    # are in team units — dimensionally inconsistent, giving a wildly wrong balance.
    - (sum{i  in I:  (i,j3)  in Link03} (u0_3[i,j3]  + ut3[i,j3])
    + sum{j1 in L1: (j1,j3) in Link13}  u1_3[j1,j3]
    + sum{j2 in L2: (j2,j3) in Link23}  u2_3[j2,j3]) * (1/POP_PER_TEAM)
    + sum{from in EL[3] inter L3} transfer3[e3,from,j3]
    + newhire3[e3,j3]
    = (surplus3[e3,j3] - deficit3[e3,j3]);

# s.t. TeamBalance3c{j3 in CL[3] inter L3, e3 in E[3]}:
#     - sum{i  in I:  (i,j3)  in Link03} (u0_3[i,j3]  + ut3[i,j3])
#     - sum{j1 in L1: (j1,j3) in Link13}  u1_3[j1,j3]
#     - sum{j2 in L2: (j2,j3) in Link23}  u2_3[j2,j3]
#     + POP_PER_TEAM * sum{from in EL[3] inter L3} transfer3[e3,from,j3]
#     + POP_PER_TEAM * newhire3[e3,j3]
#     = POP_PER_TEAM * (surplus3[e3,j3] - deficit3[e3,j3]);

s.t. SurplusLimit3{e3 in E[3], j3 in EL[3] inter L3}:
    surplus3[e3,j3] <= CNES3[e3,j3];

# Teams transferred OUT <= CNES
s.t. TransfOut3_lt_CNES{e3 in E[3], j3 in EL[3], to in L3: to != j3}: transfer3[e3,j3,to] <= CNES3[e3,j3]; 


# Constraints for Level 3 (THC)
s.t. DetectTransferOut3a{e3 in E[3], j3 in EL[3] inter L3}:
    sum{to in L3: to != j3}transfer3[e3,j3,to] >= HasTransferOut3[e3,j3];

s.t. DetectTransferOut3b{e3 in E[3], j3 in EL[3] inter L3}:
    sum{to in L3: to != j3}transfer3[e3,j3,to] <= CNES3[e3,j3] * HasTransferOut3[e3,j3];

s.t. NoHireIfTransferOut3{e3 in E[3], j3 in EL[3] inter L3}:
    newhire3[e3,j3] <= MAX_NEW_HIRE3[e3,j3] * (1 - HasTransferOut3[e3,j3]);

#################################################
# CAPACITY CONSTRAINTS
#################################################
s.t. ExtraSizeOnlyIfOpen1_Strong{j1 in L1}:
    extra_size1[j1] <= (5 - SIZE[j1]) * y1[j1];

# Existing locations — capacity is base C1[j1] plus any approved expansion
s.t. R6e{j1 in EL[1] inter L1}: 
    sum{i in I: (i,j1) in Link01}u0_1[i,j1]                   # Home → L1
    + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{i in I: (i,j1) in Link01} ut1[i,j1]
    <= C1[j1]; # + extra_size1[j1]*POP_PER_TEAM;             # expandable capacity

s.t. R7e{j2 in EL[2] inter L2}: 
    sum{i in I: (i,j2) in Link02}u0_2[i,j2] 
    + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
    + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]
    + sum{i in I: (i,j2) in Link02} ut2[i,j2] <= C2[j2];

s.t. R8e{j3 in EL[3] inter L3}: 
    sum{i in I: (i,j3) in Link03} u0_3[i,j3] 
    + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
    + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]
    + sum{i in I: (i,j3) in Link03} ut3[i,j3] <= C3[j3];

s.t. R9e{j1 in EL[1] inter L1}: 
    sum{i in I: (j1,i) in Link10}u1_0[j1,i]                   # L1 → Home
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]              # L1 → L2
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3]              # L1 → L3
    <= C1[j1]; # + extra_size1[j1]*POP_PER_TEAM;               # (expandable)

s.t. R10e{j2 in EL[2] inter L2}: 
    sum{i in I: (j2,i) in Link20}u2_0[j2,i]                   # L2 → Home
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3] <= C2[j2];   # L2 → L3

s.t. R11e{j3 in EL[3] inter L3}: 
    sum{i in I: (j3,i) in Link30}u3_0[j3,i]                   # L3 → Home
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2] <= C3[j3];   # L3 → L2
     

# Candidate locations (activated only if used)
s.t. R6c{j1 in CL[1] inter L1}: 
    sum{i in I: (i,j1) in Link01}u0_1[i,j1]                   # Home → L1
    + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{i in I: (i,j1) in Link01} ut1[i,j1] 
    <= C1[j1]*y1[j1] + extra_size1[j1]*POP_PER_TEAM;

s.t. R7c{j2 in CL[2] inter L2}: 
    sum{i in I: (i,j2) in Link02}u0_2[i,j2] 
    + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
    + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]
    + sum{i in I: (i,j2) in Link02} ut2[i,j2] <= C2[j2]*y2[j2];

s.t. R8c{j3 in CL[3] inter L3}: 
    sum{i in I: (i,j3) in Link03} u0_3[i,j3] 
    + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
    + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]
    + sum{i in I: (i,j3) in Link03} ut3[i,j3] <= C3[j3]*y3[j3];

s.t. R9c{j1 in CL[1] inter L1}: 
    sum{i in I: (j1,i) in Link10}u1_0[j1,i]                   # L1 → Home
    + sum{j2 in L2: (j1,j2) in Link12}u1_2[j1,j2]              # L1 → L2
    + sum{j3 in L3: (j1,j3) in Link13}u1_3[j1,j3]              # L1 → L3
    <= C1[j1]*y1[j1] + extra_size1[j1]*POP_PER_TEAM;   

s.t. R10c{j2 in CL[2] inter L2}: 
    sum{i in I: (j2,i) in Link20}u2_0[j2,i]                   # L2 → Home
    + sum{j1 in L1: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j2,j3) in Link23}u2_3[j2,j3] <= C2[j2]*y2[j2];   # L2 → L3

s.t. R11c{j3 in CL[3] inter L3}: 
    sum{i in I: (j3,i) in Link30}u3_0[j3,i]                   # L3 → Home
    + sum{j1 in L1: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{j2 in L2: (j3,j2) in Link32}u3_2[j3,j2] <= C3[j3]*y3[j3];   # L3 → L2

# Budget-adjusted maximum new facilities
s.t. R12c:  sum{j1 in CL[1] inter L1}y1[j1] <= MaxNewPHC;
s.t. R13c: sum{j2 in CL[2] inter L2}y2[j2] <= MaxNewSHC;
s.t. R14c: sum{j3 in CL[3] inter L3}y3[j3] <= MaxNewTHC;


# s.t. APSCost: Total_Costs_APS = 
#     # Existing facilities cost    
#     sum{j1 in EL[1] inter L1}FC1[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
#     + sum{j2 in EL[2] inter L2}FC2[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
#     + sum{j3 in EL[3] inter L3}FC3[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e]
#     # Existing PHC expansion cost (annualised investment + incremental operating cost)
#     + sum{j1 in EL[1] inter L1}(IA1_exp_unit + FC1_exp_unit)*extra_size1[j1]
#     # New facilities fixed cost    
#     + sum{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1])*y1[j1] 
#     + sum{j2 in CL[2] inter L2}(FC2[j2]+IA2[j2])*y2[j2] 
#     + sum{j3 in CL[3] inter L3}(FC3[j3]+IA3[j3])*y3[j3]
    
#     # # New staff cost
#     # + sum{j1 in L1, c1 in E[1]}CE1[c1]*newhire1[c1,j1] 
#     # + sum{j2 in L2, c2 in E[2]}CE2[c2]*newhire2[c2,j2] 
#     # + sum{j3 in L3, c3 in E[3]}CE3[c3]*newhire3[c3,j3]
#     + sum{j1 in EL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
#     - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
#     + newhire1[e1,j1])  # New teams hired
#     + sum{j1 in CL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN    
#     + newhire1[e1,j1])  # New teams hired

#     + sum{j2 in EL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
#     - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
#     + newhire2[e2,j2]) # New teams hired
#     + sum{j2 in CL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN    
#     + newhire2[e2,j2]) # New teams hired
	
#     + sum{j3 in EL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
#     - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
#     + newhire3[e3,j3]) # New teams hired
#     + sum{j3 in CL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN    
#     + newhire3[e3,j3]) # New teams hired

#     # Variable costs
#     + sum{j1 in L1}VC1[j1]*(sum{i in I: (i,j1) in Link01}u0_1[i,j1]                   # Home → L1
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
#     + sum{i in I: (i,j1) in Link01} ut1[i,j1])                # Telehealth in L1
#     + sum{j2 in L2}VC2[j2]*(sum{i in I: (i,j2) in Link02}u0_2[i,j2] 
#     + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
#     + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]
#     + sum{i in I: (i,j2) in Link02} ut2[i,j2])
#     + sum{j3 in L3}VC3[j3]*(sum{i in I: (i,j3) in Link03} u0_3[i,j3] 
#     + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
#     + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]
#     + sum{i in I: (i,j3) in Link03} ut3[i,j3])
#     # NO patients Transportation costs  
#     # Re-assignment costs:  Transfer IN
#     + sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}
#          RC1[e1]*(DL1[from,to]/1000)*transfer1[e1,from,to]
#     + sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}
#          RC2[e2]*(DL2[from,to]/1000)*transfer2[e2,from,to]
#     + sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}
#          RC3[e3]*(DL3[from,to]/1000)*transfer3[e3,from,to]
#     # Re-assignment costs:  Transfer OUT
#     + sum{e1 in E[1], j1 in EL[1] inter L1, to in L1: to != j1}
#         RC1[e1]*(DL1[j1,to]/1000)*transfer1[e1,j1,to]
#     + sum{e2 in E[2], j2 in EL[2] inter L2, to in L2: to != j2}
#         RC2[e2]*(DL2[j2,to]/1000)*transfer2[e2,j2,to]
#     + sum{e3 in E[3], j3 in EL[3] inter L3, to in L3: to != j3}
#         RC3[e3]*(DL3[j3,to]/1000)*transfer3[e3,j3,to]
#          ;
#     # NO Penalty for surplus or deficit

s.t. APSCost: Total_Costs_APS_s = 
    # Existing facilities cost    
    sum{j1 in EL[1] inter L1}FC1_s[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1_s[e]  
    + sum{j2 in EL[2] inter L2}FC2_s[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2_s[e] 
    + sum{j3 in EL[3] inter L3}FC3_s[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3_s[e]
    # sum{j1 in EL[1] inter L1}FC1_s[j1]*y1[j1] 
    # + sum{j2 in EL[2] inter L2}FC2_s[j2]*y2[j2]
    # + sum{j3 in EL[3] inter L3}FC3_s[j3]*y3[j3]
    # Existing PHC expansion cost (annualised investment + incremental operating cost)
    # + sum{j1 in EL[1] inter L1}(IA1_exp_unit_s + FC1_exp_unit_s)*extra_size1[j1]
    + sum{j1 in L[1] inter L1}(IA1_exp_unit_s + FC1_exp_unit_s)*extra_size1[j1]
    # New facilities fixed cost    
    + sum{j1 in CL[1] inter L1}(FC1_s[j1]+IA1_s[j1])*y1[j1] 
    + sum{j2 in CL[2] inter L2}(FC2_s[j2]+IA2_s[j2])*y2[j2] 
    + sum{j3 in CL[3] inter L3}(FC3_s[j3]+IA3_s[j3])*y3[j3]
    
    # # New staff cost
    # + sum{j1 in L1, c1 in E[1]}CE1[c1]*newhire1[c1,j1] 
    # + sum{j2 in L2, c2 in E[2]}CE2[c2]*newhire2[c2,j2] 
    # + sum{j3 in L3, c3 in E[3]}CE3[c3]*newhire3[c3,j3]
    + sum{j1 in EL[1], e1 in E[1]}CE1_s[e1]*(
	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
    - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
    + newhire1[e1,j1])  # New teams hired
    + sum{j1 in CL[1], e1 in E[1]}CE1_s[e1]*(
	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN    
    + newhire1[e1,j1])  # New teams hired

    + sum{j2 in EL[2], e2 in E[2]}CE2_s[e2]*(
	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
    - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
    + newhire2[e2,j2]) # New teams hired
    + sum{j2 in CL[2], e2 in E[2]}CE2_s[e2]*(
	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN    
    + newhire2[e2,j2]) # New teams hired
	
    + sum{j3 in EL[3], e3 in E[3]}CE3_s[e3]*(
	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
    - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
    + newhire3[e3,j3]) # New teams hired
    + sum{j3 in CL[3], e3 in E[3]}CE3_s[e3]*(
	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN    
    + newhire3[e3,j3]) # New teams hired

    # Variable costs
    + sum{j1 in L1}VC1_s[j1]*(sum{i in I: (i,j1) in Link01}u0_1[i,j1]                   # Home → L1
    + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{i in I: (i,j1) in Link01} ut1[i,j1])                # Telehealth in L1
    + sum{j2 in L2}VC2_s[j2]*(sum{i in I: (i,j2) in Link02}u0_2[i,j2] 
    + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
    + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]
    + sum{i in I: (i,j2) in Link02} ut2[i,j2])
    + sum{j3 in L3}VC3_s[j3]*(sum{i in I: (i,j3) in Link03} u0_3[i,j3] 
    + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
    + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]
    + sum{i in I: (i,j3) in Link03} ut3[i,j3])
    # NO patients Transportation costs  
    # Re-assignment costs:  Transfer IN
    + sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}
         RC1_s[e1]*(DL1_KM[from,to])*transfer1[e1,from,to]
    + sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}
         RC2_s[e2]*(DL2_KM[from,to])*transfer2[e2,from,to]
    + sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}
         RC3_s[e3]*(DL3_KM[from,to])*transfer3[e3,from,to]
    # Re-assignment costs:  Transfer OUT
    + sum{e1 in E[1], j1 in EL[1] inter L1, to in L1: to != j1}
        RC1_s[e1]*(DL1_KM[j1,to])*transfer1[e1,j1,to]
    + sum{e2 in E[2], j2 in EL[2] inter L2, to in L2: to != j2}
        RC2_s[e2]*(DL2_KM[j2,to])*transfer2[e2,j2,to]
    + sum{e3 in E[3], j3 in EL[3] inter L3, to in L3: to != j3}
        RC3_s[e3]*(DL3_KM[j3,to])*transfer3[e3,j3,to]
         ;
    # NO Penalty for surplus or deficit


# Overall budget constraint
# s.t. APSBudgetConstraint:  Total_Costs_APS <= BUDGET;
s.t. APSBudgetConstraint: Total_Costs_APS_s <= BUDGET_s + budget_slack;

#################################################
# OBJECTIVE FUNCTION
#################################################

# minimize Total_Costs:
minimize Total_Costs_s:
    # Patient transportation cost
      sum{i in I, j1 in L1: (i,j1) in Link01}TC0_1_s[i,j1]*u0_1[i,j1] 
    + sum{i in I, j2 in L2: (i,j2) in Link02}TC0_2_s[i,j2]*u0_2[i,j2] 
    + sum{i in I, j3 in L3: (i,j3) in Link03}TC0_3_s[i,j3]*u0_3[i,j3]     
    + sum{j1 in L1, j2 in L2: (j1,j2) in Link12}TC1_2_s[j1,j2]*u1_2[j1,j2]  
    + sum{j1 in L1, j3 in L3: (j1,j3) in Link13}TC1_3_s[j1,j3]*u1_3[j1,j3]  
    + sum{j2 in L2, j3 in L3: (j2,j3) in Link23}TC2_3_s[j2,j3]*u2_3[j2,j3] 
    # Cost of existing units
    # + sum{j1 in EL[1] inter L1}FC1_s[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1_s[e]  
    # + sum{j2 in EL[2] inter L2}FC2_s[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2_s[e] 
    # + sum{j3 in EL[3] inter L3}FC3_s[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3_s[e]
    + sum{j1 in EL[1] inter L1}FC1_s[j1]*y1[j1] 
    + sum{j2 in EL[2] inter L2}FC2_s[j2]*y2[j2] 
    + sum{j3 in EL[3] inter L3}FC3_s[j3]*y3[j3] 
    # Existing PHC expansion cost (annualised investment + incremental operating cost)
    # + sum{j1 in EL[1] inter L1}(IA1_exp_unit_s + FC1_exp_unit_s)*extra_size1[j1]
    + sum{j1 in L[1] inter L1}(IA1_exp_unit_s + FC1_exp_unit_s)*extra_size1[j1]
    # New unit cost
    + sum{j1 in CL[1] inter L1}(FC1_s[j1]+IA1_s[j1])*y1[j1] 
    + sum{j2 in CL[2] inter L2}(FC2_s[j2]+IA2_s[j2])*y2[j2] 
    + sum{j3 in CL[3] inter L3}(FC3_s[j3]+IA3_s[j3])*y3[j3]    
    # Cost of NEW teams hired    
    # + sum{j1 in L1, e1 in E[1]}CE1[e1]*newhire1[e1,j1]
    # + sum{j2 in L2, e2 in E[2]}CE2[e2]*newhire2[e2,j2]
    # + sum{j3 in L3, e3 in E[3]}CE3[e3]*newhire3[e3,j3]
    + sum{j1 in EL[1], e1 in E[1]}CE1_s[e1]*(
	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
    - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
    + newhire1[e1,j1])  # New teams hired
    + sum{j1 in CL[1], e1 in E[1]}CE1_s[e1]*(
	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN    
    + newhire1[e1,j1])  # New teams hired

    + sum{j2 in EL[2], e2 in E[2]}CE2_s[e2]*(
	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
    - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
    + newhire2[e2,j2]) # New teams hired
    + sum{j2 in CL[2], e2 in E[2]}CE2_s[e2]*(
	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN    
    + newhire2[e2,j2]) # New teams hired
	
    + sum{j3 in EL[3], e3 in E[3]}CE3_s[e3]*(
	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
    - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
    + newhire3[e3,j3]) # New teams hired
    + sum{j3 in CL[3], e3 in E[3]}CE3_s[e3]*(
	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN    
    + newhire3[e3,j3]) # New teams hired

    # Variable cost per patient
    + sum{j1 in L1}VC1_s[j1]*(sum{i in I: (i,j1) in Link01}u0_1[i,j1]  # Home → L1
    + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
    + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
    + sum{i in I: (i,j1) in Link01} ut1[i,j1])                # Telehealth in L1
    + sum{j2 in L2}VC2_s[j2]*(sum{i in I: (i,j2) in Link02}u0_2[i,j2] # Home → L2
    + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2]              # L1 → L2
    + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]              # L3 → L2
    + sum{i in I: (i,j2) in Link02} ut2[i,j2])                # Telehealth in L2
    + sum{j3 in L3}VC3_s[j3]*(sum{i in I: (i,j3) in Link03} u0_3[i,j3] # Home → L3
    + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3]              # L1 → L3
    + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]              # L2 → L2
    + sum{i in I: (i,j3) in Link03} ut3[i,j3])                # Telehealth in L3  

    # Re-assignment costs:  Transfer IN
    + sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}
         RC1_s[e1]*(DL1_KM[from,to])*transfer1[e1,from,to]
    + sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}
         RC2_s[e2]*(DL2_KM[from,to])*transfer2[e2,from,to]
    + sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}
         RC3_s[e3]*(DL3_KM[from,to])*transfer3[e3,from,to]
    # Re-assignment costs:  Transfer OUT
    + sum{e1 in E[1], j1 in EL[1] inter L1, to in L1: to != j1}
        RC1_s[e1]*(DL1_KM[j1,to])*transfer1[e1,j1,to]
    + sum{e2 in E[2], j2 in EL[2] inter L2, to in L2: to != j2}
        RC2_s[e2]*(DL2_KM[j2,to])*transfer2[e2,j2,to]
    + sum{e3 in E[3], j3 in EL[3] inter L3, to in L3: to != j3}
        RC3_s[e3]*(DL3_KM[j3,to])*transfer3[e3,j3,to]
    

    # Penalty for surplus or deficit 
    + sum{e1 in E[1], j1 in L1}P1_s*surplus1[e1,j1] 
    + sum{e2 in E[2], j2 in L2}P2_s*surplus2[e2,j2] 
    + sum{e3 in E[3], j3 in L3}P3_s*surplus3[e3,j3] 
    + sum{e1 in E[1], j1 in L1}P1_d*deficit1[e1,j1] 
    + sum{e2 in E[2], j2 in L2}P2_d*deficit2[e2,j2] 
    + sum{e3 in E[3], j3 in L3}P3_d*deficit3[e3,j3]

    # --- BUDGET OVERRUN PENALTY ---
    # Must appear AFTER all other terms to maintain objective scale.
    + BUDGET_OVERRUN_MULT * budget_slack      
    # + sum{i in I}USERVED_PENALTY * unserved_slack[i]
    ;








# #######################################################################
# solve;


# #################################################
# # OUTPUT REPORTS
# #################################################

# printf: "\n========================================\n";
# printf: "Health Care Plan with Team Reallocation\n";
# printf: "========================================\n";
# printf: "Logist cost:\t\t$%10.2f\n", 
#       sum{i in I, j1 in L1: (i,j1) in Link01}TC0_1[i,j1]*u0_1[i,j1] 
#     + sum{i in I, j2 in L2: (i,j2) in Link02}TC0_2[i,j2]*u0_2[i,j2] 
#     + sum{i in I, j3 in L3: (i,j3) in Link03}TC0_3[i,j3]*u0_3[i,j3]     
#     + sum{j1 in L1, j2 in L2: (j1,j2) in Link12}TC1_2[j1,j2]*u1_2[j1,j2]  
#     + sum{j1 in L1, j3 in L3: (j1,j3) in Link13}TC1_3[j1,j3]*u1_3[j1,j3]  
#     + sum{j2 in L2, j3 in L3: (j2,j3) in Link23}TC2_3[j2,j3]*u2_3[j2,j3];
# printf: "Fixed cost [Existing]:\t$%10.2f\n", 
#       sum{j1 in EL[1] inter L1}FC1[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
#     + sum{j2 in EL[2] inter L2}FC2[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
#     + sum{j3 in EL[3] inter L3}FC3[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e];
# printf: "Expansion cost [Existing]:\t$%10.2f\n", 
#       sum{j1 in EL[1] inter L1}(IA1_exp_unit + FC1_exp_unit)*extra_size1[j1];
# printf: "Fixed cost [Candidate]:\t$%10.2f\n", 
#       sum{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1])*y1[j1] 
#     + sum{j2 in CL[2] inter L2}(FC2[j2]+IA2[j2])*y2[j2] 
#     + sum{j3 in CL[3] inter L3}(FC3[j3]+IA3[j3])*y3[j3];
# printf: "Expansion cost [Candidate]:\t$%10.2f\n", 
#       sum{j1 in CL[1] inter L1}(IA1_exp_unit + FC1_exp_unit)*extra_size1[j1];
# printf: "New team cost:\t\t$%10.2f\n", 
#     sum{j1 in EL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
#     - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
#     + newhire1[e1,j1])  # New teams hired
#     + sum{j1 in CL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN    
#     + newhire1[e1,j1])  # New teams hired

#     + sum{j2 in EL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
#     - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
#     + newhire2[e2,j2]) # New teams hired
#     + sum{j2 in CL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN    
#     + newhire2[e2,j2]) # New teams hired
	
#     + sum{j3 in EL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
#     - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
#     + newhire3[e3,j3]) # New teams hired
#     + sum{j3 in CL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN    
#     + newhire3[e3,j3]);

# printf: "Team relocation cost:\t$%10.2f\n",
#     # Re-assignment costs:  Transfer IN
#     sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}
#          RC1[e1]*(DL1_KM[from,to])*transfer1[e1,from,to]
#     + sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}
#          RC2[e2]*(DL2_KM[from,to])*transfer2[e2,from,to]
#     + sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}
#          RC3[e3]*(DL3_KM[from,to])*transfer3[e3,from,to]
#     # Re-assignment costs:  Transfer OUT
#     + sum{e1 in E[1], j1 in EL[1] inter L1, to in L1: to != j1}
#         RC1[e1]*(DL1_KM[j1,to])*transfer1[e1,j1,to]
#     + sum{e2 in E[2], j2 in EL[2] inter L2, to in L2: to != j2}
#         RC2[e2]*(DL2_KM[j2,to])*transfer2[e2,j2,to]
#     + sum{e3 in E[3], j3 in EL[3] inter L3, to in L3: to != j3}
#         RC3[e3]*(DL3_KM[j3,to])*transfer3[e3,j3,to];
# printf: "Variable Cost:\t\t$%10.2f\n",
#     # Variable cost per patient
#     sum{j1 in L1}VC1[j1]*(sum{i in I: (i,j1) in Link01}u0_1[i,j1]  # Home → L1
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
#     + sum{i in I: (i,j1) in Link01} ut1[i,j1])                # Telehealth in L1
#     + sum{j2 in L2}VC2[j2]*(sum{i in I: (i,j2) in Link02}u0_2[i,j2] # Home → L2
#     + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2]              # L1 → L2
#     + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]              # L3 → L2
#     + sum{i in I: (i,j2) in Link02} ut2[i,j2])                # Telehealth in L2
#     + sum{j3 in L3}VC3[j3]*(sum{i in I: (i,j3) in Link03} u0_3[i,j3] # Home → L3
#     + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3]              # L1 → L3
#     + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]              # L2 → L2
#     + sum{i in I: (i,j3) in Link03} ut3[i,j3]);                # Telehealth in L3 
# printf: "========================================\n";
# printf: "Total     Cost:\t\t$%10.2f\n", 
# Total_Costs_s * COST_SCALE
# # If GLPK or Highs...
# # + (sum{j1 in EL[1] inter L1}FC1[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
# #     + sum{j2 in EL[2] inter L2}FC2[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
# #     + sum{j3 in EL[3] inter L3}FC3[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e])
# + (sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
#    + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
#    + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e])
# - (# Penalty for surplus or deficit 
#     sum{e1 in E[1], j1 in L1}P1_s*surplus1[e1,j1] 
#     + sum{e2 in E[2], j2 in L2}P2_s*surplus2[e2,j2] 
#     + sum{e3 in E[3], j3 in L3}P3_s*surplus3[e3,j3] 
#     + sum{e1 in E[1], j1 in L1}P1_d*deficit1[e1,j1] 
#     + sum{e2 in E[2], j2 in L2}P2_d*deficit2[e2,j2] 
#     + sum{e3 in E[3], j3 in L3}P3_d*deficit3[e3,j3]) * COST_SCALE;

# printf: "Total APS Cost:\t\t$%10.2f\n", Total_Costs_APS_s * COST_SCALE;
# printf: "Budget Limit:\t\t$%10.2f\n", BUDGET_s * COST_SCALE;
# printf: "Budget Usage:\t\t%.2f%%\n", (Total_Costs_APS_s/BUDGET_s)*100;
# printf: "Budget Overrun:\t\t$%10.2f\n", budget_slack * COST_SCALE;
# printf: "Overrun Pct:\t\t%.2f%%\n",
#     if BUDGET_s > 0 then (budget_slack / BUDGET_s) * 100 else 0;
# printf: "Effective Budget:\t$%10.2f\n", (BUDGET_s + budget_slack) * COST_SCALE;
# printf: "========================================\n";


# printf: "New Units:\tQty\tMax\tUse (%%)\n"; 
# printf: "========================================\n";
# printf: "PHC      :\t%d\t%d\t%.2f%%\n", 
# sum{j1 in CL[1] inter L1}y1[j1],
# MaxNewPHC, 
# if MaxNewPHC > 0 then ((sum{j1 in CL[1] inter L1}y1[j1])/(MaxNewPHC))*100 else 0; 
# printf: "SHC      :\t%d\t%d\t%.2f%%\n", 
# sum{j2 in CL[2] inter L2}y2[j2],
# MaxNewSHC, 
# if MaxNewSHC > 0 then ((sum{j2 in CL[2] inter L2}y2[j2])/(MaxNewSHC))*100 else 0; 
# printf: "THC      :\t%d\t%d\t%.2f%%\n", 
# sum{j3 in CL[3] inter L3}y3[j3],
# MaxNewTHC, 
# if MaxNewTHC > 0 then ((sum{j3 in CL[3] inter L3}y3[j3])/(MaxNewTHC))*100 else 0; 
# printf: "========================================\n";

# printf: "\n========================================\n";
# printf: "TEAM REALLOCATION SUMMARY\n";
# printf: "========================================\n";

# # PHC Team Transfers
# printf: "\nPHC Team Transfers:\n";
# printf: "From\t> To\t\tTeam\tQty\tDist (km)\n";
# printf: "================================================\n";
# for{e1 in E[1], from in EL[1] inter L1, to in L1: from != to and transfer1[e1,from,to] > 0.01}{
#     printf: "[%-4s]\t> [%-4s]%s\t%-4s\t%.2f\t%.2f\n", 
#         from, 
#         to, 
#         if to in CL[1] then "*" else "", 
#         e1, 
#         transfer1[e1,from,to], 
#         (DL1_KM[from,to]);
# }

# # SHC Team Transfers
# printf: "\nSHC Team Transfers:\n";
# printf: "From\t> To\t\tTeam\tQty\tDist (km)\n";
# printf: "================================================\n";
# for{e2 in E[2], from in EL[2] inter L2, to in L2: from != to and transfer2[e2,from,to] > 0.01}{
#     printf: "[%-4s]\t> [%-4s]%s\t%-4s\t%.2f\t%.2f\n", 
#         from, 
#         to,
#         if to in CL[2] then "*" else "",  
#         e2, 
#         transfer2[e2,from,to], 
#         (DL2_KM[from,to]);
# }

# # THC Team Transfers
# printf: "\nTHC Team Transfers:\n";
# printf: "From\t> To\t\tTeam\tQty\tDist (km)\n";
# printf: "================================================\n";
# for{e3 in E[3], from in EL[3] inter L3, to in L3: from != to and transfer3[e3,from,to] > 0.01}{
#     printf: "[%-4s]\t> [%-4s]%s\t%-4s\t%.2f\t%.2f\n", 
#         from, 
#         to,
#         if to in CL[3] then "*" else "", 
#         e3, 
#         transfer3[e3,from,to], 
#         (DL3_KM[from,to]);
# }

# printf: "\n================================================\n";
# printf: "NEW TEAMS HIRED\n";
# printf: "================================================\n";
# printf: "\nPHC New Hires:\n";
# printf: "Location\tTeam\tQty\n";
# printf: "================================================\n";
# for{j1 in L1, e1 in E[1]: newhire1[e1,j1] > 0.01}{
#     printf: "[%-7s]%s\t%-4s\t%.2f\n", 
#         j1, 
#         if j1 in CL[1] then "*" else "",
#         e1, 
#         newhire1[e1,j1];
# }

# printf: "\nSHC New Hires:\n";
# printf: "Location\tTeam\tQty\n";
# printf: "================================================\n";
# for{j2 in L2, e2 in E[2]: newhire2[e2,j2] > 0.01}{
#     printf: "[%-7s]%s\t%-4s\t%.2f\n", 
#         j2,
#         if j2 in CL[2] then "*" else " ",
#         e2, 
#         newhire2[e2,j2];
# }

# printf: "\nTHC New Hires:\n";
# printf: "Location\tTeam\tQty\n";
# printf: "================================================\n";
# for{j3 in L3, e3 in E[3]: newhire3[e3,j3] > 0.01}{
#     printf: "[%-7s]%s\t%-4s\t%.2f\n", 
#         j3,
#         if j3 in CL[3] then "*" else " ",
#         e3, 
#         newhire3[e3,j3];
# }

# printf: "\n========================================\n";
# printf: "TEAM BALANCE PER LOCATION\n";
# printf: "========================================\n";

# printf: "\nPHC Locations:\n";
# printf: "Loc\t\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n";
# printf: "===========================================================================\n";

# for{j1 in L1: ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1]) 
# + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
# + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])>0) or j1 in EL[1] and sum{e1 in E[1]} CNES1[e1,j1] > 0}{
#     for{e1 in E[1]}{
#         printf: "[%-7s]%s\t%-4s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j1,
#             if j1 in CL[1] then "*" else "",
#             e1,
#             if j1 in EL[1] then CNES1[e1,j1] else 0,
#             # round((sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1]) * TEAM_SCALE0_1[i,e1]
#             # + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1] * TEAM_SCALE1[e1]
#             # + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1] * TEAM_SCALE1[e1])),
#             (sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1]) * TEAM_SCALE0_1[i,e1]
#             + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1] * TEAM_SCALE1[e1]
#             + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1] * TEAM_SCALE1[e1]),
#             sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1] # Transfers IN
#             - (if j1 in EL[1] then sum{to in L1: to != j1}transfer1[e1,j1,to] else 0), # Teams transferred OUT            
#             newhire1[e1,j1],
#             (if j1 in EL[1] then CNES1[e1,j1] else 0) # Result: CNES +
#             + sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1] # Transfers IN
#             - (if j1 in EL[1] then sum{to in L1: to != j1}transfer1[e1,j1,to] else 0) # Teams transferred OUT            
#             + newhire1[e1,j1],
#             surplus1[e1,j1],
#             deficit1[e1,j1];
#     }
# }


# printf: "===========================================================================\n";
# printf: "TOTAL TEAMS PER CATEGORY\n";
# printf: "===========================================================================\n";
# printf: "Team\tRequired\tResult\n";
# for{e1 in E[1]}{
#     printf: "%-4s\t%.2f\t\t%.2f\n",
#         e1,
#         # ReqTotal[e1],
#         sum{j1 in L1} (sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1])  * TEAM_SCALE0_1[i,e1]
#             + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1]               * TEAM_SCALE1[e1]
#             + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1]               * TEAM_SCALE1[e1]),
#         # ResultTotal[e1];
#         sum{j1 in L1} ((if j1 in EL[1] then CNES1[e1,j1] else 0)
#         + sum{from in EL[1] inter L1: from != j1} transfer1[e1,from,j1]
#         - (if j1 in EL[1] then sum{to in L1: to != j1} transfer1[e1,j1,to] else 0)
#         + newhire1[e1,j1]);        
# }
# printf: "===========================================================================\n";


# printf: "\nSHC Locations:\n";
# printf: "Loc\t\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n";
# printf: "===========================================================================\n";
# for{j2 in L2: ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) 
# + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
# + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]) > 0) or j2 in EL[2] and sum{e2 in E[2]} CNES2[e2,j2] > 0}{
#     for{e2 in E[2]}{
#         printf: "[%-7s]%s\t%-4s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j2,
#             if j2 in CL[2] then "*" else "",
#             e2,
#             if j2 in EL[2] then CNES2[e2,j2] else 0, #CNES
#             (sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) 
#             + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
#             + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/POP_PER_TEAM,
#             sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Transfers IN
#             - (if j2 in EL[2] then sum{to in L2: to != j2}transfer2[e2,j2,to] else 0), # Teams transferred OUT            
#             newhire2[e2,j2],
#             (if j2 in EL[2] then CNES2[e2,j2] else 0) # CNES
#             + sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Transfers IN
#             - (if j2 in EL[2] then sum{to in L2: to != j2}transfer2[e2,j2,to] else 0) # Teams transferred OUT
#             + newhire2[e2,j2],
#             surplus2[e2,j2],
#             deficit2[e2,j2];
#     }
# }

# printf: "\nTHC Locations:\n";
# printf: "Loc\t\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n";
# printf: "===========================================================================\n";
# for{j3 in L3: ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) 
# + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
# + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]) > 0) or j3 in EL[3] and sum{e3 in E[3]} CNES3[e3,j3] > 0}{
#     for{e3 in E[3]}{
#         printf: "[%-7s]%s\t%-4s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j3,
#             if j3 in CL[3] then "*" else "",
#             e3,
#             if j3 in EL[3] then CNES3[e3,j3] else 0,
#             (sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) 
#             + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
#             + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]) / POP_PER_TEAM,
#             sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Transfers IN
#             - (if j3 in EL[3] then sum{to in L3: to != j3}transfer3[e3,j3,to] else 0), # Teams transferred OUT            
#             newhire3[e3,j3],
#             (if j3 in EL[3] then CNES3[e3,j3] else 0) # CNES
#             + sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Transfers IN
#             - (if j3 in EL[3] then sum{to in L3: to != j3}transfer3[e3,j3,to] else 0) # Teams transferred OUT
#             + newhire3[e3,j3],
#             surplus3[e3,j3],
#             deficit3[e3,j3];
#     }
# }

# printf: "\n========================================\n";
# printf: "Region:\t\t  Pop\t Flow\n"; 
# printf: "========================================\n";
# printf{i in I}: "[%-14s]: %d\t %d\n", i, 
# W[i], 
# sum{j1 in L1: (i,j1) in Link01}u0_1[i,j1] 
# + sum{j2 in L2: (i,j2) in Link02} u0_2[i,j2]
# + sum{j3 in L3: (i,j3) in Link03} u0_3[i,j3]
# + sum{j1 in L1: (i,j1) in Link01} ut1[i,j1]
# + sum{j2 in L2: (i,j2) in Link02} ut2[i,j2]
# + sum{j3 in L3: (i,j3) in Link03} ut3[i,j3];

# printf: "============================================\n";
# printf: "Reg     > PHC + SHC + THC  :(flow)\n";
# printf: "============================================\n";
# for{i in I}{
#     # PHC
#     printf "RC[%-5s]\t\t%d\tDist (km)\n", i, W[i]; 
#     for{j1 in L1: (i,j1) in Link01 and u0_1[i,j1] > 0}{
#     printf ">\tL[%-5s]\t%d\t%.2f\n", j1, u0_1[i,j1], (D0_1_KM[i,j1]);}  
#     for{j1 in L1: (i,j1) in Link01 and ut1[i,j1] > 0}{
#     printf ">\tL[%-5s] tel\t%d\n", j1, ut1[i,j1]; }
#     # SHC
#     for{j2 in L2: (i,j2) in Link02 and u0_2[i,j2] > 0}{
#     printf ">\tL[%-5s]\t%d\t%.2f\n", j2, u0_2[i,j2], (D0_2_KM[i,j2]);} 
#     for{j2 in L2: (i,j2) in Link02 and ut2[i,j2] > 0}{
#     printf ">\tL[%-5s] tel\t%d\n", j2, ut2[i,j2];}     
#     # THC
#     for{j3 in L3: (i,j3) in Link03 and u0_3[i,j3] > 0}{
#     printf ">\tL[%-5s]\t%d\t%.2f\n", j3, u0_3[i,j3], (D0_3_KM[i,j3]);} 
#     for{j3 in L3: (i,j3) in Link03 and ut3[i,j3] > 0}{
#     printf ">\tL[%-5s] tel\t%d\n", j3, ut3[i,j3];}
# }
# printf: "============================================\n";
# printf: "*tel: (telesaude, ou teleconsulta)\n";
# printf: "============================================\n";


# printf: "========================================\n";
# printf: "PHC     > Reg + SHC + THC (dest. flow)\n";
# printf: "========================================\n";
# for{j1 in L1: (sum{i in I: (i,j1) in Link01}(u0_1[i,j1] + ut1[i,j1])
# + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
# + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]) > 0}{
#     printf"PHC[%-4s] > \t : %d\t(%d + %d + %d) (Orig: Reg + SHC + THC)\n", 
#         j1, 
#         sum{i in I: (i,j1) in Link01}(u0_1[i,j1] + ut1[i,j1])
#         + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#         + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1],
#         sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ ut1[i,j1]), 
#         sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1], 
#         sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1];
#     # Reg
#     for{i in I: (j1,i) in Link10 and u1_0[j1,i] > 0}{
#     printf"\t> L[%-4s]: %d\n", i, u1_0[j1,i];} # O1_0[j1]*
#     # SHC
#     for{j2 in L2: (j1,j2) in Link12 and u1_2[j1,j2] > 0}{
#     printf"\t> L[%-4s]: %d\n", j2, u1_2[j1,j2];} # O1_2[j1]*
#     # THC
#     for{j3 in L3: (j1,j3) in Link13 and u1_3[j1,j3] > 0}{
#     printf"\t> L[%-4s]: %d\n", j3, u1_3[j1,j3];} # O1_3[j1]*
# }

# printf: "========================================\n";
# printf: "SHC     > Reg + PHC + THC (dest. flow)\n";
# printf: "========================================\n";
# for{j2 in L2: (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2])
# + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
# + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])>0}{
#     printf: "SHC[%-4s] > \t : %d\t(%d + %d + %d) (Orig: Reg + PHC + THC)\n", 
#         j2, 
#         sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2])
#         + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
#         + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2], 
#         sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]), 
#         sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2], 
#         sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2];
#     # Reg
#     for{i in I: (j2,i) in Link20 and u2_0[j2,i] > 0}{
#     printf"\t> L[%-4s]: %d\n", i, u2_0[j2,i];} 
#     # PHC
#     for{j1 in L1: (j2,j1) in Link21 and u2_1[j2,j1] > 0}{
#     printf"\t> L[%-4s]: %d\n", j1, u2_1[j2,j1];}
#     # THC
#     for{j3 in L3: (j2,j3) in Link23 and u2_3[j2,j3] > 0}{
#     printf"\t> L[%-4s]: %d\n", j3, u2_3[j2,j3];}
# }

# printf: "========================================\n";
# printf: "THC     > Reg + PHC + SHC (dest. flow)\n";
# printf: "========================================\n";
# for{j3 in L3: (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3])
# + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
# + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])>0}{
#     printf: "THC[%-4s] > \t : %d\t(%d + %d + %d) (Orig: Reg + PHC + SHC)\n", 
#         j3, 
#         sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3])
#         + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
#         + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3], 
#         sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]), 
#         sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3], 
#         sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3];
#     # Reg
#     for{i in I: (j3,i) in Link30 and u3_0[j3,i] > 0}{
#     printf"\t> L[%-4s]: %d\n", i, u3_0[j3,i];} 
#     # PHC
#     for{j1 in L1: (j3,j1) in Link31 and u3_1[j3,j1] > 0}{
#     printf"\t> L[%-4s]: %d\n", j1, u3_1[j3,j1];}
#     # SHC
#     for{j2 in L2: (j3,j2) in Link32 and u3_2[j3,j2] > 0}{
#     printf"\t> L[%-4s]: %d\n", j2, u3_2[j3,j2];}
# }


# printf: "================================================================\n";
# printf: "PHC     :\tCapty\tExp\tTCapty\tMet\tUse(%%)\n";
# printf: "================================================================\n";

# printf{j1 in EL[1] inter L1}:
# "[%-5s]:\t%d\t%d\t%d\t%d\t%3d%%\n",
# j1,
# C1[j1],
# extra_size1[j1]*POP_PER_TEAM,
# C1[j1] + extra_size1[j1]*POP_PER_TEAM,
# (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]),
# if (C1[j1] + extra_size1[j1]*POP_PER_TEAM) > 0 then
#     ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])
#     / (C1[j1] + extra_size1[j1]*POP_PER_TEAM)) else 0;

# printf{j1 in CL[1] inter L1:
#         (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#         + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#         + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]) > 0}:
# "[%-5s*]:\t%d\t%d\t%d\t%d\t%3d%%\n",
# j1,
# C1[j1],
# extra_size1[j1]*POP_PER_TEAM,
# C1[j1] + extra_size1[j1]*POP_PER_TEAM,
# (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]),
# if (C1[j1] + extra_size1[j1]*POP_PER_TEAM) > 0 then
#     ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])
#     / (C1[j1] + extra_size1[j1]*POP_PER_TEAM)) else 0;

# printf: "========================================\n";
# printf: "SHC     :\tCapty\tMet\tUse(%%)\n";
# printf: "========================================\n";
# printf{j2 in EL[2] inter L2}: "[%-6s]:\t%d\t%d\t%3d%%\n", j2, 
# C2[j2], 
# (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]),
# if C2[j2] > 0 then ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/(C2[j2]))*100 else 0;

# printf{j2 in CL[2] inter L2: (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])>0}: 
# "[%-5s*]:\t%d\t%d\t%3d%%\n", j2, 
# C2[j2], 
# (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]),
# if C2[j2] > 0 then ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/(C2[j2]))*100 else 0;

# printf: "========================================\n";
# printf: "THC     :\tCapty\tMet\tUse(%%)\n";
# printf: "========================================\n";
# printf{j3 in EL[3] inter L3}: "[%-6s]:\t%d\t%d\t%3d%%\n", j3, 
# C3[j3], 
# (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]),
# if C3[j3] > 0 then ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])/(C3[j3]))*100 else 0;

# printf{j3 in CL[3] inter L3: (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])>0}: 
# "[%-5s*]:\t%d\t%d\t%3d%%\n", j3, 
# C3[j3], 
# (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]),
# if C3[j3] > 0 then ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])/(C3[j3]))*100 else 0;
# printf: "========================================\n\n";


# printf: "==========================================================="; 
# printf: "===========================================================\n";










# # ####################################################################
# # Exportacao de resultados
# # ####################################################################

# #Relatorio em Excel
# param Financeiro, symbolic, default "1-Financeiro.txt";
# param NovasUnidades, symbolic, default "2-NovasUnidades.txt";
# param RealocacaoEquipe_PHC, symbolic, default "3-RealocacaoEquipe_PHC.txt";
# param RealocacaoEquipe_SHC, symbolic, default "4-RealocacaoEquipe_SHC.txt";
# param RealocacaoEquipe_THC, symbolic, default "5-RealocacaoEquipe_THC.txt";
# param ContratacaoEquipe_PHC, symbolic, default "6-ContratacaoEquipe_PHC.txt";
# param ContratacaoEquipe_SHC, symbolic, default "7-ContratacaoEquipe_SHC.txt";
# param ContratacaoEquipe_THC, symbolic, default "8-ContratacaoEquipe_THC.txt";
# param Balanceamento_PHC, symbolic, default "9-Balanceamento_PHC.txt";
# param Balanceamento_SHC, symbolic, default "10-Balanceamento_SHC.txt";
# param Balanceamento_THC, symbolic, default "11-Balanceamento_THC.txt";
# param Fluxo_RegCensitaria, symbolic, default "12-Fluxo_RegCensitaria.txt";
# param Fluxo_PHC, symbolic, default "13-Fluxo_PHC.txt";
# param Fluxo_SHC, symbolic, default "14-Fluxo_SHC.txt";
# param Fluxo_THC, symbolic, default "15-Fluxo_THC.txt";
# param Uso_PHC, symbolic, default "16-Uso_PHC.txt";
# param Uso_SHC, symbolic, default "17-Uso_SHC.txt";
# param Uso_THC, symbolic, default "18-Uso_THC.txt";



# ##################################################################################################
# printf: "\n========================================\n";
# printf: "Health Care Plan with Team Reallocation\n";
# printf: "========================================\n";
# printf: "Logist cost:\t%.2f\n", 
#       sum{i in I, j1 in L1: (i,j1) in Link01}TC0_1[i,j1]*u0_1[i,j1] 
#     + sum{i in I, j2 in L2: (i,j2) in Link02}TC0_2[i,j2]*u0_2[i,j2] 
#     + sum{i in I, j3 in L3: (i,j3) in Link03}TC0_3[i,j3]*u0_3[i,j3]     
#     + sum{j1 in L1, j2 in L2: (j1,j2) in Link12}TC1_2[j1,j2]*u1_2[j1,j2]  
#     + sum{j1 in L1, j3 in L3: (j1,j3) in Link13}TC1_3[j1,j3]*u1_3[j1,j3]  
#     + sum{j2 in L2, j3 in L3: (j2,j3) in Link23}TC2_3[j2,j3]*u2_3[j2,j3] > Financeiro;
# printf: "Fixed cost [Existing]:\t%.2f\n", 
#       sum{j1 in EL[1] inter L1}FC1[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
#     + sum{j2 in EL[2] inter L2}FC2[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
#     + sum{j3 in EL[3] inter L3}FC3[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e] >> Financeiro;
# printf: "Expansion cost [Existing]:\t%.2f\n", 
#       sum{j1 in EL[1] inter L1}(IA1_exp_unit + FC1_exp_unit)*extra_size1[j1] >> Financeiro;
# printf: "Fixed cost [Candidate]:\t%.2f\n", 
#       sum{j1 in CL[1] inter L1}(FC1[j1]+IA1[j1])*y1[j1] 
#     + sum{j2 in CL[2] inter L2}(FC2[j2]+IA2[j2])*y2[j2] 
#     + sum{j3 in CL[3] inter L3}(FC3[j3]+IA3[j3])*y3[j3] >> Financeiro;
# printf: "Expansion cost [Candidate]:\t%.2f\n", 
#       sum{j1 in CL[1] inter L1}(IA1_exp_unit + FC1_exp_unit)*extra_size1[j1] >> Financeiro;
# printf: "New team cost:\t%.2f\n",
#     sum{j1 in EL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN
#     - sum{to in L1: to != j1}transfer1[e1,j1,to]  # Teams transferred OUT    
#     + newhire1[e1,j1])  # New teams hired
#     + sum{j1 in CL[1], e1 in E[1]}CE1[e1]*(
# 	sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1]  # Teams transferred IN    
#     + newhire1[e1,j1])  # New teams hired

#     + sum{j2 in EL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN
#     - sum{to in L2: to != j2}transfer2[e2,j2,to] # Teams transferred OUT    
#     + newhire2[e2,j2]) # New teams hired
#     + sum{j2 in CL[2], e2 in E[2]}CE2[e2]*(
# 	sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Teams transferred IN    
#     + newhire2[e2,j2]) # New teams hired
	
#     + sum{j3 in EL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN
#     - sum{to in L3: to != j3}transfer3[e3,j3,to] # Teams transferred OUT    
#     + newhire3[e3,j3]) # New teams hired
#     + sum{j3 in CL[3], e3 in E[3]}CE3[e3]*(
# 	sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Teams transferred IN    
#     + newhire3[e3,j3]) >> Financeiro; # New teams hired

# printf: "Team relocation cost:\t%.2f\n",
#     # Re-assignment costs:  Transfer IN
#     sum{e1 in E[1], from in EL[1] inter L1, to in L1: from != to}
#          RC1[e1]*(DL1_KM[from,to])*transfer1[e1,from,to]
#     + sum{e2 in E[2], from in EL[2] inter L2, to in L2: from != to}
#          RC2[e2]*(DL2_KM[from,to])*transfer2[e2,from,to]
#     + sum{e3 in E[3], from in EL[3] inter L3, to in L3: from != to}
#          RC3[e3]*(DL3_KM[from,to])*transfer3[e3,from,to]
#     # Re-assignment costs:  Transfer OUT
#     + sum{e1 in E[1], j1 in EL[1] inter L1, to in L1: to != j1}
#         RC1[e1]*(DL1_KM[j1,to])*transfer1[e1,j1,to]
#     + sum{e2 in E[2], j2 in EL[2] inter L2, to in L2: to != j2}
#         RC2[e2]*(DL2_KM[j2,to])*transfer2[e2,j2,to]
#     + sum{e3 in E[3], j3 in EL[3] inter L3, to in L3: to != j3}
#         RC3[e3]*(DL3_KM[j3,to])*transfer3[e3,j3,to] >> Financeiro;
# printf: "Variable Cost:\t%.2f\n",     
#     # Variable cost per patient
#     sum{j1 in L1}VC1[j1]*(sum{i in I: (i,j1) in Link01}u0_1[i,j1]  # Home → L1
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]              # L2 → L1
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]              # L3 → L1
#     + sum{i in I: (i,j1) in Link01} ut1[i,j1])                # Telehealth in L1
#     + sum{j2 in L2}VC2[j2]*(sum{i in I: (i,j2) in Link02}u0_2[i,j2] # Home → L2
#     + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2]              # L1 → L2
#     + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]              # L3 → L2
#     + sum{i in I: (i,j2) in Link02} ut2[i,j2])                # Telehealth in L2
#     + sum{j3 in L3}VC3[j3]*(sum{i in I: (i,j3) in Link03} u0_3[i,j3] # Home → L3
#     + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3]              # L1 → L3
#     + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]              # L2 → L2
#     + sum{i in I: (i,j3) in Link03} ut3[i,j3]) >> Financeiro;  # Telehealth in L3
# printf: "========================================\n";
# printf: "Total Cost:\t%.2f\n", 
# Total_Costs_s * COST_SCALE
# # If GLPK or Highs...
# # + (sum{j1 in EL[1] inter L1}FC1[j1]*y1[j1] + sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
# #     + sum{j2 in EL[2] inter L2}FC2[j2]*y2[j2] + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
# #     + sum{j3 in EL[3] inter L3}FC3[j3]*y3[j3] + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e])
# + (sum{e in E[1], j1 in EL[1]}CNES1[e,j1]*CE1[e]  
#    + sum{e in E[2], j2 in EL[2]}CNES2[e,j2]*CE2[e] 
#    + sum{e in E[3], j3 in EL[3]}CNES3[e,j3]*CE3[e])
# - (# Penalty for surplus or deficit 
#     sum{e1 in E[1], j1 in L1}P1_s*surplus1[e1,j1] 
#     + sum{e2 in E[2], j2 in L2}P2_s*surplus2[e2,j2] 
#     + sum{e3 in E[3], j3 in L3}P3_s*surplus3[e3,j3] 
#     + sum{e1 in E[1], j1 in L1}P1_d*deficit1[e1,j1] 
#     + sum{e2 in E[2], j2 in L2}P2_d*deficit2[e2,j2] 
#     + sum{e3 in E[3], j3 in L3}P3_d*deficit3[e3,j3]) * COST_SCALE
#     >> Financeiro;
# printf: "Total APS Cost:\t%.2f\n", Total_Costs_APS_s * COST_SCALE >> Financeiro;
# printf: "Budget Limit:\t%.2f\n", BUDGET_s * COST_SCALE >> Financeiro;
# printf: "Budget Usage (%%):\t%.2f\n", (Total_Costs_APS_s/BUDGET_s) >> Financeiro;
# printf: "Budget Overrun:\t%.2f\n", budget_slack * COST_SCALE >> Financeiro;
# printf: "Overrun (%%):\t%.2f\n", 
# if BUDGET_s > 0 then (budget_slack / BUDGET_s) else 0 >> Financeiro;
# printf: "Effective Budget:\t%.2f\n", (BUDGET_s + budget_slack) * COST_SCALE >> Financeiro;
# printf: "========================================\n";


# printf: "New Units:\tQty\tMax\tUse (%%)\n" > NovasUnidades; 
# printf: "========================================\n";
# printf: "PHC:\t%d\t%d\t%.2f\n", 
# sum{j1 in CL[1] inter L1}y1[j1],
# MaxNewPHC, 
# if MaxNewPHC > 0 then ((sum{j1 in CL[1] inter L1}y1[j1])/(MaxNewPHC)) else 0 >> NovasUnidades;
# printf: "SHC:\t%d\t%d\t%.2f\n", 
# sum{j2 in CL[2] inter L2}y2[j2],
# MaxNewSHC, 
# if MaxNewSHC > 0 then ((sum{j2 in CL[2] inter L2}y2[j2])/(MaxNewSHC)) else 0 >> NovasUnidades;
# printf: "THC :\t%d\t%d\t%.2f\n", 
# sum{j3 in CL[3] inter L3}y3[j3],
# MaxNewTHC, 
# if MaxNewTHC > 0 then ((sum{j3 in CL[3] inter L3}y3[j3])/(MaxNewTHC)) else 0 >> NovasUnidades;
# printf: "========================================\n";



# printf: "\n========================================\n";
# printf: "TEAM REALLOCATION SUMMARY\n";
# printf: "========================================\n";

# # PHC Team Transfers
# # printf: "PHC Team Transfers:\n" > RealocacaoEquipe_PHC;
# printf: "From\tTo\tTeam\tQty\tDist (km)\n" > RealocacaoEquipe_PHC;
# printf: "================================================\n";
# for{e1 in E[1], from in EL[1] inter L1, to in L1: from != to and transfer1[e1,from,to] > 0.01}{
#     printf: "[%s]\t[%s]%s\t%s\t%.2f\t%.2f\n", 
#         from, 
#         to, 
#         if to in CL[1] then "*" else "", 
#         e1, 
#         transfer1[e1,from,to], 
#         (DL1_KM[from,to]) >> RealocacaoEquipe_PHC;
# }

# # SHC Team Transfers
# # printf: "\n\n" >> RealocacaoEquipe_SHC;
# # printf: "\nSHC Team Transfers:\n" > RealocacaoEquipe_SHC;
# printf: "From\tTo\tTeam\tQty\tDist (km)\n" > RealocacaoEquipe_SHC;
# printf: "================================================\n";
# for{e2 in E[2], from in EL[2] inter L2, to in L2: from != to and transfer2[e2,from,to] > 0.01}{
#     printf: "[%s]\t[%s]%s\t%s\t%.2f\t%.2f\n", 
#         from, 
#         to,
#         if to in CL[2] then "*" else "",  
#         e2, 
#         transfer2[e2,from,to], 
#         (DL2_KM[from,to]) >> RealocacaoEquipe_SHC;
# }

# # THC Team Transfers
# # printf: "\n\n" >> RealocacaoEquipe_THC;
# # printf: "\nTHC Team Transfers:\n" > RealocacaoEquipe_THC;
# printf: "From\tTo\tTeam\tQty\tDist (km)\n" > RealocacaoEquipe_THC;
# printf: "================================================\n";
# for{e3 in E[3], from in EL[3] inter L3, to in L3: from != to and transfer3[e3,from,to] > 0.01}{
#     printf: "[%s]\t[%s]%s\t%s\t%.2f\t%.2f\n", 
#         from, 
#         to,
#         if to in CL[3] then "*" else "", 
#         e3, 
#         transfer3[e3,from,to], 
#         (DL3_KM[from,to]) >> RealocacaoEquipe_THC;
# }


# printf: "\n================================================\n";
# printf: "NEW TEAMS HIRED\n";
# printf: "================================================\n";
# # printf: "Location\tTeam\tQty\n" > ContratacaoEquipe_PHC;
# # printf: "PHC New Hires:\n" >> ContratacaoEquipe_PHC;
# printf: "Location\tTeam\tQty\n" > ContratacaoEquipe_PHC;
# printf: "================================================\n";
# for{j1 in L1, e1 in E[1]: newhire1[e1,j1] > 0.01}{
#     printf: "[%s]%s\t%s\t%.2f\n", 
#         j1, 
#         if j1 in CL[1] then "*" else "",
#         e1, 
#         newhire1[e1,j1] >> ContratacaoEquipe_PHC;
# }

# # printf: "\n\n" >> ContratacaoEquipe_SHC;
# # printf: "\nSHC New Hires:\n" >> ContratacaoEquipe_SHC;
# printf: "Location\tTeam\tQty\n" > ContratacaoEquipe_SHC;
# printf: "================================================\n";
# for{j2 in L2, e2 in E[2]: newhire2[e2,j2] > 0.01}{
#     printf: "[%s]%s\t%s\t%.2f\n", 
#         j2,
#         if j2 in CL[2] then "*" else "",
#         e2, 
#         newhire2[e2,j2] >> ContratacaoEquipe_SHC;
# }

# # printf: "\n\n" >> ContratacaoEquipe_THC;
# # printf: "\nTHC New Hires:\n" >> ContratacaoEquipe_THC;
# printf: "Location\tTeam\tQty\n" > ContratacaoEquipe_THC;
# printf: "================================================\n";
# for{j3 in L3, e3 in E[3]: newhire3[e3,j3] > 0.01}{
#     printf: "[%s]%s\t%s\t%.2f\n", 
#         j3,
#         if j3 in CL[3] then "*" else "",
#         e3, 
#         newhire3[e3,j3] >> ContratacaoEquipe_THC;
# }


# printf: "\n========================================\n";
# printf: "TEAM BALANCE PER LOCATION\n";
# printf: "========================================\n";

# # printf: "PHC Locations:\n" > Balanceamento_PHC;
# printf: "Loc\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n" > Balanceamento_PHC;
# printf: "===========================================================================\n";

# for{j1 in L1: ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1]) 
# + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
# + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])>0) or j1 in EL[1] and sum{e1 in E[1]} CNES1[e1,j1] > 0}{
#     for{e1 in E[1]}{        
#         printf: "[%s]%s\t%s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j1,
#             if j1 in CL[1] then "*" else "",
#             e1,
#             if j1 in EL[1] then CNES1[e1,j1] else 0,
#             # round((sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1]) * TEAM_SCALE0_1[i,e1]
#             # + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1] * TEAM_SCALE1[e1]
#             # + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1] * TEAM_SCALE1[e1])),
#             (sum{i  in I:  (i,j1)  in Link01} (u0_1[i,j1]  + ut1[i,j1]) * TEAM_SCALE0_1[i,e1]
#             + sum{j2 in L2: (j2,j1) in Link21}  u2_1[j2,j1] * TEAM_SCALE1[e1]
#             + sum{j3 in L3: (j3,j1) in Link31}  u3_1[j3,j1] * TEAM_SCALE1[e1]),
#             sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1] # Transfers IN
#             - (if j1 in EL[1] then sum{to in L1: to != j1}transfer1[e1,j1,to] else 0), # Teams transferred OUT            
#             newhire1[e1,j1],
#             (if j1 in EL[1] then CNES1[e1,j1] else 0) # Result: CNES +
#             + sum{from in EL[1] inter L1: from != j1}transfer1[e1,from,j1] # Transfers IN
#             - (if j1 in EL[1] then sum{to in L1: to != j1}transfer1[e1,j1,to] else 0) # Teams transferred OUT            
#             + newhire1[e1,j1],
#             surplus1[e1,j1],
#             deficit1[e1,j1] >> Balanceamento_PHC;
#     }
# }



# # printf: "===========================================================================\n";
# # printf: "TOTAL TEAMS PER CATEGORY\n";
# # printf: "===========================================================================\n";
# # printf: "Team\tRequired\tResult\n" >> Balanceamento_PHC;
# # for{e1 in E[1]}{
# #     printf: "%s\t%.2f\t\t%.2f\n",
# #         e1,
# #         # ReqTotal[e1],
# #         sum{j1 in L1} (sum{i in I} (u0_1[i,j1] + ut1[i,j1])*MS0_1[i,e1]
# #         + sum{j2 in L2} u2_1[j2,j1]*MS1[e1]
# #         + sum{j3 in L3} u3_1[j3,j1]*MS1[e1]),
# #         # ResultTotal[e1];
# #         sum{j1 in L1} ((if j1 in EL[1] then CNES1[e1,j1] else 0)
# #         + sum{from in EL[1] inter L1: from != j1} transfer1[e1,from,j1]
# #         - (if j1 in EL[1] then sum{to in L1: to != j1} transfer1[e1,j1,to] else 0)
# #         + newhire1[e1,j1]) >> Balanceamento_PHC;
# # }
# # printf: "===========================================================================\n";


# # printf: "\nSHC Locations:\n" >> Balanceamento_SHC;
# printf: "Loc\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n" > Balanceamento_SHC;
# printf: "===========================================================================\n";
# for{j2 in L2: ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) 
# + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
# + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]) > 0) or j2 in EL[2] and sum{e2 in E[2]} CNES2[e2,j2] > 0}{
#     for{e2 in E[2]}{
#         printf: "[%s]%s\t%s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j2,
#             if j2 in CL[2] then "*" else "",
#             e2,
#             if j2 in EL[2] then CNES2[e2,j2] else 0, #CNES
#             (sum{i in I: (i,j2) in Link02}(u0_2[i,j2]+ut2[i,j2]) 
#             + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
#             + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/POP_PER_TEAM,
#             sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Transfers IN
#             - (if j2 in EL[2] then sum{to in L2: to != j2}transfer2[e2,j2,to] else 0), # Teams transferred OUT            
#             newhire2[e2,j2],
#             (if j2 in EL[2] then CNES2[e2,j2] else 0) # CNES
#             + sum{from in EL[2] inter L2: from != j2}transfer2[e2,from,j2] # Transfers IN
#             - (if j2 in EL[2] then sum{to in L2: to != j2}transfer2[e2,j2,to] else 0) # Teams transferred OUT
#             + newhire2[e2,j2],
#             surplus2[e2,j2],
#             deficit2[e2,j2] >> Balanceamento_SHC;
#     }
# }

# # printf: "\nTHC Locations:\n" >> Balanceamento_THC;
# printf: "Loc\tTeam\tCNES\tReq\tTransf\tNew\tRes\tSurp\tDef\n" > Balanceamento_THC;
# printf: "===========================================================================\n";
# for{j3 in L3: ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) 
# + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
# + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]) > 0) or j3 in EL[3] and sum{e3 in E[3]} CNES3[e3,j3] > 0}{
#     for{e3 in E[3]}{
#         printf: "[%s]%s\t%s\t%.1f\t%.2f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
#             j3,
#             if j3 in CL[3] then "*" else "",
#             e3,
#             if j3 in EL[3] then CNES3[e3,j3] else 0,
#             (sum{i in I: (i,j3) in Link03}(u0_3[i,j3]+ut3[i,j3]) 
#             + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
#             + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]) / POP_PER_TEAM,
#             sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Transfers IN
#             - (if j3 in EL[3] then sum{to in L3: to != j3}transfer3[e3,j3,to] else 0), # Teams transferred OUT            
#             newhire3[e3,j3],
#             (if j3 in EL[3] then CNES3[e3,j3] else 0) # CNES
#             + sum{from in EL[3] inter L3: from != j3}transfer3[e3,from,j3] # Transfers IN
#             - (if j3 in EL[3] then sum{to in L3: to != j3}transfer3[e3,j3,to] else 0) # Teams transferred OUT
#             + newhire3[e3,j3],
#             surplus3[e3,j3],
#             deficit3[e3,j3] >> Balanceamento_THC;
#     }
# }

# # printf: "\n========================================\n";
# # printf: "Region\tPop\tFlow\n" > Fluxo_RegCensitaria; 
# # printf: "========================================\n";
# # printf{i in I}: "[%s]\t%d\t%d\n", i, 
# # W[i], 
# # sum{j1 in L1}u0_1[i,j1] 
# # + sum{j2 in L2} u0_2[i,j2]
# # + sum{j3 in L3} u0_3[i,j3]
# # + sum{j1 in L1} ut1[i,j1]
# # + sum{j2 in L2} ut2[i,j2]
# # + sum{j3 in L3} ut3[i,j3] >> Fluxo_RegCensitaria; 

# printf: "========================================\n";
# # printf: "\n\nReg     > PHC + SHC + THC  :(flow)\n" >> Fluxo_RegCensitaria; 
# printf: "========================================\n";
# printf "" > Fluxo_RegCensitaria;
# for{i in I}{
#     # PHC
#     printf "RC[%s]\t\t%d\tDist (km)\n", i, W[i] >> Fluxo_RegCensitaria; 
#     for{j1 in L1: (i,j1) in Link01 and u0_1[i,j1] > 0}{
#     printf ">\tL[%s]\t%d\t%.2f\n", j1, u0_1[i,j1], (D0_1_KM[i,j1]) >> Fluxo_RegCensitaria;}  
#     for{j1 in L1: (i,j1) in Link01 and ut1[i,j1] > 0}{
#     printf ">\tL[%s] tel\t%d\n", j1, ut1[i,j1] >> Fluxo_RegCensitaria; }
#     # SHC
#     for{j2 in L2: (i,j2) in Link02 and u0_2[i,j2] > 0}{
#     printf ">\tL[%s]\t%d\t%.2f\n", j2, u0_2[i,j2], (D0_2_KM[i,j2]) >> Fluxo_RegCensitaria;} 
#     for{j2 in L2: (i,j2) in Link02 and ut2[i,j2] > 0}{
#     printf ">\tL[%s] tel\t%d\n", j2, ut2[i,j2] >> Fluxo_RegCensitaria;}     
#     # THC
#     for{j3 in L3: (i,j3) in Link03 and u0_3[i,j3] > 0}{
#     printf ">\tL[%s]\t%d\t%.2f\n", j3, u0_3[i,j3], (D0_3_KM[i,j3]) >> Fluxo_RegCensitaria;} 
#     for{j3 in L3: (i,j3) in Link03 and ut3[i,j3] > 0}{
#     printf ">\tL[%s] tel\t%d\n", j3, ut3[i,j3] >> Fluxo_RegCensitaria;}
# }
# # printf: "========================================\n";
# # printf: "*tel: (telesaude, ou teleconsulta)\n" >> Fluxo_RegCensitaria; 
# # printf: "========================================\n";


# printf: "========================================\n";
# # printf: "PHC     > Reg + SHC + THC (dest. flow)\n" >> Fluxo_PHC; 
# printf: "========================================\n";
# printf "" > Fluxo_PHC;

# for{j1 in L1: (sum{i in I: (i,j1) in Link01}(u0_1[i,j1] + ut1[i,j1])
# + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
# + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]) > 0}{
#     printf"PHC[%s]\t\t%d\tDist (km)\n",  # \t(%d + %d + %d) (Orig: Reg + SHC + THC)
#         j1, 
#         sum{i in I: (i,j1) in Link01}(u0_1[i,j1] + ut1[i,j1])
#         + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#         + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1] >> Fluxo_PHC;
        
#     # Reg
#     for{i in I: (j1,i) in Link10 and u1_0[j1,i] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", i, u1_0[j1,i], (D1_0_KM[j1,i]) >> Fluxo_PHC;} # O1_0[j1]*
#     # SHC
#     for{j2 in L2: (j1,j2) in Link12 and u1_2[j1,j2] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j2, u1_2[j1,j2], (D1_2_KM[j1,j2]) >> Fluxo_PHC;} # O1_2[j1]*
#     # THC
#     for{j3 in L3: (j1,j3) in Link13 and u1_3[j1,j3] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j3, u1_3[j1,j3], (D1_3_KM[j1,j3]) >> Fluxo_PHC;} # O1_3[j1]*
# }

# printf: "========================================\n";
# # printf: "\n\nSHC     > Reg + PHC + THC (dest. flow)\n" >> Fluxo_SHC;
# printf: "========================================\n";
# printf "" > Fluxo_SHC;

# for{j2 in L2: (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2])
# + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
# + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])>0}{
#     printf: "SHC[%s]\t\t%d\tDist (km)\n",  # \t(%d + %d + %d) (Orig: Reg + PHC + THC)
#         j2, 
#         sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2])
#         + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] 
#         + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2] >> Fluxo_SHC;
        
#     # Reg
#     for{i in I: (j2,i) in Link20 and u2_0[j2,i] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", i, u2_0[j2,i], (D2_0_KM[j2,i]) >> Fluxo_SHC;} 
#     # PHC
#     for{j1 in L1: (j2,j1) in Link21 and u2_1[j2,j1] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j1, u2_1[j2,j1], (D2_1_KM[j2,j1]) >> Fluxo_SHC;}
#     # THC
#     for{j3 in L3: (j2,j3) in Link23 and u2_3[j2,j3] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j3, u2_3[j2,j3], (D2_3_KM[j2,j3]) >> Fluxo_SHC;}
# }

# printf: "========================================\n";
# # printf: "\n\nTHC     > Reg + PHC + SHC (dest. flow)\n" >> Fluxo_THC;
# printf: "========================================\n";
# printf "" > Fluxo_THC;

# for{j3 in L3: (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3])
# + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
# + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])>0}{
#     printf: "THC[%s]\t\t%d\tDist (km)\n", # \t(%d + %d + %d) (Orig: Reg + PHC + SHC)
#         j3, 
#         sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3])
#         + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] 
#         + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3] >> Fluxo_THC;
        
#     # Reg
#     for{i in I: (j3,i) in Link30 and u3_0[j3,i] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", i, u3_0[j3,i], (D3_0_KM[j3,i]) >> Fluxo_THC;} 
#     # PHC
#     for{j1 in L1: (j3,j1) in Link31 and u3_1[j3,j1] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j1, u3_1[j3,j1], (D3_1_KM[j3,j1]) >> Fluxo_THC;}
#     # SHC
#     for{j2 in L2: (j3,j2) in Link32 and u3_2[j3,j2] > 0}{
#     printf">\tL[%s]\t%d\t%.2f\n", j2, u3_2[j3,j2], (D3_2_KM[j3,j2]) >> Fluxo_THC;}
# }

# printf: "=======================================================\n";
# printf: "PHC\tCapty\tExp\tTCapty\tMet\tUse\n" > Uso_PHC;
# printf: "========================================================\n";

# printf{j1 in EL[1] inter L1}:
# "[%s]\t%d\t%d\t%d\t%d\t%5.2f\n",
# j1,
# C1[j1],
# extra_size1[j1]*POP_PER_TEAM,
# C1[j1] + extra_size1[j1]*POP_PER_TEAM,
# (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]),
# if (C1[j1] + extra_size1[j1]*POP_PER_TEAM) > 0 then
#     ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])
#     / (C1[j1] + extra_size1[j1]*POP_PER_TEAM)) else 0 >> Uso_PHC;

# printf{j1 in CL[1] inter L1:
#         (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#         + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#         + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]) > 0}:
# "[%s*]\t%d\t%d\t%d\t%d\t%5.2f\n",
# j1,
# C1[j1],
# extra_size1[j1]*POP_PER_TEAM,
# C1[j1] + extra_size1[j1]*POP_PER_TEAM,
# (sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1]),
# if (C1[j1] + extra_size1[j1]*POP_PER_TEAM) > 0 then
#     ((sum{i in I: (i,j1) in Link01}(u0_1[i,j1]+ut1[i,j1])
#     + sum{j2 in L2: (j2,j1) in Link21}u2_1[j2,j1]
#     + sum{j3 in L3: (j3,j1) in Link31}u3_1[j3,j1])
#     / (C1[j1] + extra_size1[j1]*POP_PER_TEAM)) else 0 >> Uso_PHC;


# printf: "========================================\n";
# printf: "SHC\tCapty\tMet\tUse\n" > Uso_SHC;
# printf: "========================================\n";
# printf{j2 in EL[2] inter L2}: "[%s]\t%d\t%d\t%.2f\n", j2, 
# C2[j2], 
# (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]),
# if C2[j2] > 0 then ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/(C2[j2])) else 0 >> Uso_SHC;

# printf{j2 in CL[2] inter L2: (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])>0}: 
# "[%s*]\t%d\t%d\t%.2f\n", j2, 
# C2[j2], 
# (sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2]),
# if C2[j2] > 0 then ((sum{i in I: (i,j2) in Link02}(u0_2[i,j2] + ut2[i,j2]) + sum{j1 in L1: (j1,j2) in Link12}u1_2[j1,j2] + sum{j3 in L3: (j3,j2) in Link32}u3_2[j3,j2])/(C2[j2])) else 0 >> Uso_SHC;

# printf: "========================================\n";
# printf: "THC\tCapty\tMet\tUse\n" > Uso_THC;
# printf: "========================================\n";
# printf{j3 in EL[3] inter L3}: "[%s]\t%d\t%d\t%.2f\n", j3, 
# C3[j3], 
# (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]),
# if C3[j3] > 0 then ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])/(C3[j3])) else 0 >> Uso_THC;

# printf{j3 in CL[3] inter L3: (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])>0}: 
# "[%s*]\t%d\t%d\t%.2f\n", j3, 
# C3[j3], 
# (sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3]),
# if C3[j3] > 0 then ((sum{i in I: (i,j3) in Link03}(u0_3[i,j3] + ut3[i,j3]) + sum{j1 in L1: (j1,j3) in Link13}u1_3[j1,j3] + sum{j2 in L2: (j2,j3) in Link23}u2_3[j2,j3])/(C3[j3])) else 0 >> Uso_THC;
# printf: "========================================\n\n";

# ########################################################################

end;



