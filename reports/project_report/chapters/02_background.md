# 2 Background, scope and approach

## 2.1 The problem

Rewetting decisions depend on knowing where and when the water table falls, because drained peat dries out and burns. Tropical peat forms a dome of partly decomposed plant material. It is highest in the middle and slopes by a few metres over several kilometres towards the rivers that bound it, and when intact it stays waterlogged all year. Drainage canals dug for plantations, farming, transport or logging lower the water table, most strongly near the canals. In the dry season the rain stops but evapotranspiration continues at about 4 mm per day, the water table falls further, and the dry upper peat can burn, sometimes for weeks below the surface. Drained peat also subsides: about 2.2 cm per year on average over 2.7 million ha of Southeast Asian peat surveyed by satellite radar in 2007-2011 (Hoyt et al. 2020) and about 4.3 cm per year under plantation drainage (Evans et al. 2019).

Rewetting aims to keep the water table high enough through the dry season that the peat does not dry out and burn. Its tools are canal blocks (*sekat kanal*), adjustable water gates (*pintu air*) and, where water has to be moved, pumps.

## 2.2 Policy context in 2026

Indonesia has the largest area of tropical peat in the world, about 13.36 million ha holding an estimated 57 gigatonnes of carbon. Since 2016 the government has restored peat through the 3R strategy: rewetting, revegetation and revitalisation of livelihoods, delivered through programmes such as the peat-care villages (*Desa Mandiri Peduli Gambut*, DMPG), restoration by concession holders, communities and development partners. In October 2025 the government reported about 4.16 million ha of peat rewetted through 45,000 canal blocks (KLH/BPLH 2026).

The 2026 dry season raised the urgency. The national fire monitoring system (Sipongi, Ministry of Forestry) recorded 202,004.30 ha burned from January to July 2026. KLH/BPLH's own burn-scar analysis gives about 1.64 million ha burned from January to October 2026, more than in the same period of 2019, 2023 and 2025, of which about 673,279 ha (40.9%) was on peat. KLH has set a peat restoration target of about 3.3 million ha in 337 priority KHG, selected with the peat ecosystem damage status (*Status Kerusakan Ekosistem Gambut*, SKEG), especially on burned land and land affected by canals. The interventions it lists are water management and rewetting infrastructure, revegetation where suitable, monitoring of the peat water table (*TMAT*), early fire warning and community empowerment (KLH/BPLH 2026).

KLH/BPLH frames the response as water governance at KHG level, including water sharing between licence holders and the communities around them within one KHG. Its focus group discussion of 2 November 2026 on fire prevention through KHG water governance asks for the current condition and fire risk of priority KHG, the factors that make peat vulnerable (hydrology, land use, rewetting infrastructure, governance), the roles of each ministry and agency, and a KHG-based action plan with locations, intervention types, responsibilities, timing and funding needs, including through the proposed Re-Peat project (KLH/BPLH 2026). The toolkit described in this report provides evidence for several of these: where water is short and when (chapter 8), which KHG and sub-KHG to treat first (chapters 6 and 7), and which blocks and pumps are needed and at what cost (chapter 9). Chapter 11 maps the outputs to the discussion's questions.

## 2.3 Regulatory target

Indonesian regulation (PP 71/2014 as amended by PP 57/2016) treats cultivation-function peat as damaged when the water table (*tinggi muka air*, *TMA*) is more than 0.4 m below the surface at a compliance point. Permen LHK P.15/2017 sets how the TMA is measured. The fire literature agrees with this threshold: fire danger rises mostly when the water table falls below 0.4 m, burning is found below about 0.6 m (Taufik et al. 2022), and at a South Sumatra site fire hazard became high once the water table fell below a critical depth of about 0.85 m, where capillary rise no longer kept the topsoil moist (Taufik et al. 2019). Throughout this report, "deeper than 40 cm" means the water table is below the regulatory line.

The planning unit is the *KHG* (*Kesatuan Hidrologis Gambut*, peat hydrological unit): a peat area bounded by rivers or the sea that behaves as one water system. The official list (SK.129/MENLHK/2017) has 865 KHG. Inside a KHG this study works with *sub-KHG*: parts of the KHG that drain to their own outlet, a river or a large canal.

## 2.4 Scope of the GIS workstream

The GIS workstream of the World Bank and KLH peatland rewetting project builds a toolkit, RE-PEAT, that answers four questions in order:

1. Which KHG should rewetting focus on, nationally?
2. Which ground surface can the analysis rely on inside a KHG, given that good terrain data exist for few KHG?
3. Where inside a KHG is water short, by how much, and in which season (*neraca air*, the water balance)?
4. Where should canal blocks, gates and pumps go, how much water must be moved, and at what cost?

The project selected 12 main KHG for detailed work, with reserves (Table 2.1). The twelfth, Cawang-Lalang, is to be confirmed with KLH: its name does not match the official boundary file, and the nearest KHG is Air Banyuasin - Air Lalang. Kampar-Gaung, the earlier test site, is analysed as well.

{{table: selected_khg | The selected KHG. Source: project selection of 22 October 2026; areas from the KHG boundary file, Kampar-Gaung from the SK.129/MENLHK/2017 list | selected_khg.csv joined to khg_registry.csv}}

## 2.5 How the toolkit is built

RE-PEAT is a chain of modules, each building on the outputs of the one before (Figure 2.1). Every result can be regenerated from the source data when those data are updated, and the same method runs for any of the 865 KHG.

{{diagram: toolkit_chain | The RE-PEAT chain for one KHG. Each step runs once per elevation model (LiDAR where it covers the KHG, corrected DeltaDTM and corrected DEMNAS). The national ranking runs separately over all 865 KHG | diagram}}

The modules are:

- DEM correction: clips each elevation model to the KHG and corrects DeltaDTM and DEMNAS towards bare ground (chapter 4).
- Sub-KHG delineation: divides the KHG into drainage units from the terrain, canals and rivers (chapter 5).
- National and sub-KHG prioritisation: ranks all 865 KHG, and ranks the sub-KHG inside one KHG (chapters 6 and 7).
- Neraca air: the water balance per sub-KHG and the water-table deficit from station records, and a groundwater model in development for rewetting scenarios (chapter 8).
- RE-PEAT Interventions: places canal blocks and pumps, sizes the water need and the budget, and produces the map layouts, also as a QGIS plugin for KLH staff (chapter 9).

Few KHG have airborne LiDAR, and the open elevation models differ in quality from one KHG to the next (chapter 4). The whole chain therefore runs once per elevation model, and the differences between the three runs show how much a result depends on the terrain.

## 2.6 Lessons from the 2021 Kahayan-Sebangau study

The 2021 final report of the UGM team on KHG Sungai Kahayan - Sungai Sebangau is the direct predecessor of this toolkit. Several of its methods were kept and automated: sub-KHG delineation from flow direction and stream order with large channels as outlets (16 sub-KHG there), a water balance with interception by land cover, block spacing from the 0.4 m design limit divided by land slope, and the closing of blocks from June to August. It also showed that the worst sub-KHG by mean water balance were not the worst by number of deficit months, so both measures are kept.

Two of its steps are not carried forward. The study multiplied the mean daily water-table decline by the KHG area as if each centimetre of decline were a centimetre of water lost, which ignores that peat releases only part of its volume when it drains (its specific yield, about 0.3 near the surface). It also estimated a canal emptying time of 730 to 770 days by assuming canals lose water only by open-water evaporation, which the authors themselves called unrealistic, since canals lose most of their water by seepage into the peat. Chapter 8 returns to how the study's water balance was reproduced.

## 2.7 Structure of this report

Chapter 3 describes the data and how they were curated. Chapters 4 to 9 follow the chain: terrain, delineation, national and sub-KHG prioritisation, neraca air and interventions. Chapter 10 compares the KHG, chapter 11 lists the limitations and the decisions needed from KLH and the World Bank, and the annexes hold the references, the glossary and the parameter register.
The national and sub-KHG rankings use default weights proposed by the project for agreement with KLH and the World Bank; the weights can be adjusted in the dashboard. The groundwater model in chapter 8 is in development.
