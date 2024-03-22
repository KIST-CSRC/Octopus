# OCTOPUS (Operation Control system for Task Optimization and job Parallelization with User-optimal Schedulers)

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

# User Manual
## Using conda
```
conda env create -f requirements_conda.txt
```

## Using pip
```
pip install -r requirements_pip.txt
```
# Prerequisites
[Prerequisties information is reported here.](prerequisties.md)

# Script architecture
```
Master Node
├── Algorithm
│   └── Automated: Automated experimentation
│   └── Bayesian: Bayesian optimization
│   └── Loss: loss function
│   └── SaveModel: directory of model pickle
├── Analysis
│   └── AnalysisUV.py: extract property from raw spectrum
├── DB
│   └── DB_Class.py: link master node with MongoDB
├── Job
│   └── Job_Class.py: realize closed-loop experimentation
│   └── JobSchduler_Class.py: control & manage jobs
│   └── JobTrigger.py: criteria of next job execution
└── Log
│   └── Client: include log file of client
│   └── Master: include log file of master
│   └── MessageAPI: consists of individual messenger 
│                   (telegram, facebook, kakaotalk, line, mail, dooray)
│   └── DigitalSecretary.py: integrated MessageAPI
│   └── Logging_Class.py: report all progress of client and all components of master node
│   └── Information.json: include user information about popular messenger 
│                         (telegram, facebook, kakaotalk, line, mail, dooray)
├── Resource
│   └── ResourceManager.py: update module information & manage module resource
├── TaskAction
│   └── TaskGenerator_Class.py: abstract experimental task considering job script information
│   └── TaskScheduler_Class.py: control task for each modules depending on scheduling modes
│   └── ActionTranslator_Class.py: digitalize abstracted task for each modules
│   └── ActionExecutor.py: data encoding & decoding, transfer & receive action data
├── USER
├── UserManager
│   └── user.db: store user information (ex. username, password)
│   └── UserManager_Class.py: manage user information
├── client.py: activate client object
└── master_node.py: activate master node after modules activation
```
# How to work
1. If you activate all modules, then exectue below command.
```bash
python master_node.py
```
2. activate client.py
```bash
python Client.py
```
3. input username, password in prompt.

# Benefit
Our study highlights both capabilities of the operation control system with user-optimal schedulers to manage various experiments without human intervention and to obtain outstanding operational efficiency for automated or autonomous experimentations.

# Reference
1. H. J. Yoo, N. Kim, H. Lee, D. Kim, L. T. C. Ow, H. Nam, C. Kim, S. Y. Lee, K.-Y. Lee, D. Kim, S. S. Han, Bespoke Metal Nanoparticle Synthesis at Room Temperature and Discovery of Chemical Knowledge on Nanoparticle Growth via Autonomous Experimentations. Adv. Funct. Mater. 2024, 2312561. https://doi.org/10.1002/adfm.202312561