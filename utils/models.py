from typing import List, Dict
from pydantic import BaseModel, Field, validator

# Define all your Pydantic models here

class ApprovalRequest(BaseModel):
    approved: bool

class MigrationDecModel(BaseModel):
    message_id: int
    status: str

class TemperatureModel(BaseModel):
    power: str
    flag: str
    env_temp_cur: str
    now_timestamp: str
    future_timestamp: str
    env_temp_min: str
    power_future_min: str

class MigrationMessageModel(BaseModel):
    data: dict

class MaintenanceModel(BaseModel):
    power: str
    flag: str
    now_timestamp: str
    future_timestamp: str
    power_future_min: str
    positive_3p: str
    negative_3p: str
    positive_7p: str
    negative_7p: str

class MigrationModel(BaseModel):  # Use BaseModel if RootModel is custom, import accordingly
    root: Dict[str, dict]

class SaveMigrationModel(BaseModel):
    status: str
    data: dict

class GainAfterModel(BaseModel):
    past_power: float
    cur_power: float
    prop_power: float
    prop_ratio: float
    actual_ratio: float
    val_ratio: float
    val_difference: float

class GainBeforeModel(BaseModel):
    prop_gain: float
    prop_power: float
    cur_power: float

class VmPowerModel(BaseModel):
    status: str
    name: str
    power: float
    confg: dict

class VMStatus(BaseModel):
    active: List[VmPowerModel]
    inactive: List[VmPowerModel]

class PhysicalMachine(BaseModel):
    status: str
    name: str
    power_consumption: float
    vms: VMStatus

class VmPlacementModel(BaseModel):
    data_center: str
    id: int
    physical_machines: List[PhysicalMachine]

class EnvInputModel(BaseModel):
    number_of_steps: str = Field(..., pattern=r'^\d+$', description="Number of steps (numeric only)", example="3")
    script_time_unit: str = Field(..., pattern=r'^\d+$', description="Time unit in minutes (e.g., '1' or '5')", example="1")
    model_type: str = Field(..., min_length=1, max_length=10, description="Model type (string with 1-10 characters)", example="lstm")

class PreventiveInputModel(BaseModel):
    number_of_steps: str = Field(..., pattern=r'^\d+$', description="Number of steps (numeric only)", example="3")
    script_time_unit: str = Field(..., pattern=r'^\d+$', description="Time unit in minutes (e.g., '1' or '5')", example="1")
    model_type: str = Field(..., min_length=1, max_length=10, description="Model type (string with 1-10 characters)", example="lstm")

class VirtualMachineEstimationModel(BaseModel):
    estimation_method: str = Field(
        "indirect",
        min_length=1,
        max_length=10,
        description="Estimation Method type (string with 1-10 characters)",
        example="indirect"
    )
    model_type: str = Field(
        "mul_reg",
        min_length=1,
        max_length=10,
        description="Model type (string with 1-10 characters)",
        example="mul_reg"
    )

    @validator('estimation_method')
    def validate_estimation_method(cls, v):
        valid_methods = ["indirect", "direct"]
        if v not in valid_methods:
            raise ValueError(f"estimation_method must be one of {valid_methods}")
        return v

class MigrationWeightsModel(BaseModel):
    power: str = Field("0.25", pattern=r'^0(\.\d+)?$|^1(\.0+)?$', description="Weight for power factor")
    balance: str = Field("0.25", pattern=r'^0(\.\d+)?$|^1(\.0+)?$', description="Weight for balance factor")
    overload: str = Field("0.25", pattern=r'^0(\.\d+)?$|^1(\.0+)?$', description="Weight for overload factor")
    allocation: str = Field("0.25", pattern=r'^0(\.\d+)?$|^1(\.0+)?$', description="Weight for allocation factor")

class MigrationAdvicesModel(BaseModel):
    migration_method: str = Field(
        "migration_advices_la",
        description="Migration method",
        example="migration_advices_la"
    )
    migration_weights: MigrationWeightsModel = Field(
        default_factory=lambda: MigrationWeightsModel(),
        description="Migration weights configuration"
    )

class MigrationInputModel(BaseModel):
    script_time_unit: str = Field(
        "1",
        pattern=r'^\d+$',
        description="Time unit in minutes",
        example="1"
    )
    virtual_machine_estimation: VirtualMachineEstimationModel = Field(
        default_factory=lambda: VirtualMachineEstimationModel(),
        description="VM estimation config"
    )
    migration_advices: MigrationAdvicesModel = Field(
        default_factory=lambda: MigrationAdvicesModel(),
        description="Migration advice config"
    )
    block_list: List[str] = Field(
        default_factory=list,
        description="List of IP addresses to not include in migration",
        example=["10.150.1.190"]
    )

class InputDataModel(BaseModel):
    migration: MigrationInputModel
    environmental: EnvInputModel
    preventive: PreventiveInputModel
