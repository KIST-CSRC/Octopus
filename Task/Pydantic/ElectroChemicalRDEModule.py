
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union

class ElectroChemicalRDEModule_Type(BaseModel):
    Type: str = ""

class ElectroChemicalRDEModule_ValueDimension(BaseModel):
    Value: Union[int, float] = 0
    Dimension: str = ""

class ElectroChemicalRDEModule_SetupElectrode_Data(BaseModel):
    ElectrodeType: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_Calibrate_Data(BaseModel):
    CalibrationStandard: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_LoadSample_Data(BaseModel):
    SampleVolume: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_AdjustRotation_Data(BaseModel):
    RotationSpeed: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_ApplyPotential_Data(BaseModel):
    Potential: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_RecordCurrent_Data(BaseModel):
    Duration: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_PerformCV_Data(BaseModel):
    ScanRate: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_PerformLPR_Data(BaseModel):
    ScanRate: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_PerformEIS_Data(BaseModel):
    FrequencyRange: ElectroChemicalRDEModule_ValueDimension
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_ChangeSolution_Data(BaseModel):
    NewSolution: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_CleanElectrode_Data(BaseModel):
    CleaningMethod: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_AnalyzeData_Data(BaseModel):
    Method: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]

class ElectroChemicalRDEModule_PerformanceTest_Data(BaseModel):
    TestType: ElectroChemicalRDEModule_Type
    Device: Dict[str, Any]
