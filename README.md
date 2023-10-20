# OCTOPUS (Operating Consolidation system for Task Optimization and Parallelization with Unsupervised Schedulers)

# Background
The Materials Acceleration Platform (MAP) has been facilitated to material discovery through widespread exploration of the chemical space. However, severe problems in MAP.
1. The development of operating system for MAP could inevitably face complex architecture to manipulate diverse experiments simultaneously. 
2. As a number of experimentations execute, superposition challenges of experimental module or device could exponentially derive resource inefficiency from bottleneck of chemical process.

Therefore, we report OCTOPUS for MAP; following two strategies below.
1. Operating Consolidation system for materials acceleration platform (MAP)
2. Unsupervised Schedulers for superposition issues and task allocation in realisitic platform

# System Architecture of OCTOPUS

<p align="center">
  <img src="paper_result\img\TOC.jpg" width="50%" height="50%" />
</p>


## Operating consolidation system for MAP

### 1. Concepts
1. Homogeneity
2. Scalability
3. Safety
4. Versatility

### 2. Technique
1. client/server-based central management system to execute closed-loop experimentation as job for multiple clients
2. network protocol-aided process modularization and utilization. OCTOPUS could truly four benefits of efficiency in MAP.

## Unsupervised Schedulers for superposition issues and task allocation in realisitic platform

### 1. Concepts
1. Module superposition due to task bottleneck times
2. Device superposition due to multiple task in device intersection
3. Job or task delay due to limitation of module resource

### 2. Technique
1. Job parallelization using bottleneck times
2. Task optimization with masking table
3. Closed-packing schedule for module resource efficiency in realistic platform

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
│   └── Automatic: Automated experimentation
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
├── Task
│   └── TaskGenerator_Class.py: abstract experimental task considering job script information
│   └── TaskScheduler_Class.py: digitalize abstracted task for each modules
│   └── TCP.py: data encoding & decoding, transfer & receive action data
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
Our study highlights both capabilities of the operating consolidation system with unsupervised schedulers to manage various experiments without human intervention and to obtain outstanding operational efficiency for automated or autonomous experimentations.

# Reference
1. Yoo, H. J., Kim, N., Lee, H., Kim, D., Ow, L. T. C., Nam, H., ... & Han, S. S. (2023). Bespoke Nanoparticle Synthesis and Chemical Knowledge Discovery Via Autonomous Experimentations. arXiv preprint arXiv:2309.00349.