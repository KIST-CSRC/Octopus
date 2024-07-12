
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union

class ValueDimension(BaseModel):
    Value: Union[int, float] = 0
    Dimension: str = ""

class MaterialType(BaseModel):
    Type: str = ""

class MethodType(BaseModel):
    Type: str = ""

class FromToType(BaseModel):
    Type: str = ""

class SolidStateModule_LoadSample_Data(BaseModel):
    SampleID: MaterialType
    Device: Dict[str, Any]

class SolidStateModule_AddPowder_Data(BaseModel):
    Material: MaterialType
    Amount: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_MixPowders_Data(BaseModel):
    Time: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_PressPowder_Data(BaseModel):
    Pressure: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Heat_Data(BaseModel):
    Temperature: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Cool_Data(BaseModel):
    Temperature: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Grind_Data(BaseModel):
    Time: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Pelletize_Data(BaseModel):
    Pressure: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Weigh_Data(BaseModel):
    Method: MethodType
    Device: Dict[str, Any]

class SolidStateModule_Transfer_Data(BaseModel):
    FromTo: FromToType
    Device: Dict[str, Any]

class SolidStateModule_Wash_Data(BaseModel):
    Solvent: MaterialType
    Volume: ValueDimension
    Device: Dict[str, Any]

class SolidStateModule_Dry_Data(BaseModel):
    Temperature: ValueDimension
    Time: ValueDimension
    Device: Dict[str, Any]
