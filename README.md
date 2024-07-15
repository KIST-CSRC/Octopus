# OCTOPUS (Operation Control System for Task Optimization and Job Parallelization via a User-optimal Scheduler)

# Background
The Materials Acceleration Platform (MAP) has been facilitated to material discovery through widespread exploration of the chemical space. However, severe problems in MAP.
1. The development of operating system for MAP could inevitably face complex architecture to manipulate diverse experiments simultaneously. 
2. As a number of experimentations execute, overlap challenges of experimental module or device could exponentially derive resource inefficiency from bottleneck of chemical process.

Therefore, we report OCTOPUS for MAP; following two strategies below.
1. Operation Control system for Materials Acceleration Platform (MAP)
2. User-optimal Schedulers for overlapp issues and resource allocation in realisitic platform

# System Architecture of OCTOPUS

<p align="center">
  <img src="paper_result/TOC.jpg" width="50%" height="50%" />
</p>

## Operation Control system for MAP

### 1. Concepts
1. Homogeneity
2. Scalability
3. Safety
4. Versatility

### 2. Technique
1. client/server-based central management system to execute closed-loop experimentation as job for multiple clients
2. network protocol-aided process modularization and utilization. OCTOPUS could truly four benefits of efficiency in MAP.

## User-optimal Schedulers for overlap issues and resource allocation in realisitic platform

### 1. Concepts
1. Module overlap due to device standby times
2. Device overlap such as device collision or device sharing environments
3. Job or task delay due to limitation of module resource

### 2. Technique
1. Job parallelization using device standby times
2. Task optimization with masking table
3. The closed-packing schedule for optimizing module resource efficiency in realistic platform

# Prerequisites
[Prerequisties information is reported here.](prerequisties.md)

# Description of architecture
[Description of architecture is reported here.](paper_result/architecture_description.png)

# How to work
## 1. Activate all modules which connect to master node
```bash
python module_node.py
```
## 2. Activate master node
If you activate all modules, then activate master node.
```bash
python master_node.py
```
## 3. Generate job script 
### 3-1. Job script template for each module
Client should customize [template of job script](JobScriptTemplate/template.json). Below json format represents template of job script.
```json
{
    "metadata" : 
    {
        "subject":"[OCTOPUS] template of job script",
        "group":"",
        "logLevel":"DEBUG"
    },
    "algorithm":
    {
        "model":"Manual",
        "totalExperimentNum":0,
        "inputParams":[]
    },
    "process": {}
}
```
In key of algorithm, it depends on model selection, "Manual" or AI based models, such as "BayesianOptimization" or "DecisionTree".

`Manual`
```json
    "algorithm":
    {
        "model":"Manual",
        "totalExperimentNum":4,
        "inputParams":[
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            }
        ]
    }
```
`BayesianOptimization`
```json
    "algorithm":
        {
            "model":"BayesianOptimization",
            "batchSize":6,
            "totalCycleNum":3,
            "verbose":0,
            "randomState":0,
            "sampling":{
                "samplingMethod":"latin",
                "samplingNum":20
            },
            "acq":{
                "acqMethod":"ucb",
                "acqSampler":"greedy",
                "acqHyperparameter":{
                    "kappa":10.0
                }
            },
            "loss":{
                "lossMethod":"lambdamaxFWHMintensityLoss",
                "lossTarget":{
                    "GetAbs":{
                        "Property":{
                            "lambdamax":573
                        },
                        "Ratio":{
                            "lambdamax":0.9,
                            "FWHM":0.03, 
                            "intensity":0.07
                        }
                    }
                }
            }, 
            "prange":{
                "AddSolution=AgNO3_Concentration" : [25, 375, 25],
                "AddSolution=AgNO3_Volume" : [100, 1200, 50],
                "AddSolution=AgNO3_Injectionrate" : [50, 200, 50]
            },
            "initParameterList":[],
            "constraints":[]
        }
```
### 3-2. Customize value of `process` key using [JobScriptTemplate/{ModuleName}.json](JobScriptTemplate)
Once client execute Copilot of OCTOPUS, job script template of each module should generate in [JobScriptTemplate](JobScriptTemplate) directory. 

For example, `BatchSynthesis`
```json
    "process":
    {
        "Synthesis":{
            "BatchSynthesis":{
                "Sequence":[
                  "BatchSynthesis_AddSolution=Citrate",
                  "BatchSynthesis_AddSolution=H2O2", 
                  "BatchSynthesis_AddSolution=NaBH4",
                  "BatchSynthesis_Stir",
                  "BatchSynthesis_Heat",
                  "BatchSynthesis_Mix", 
                  "BatchSynthesis_AddSolution=AgNO3", 
                  "BatchSynthesis_React"
                ],
                "fixedParams":
                {
                    "BatchSynthesis_AddSolution=H2O2_Concentration" : 375,
                    "BatchSynthesis_AddSolution=H2O2_Volume" : 1200,
                    "BatchSynthesis_AddSolution=H2O2_Injectionrate" : 200,
                    "BatchSynthesis_AddSolution=Citrate_Concentration" : 20,
                    "BatchSynthesis_AddSolution=Citrate_Volume" : 1200,
                    "BatchSynthesis_AddSolution=Citrate_Injectionrate" : 200,
                    "BatchSynthesis_AddSolution=NaBH4_Concentration" : 10,
                    "BatchSynthesis_AddSolution=NaBH4_Volume" : 3000,
                    "BatchSynthesis_AddSolution=NaBH4_Injectionrate" : 200,

                    "BatchSynthesis_Stir=StirRate":1000,
                    "BatchSynthesis_Heat=Temperature":25,
                    "BatchSynthesis_Mix=Time":300,
                    "BatchSynthesis_React=Time":2400
                }
            }
        }
    }
```

More detailed examples of job script in [USER/yoohj9475@kist.re.kr/job_script/test.json](USER/yoohj9475@kist.re.kr/job_script/test.json)

### cf) *USER directory structure*
```
USER
├── job_script: job script of client
├── DB (automated generation during job progress): material data. It also store in MongoDB
└── Log (automated generation during job progress): log file of all job progress 
```

## 4. Activate client.py
```bash
python Client.py
```

## 5. Input client ID, password in prompt.
In Copilot of OCTOPUS, OCTOPUS implement [Auth0 API for login process](paper_result/login_process.PNG). Therefore, you need to input client ID (email format) and password, addressed in Auth0.

## 6. Input commands and submit job
[Please refer command table.](paper_result/command_table.PNG)

# Benefit
Our study highlights both capabilities of the operation control system with user-optimal schedulers to manage various experiments without human intervention and to obtain outstanding operational efficiency for Manual or autonomous experimentations.

# Reference

- H. J. Yoo, N. Kim, H. Lee, D. Kim, L. T. C. Ow, H. Nam, C. Kim, S. Y. Lee, K.-Y. Lee, D. Kim, S. S. Han, Bespoke Metal Nanoparticle Synthesis at Room Temperature and Discovery of Chemical Knowledge on Nanoparticle Growth via Autonomous Experimentations. Adv. Funct. Mater. 2024, 2312561. https://doi.org/10.1002/adfm.202312561
