from fastapi import APIRouter

from utils.models import (
    MaintenanceModel,
    TemperatureModel,
    MigrationModel,
    GainBeforeModel,
    GainAfterModel,
    VmPlacementModel,
)
from utils.queues import (
    queue_temperature,
    queue_maintenance,
    queue_migration,
    queue_gain_after,
    queue_gain_before,
    queue_placement
)

router = APIRouter(prefix="/prom")


@router.post('/push/maintenance_data')
async def push_chart_data_maintenance(data: MaintenanceModel):
    queue_maintenance.push(data)
    return data


@router.post('/push/temperature_data')
async def push_chart_data_temperature(data: TemperatureModel):
    queue_temperature.push(data)
    return data


@router.post('/push/migration_data')
async def push_chart_data_migration(data: MigrationModel):
    queue_migration.push(data.dict())
    return data


@router.post('/push/gain_before')
async def push_chart_data_data_gain_before(data: GainBeforeModel):
    queue_gain_before.push(data.dict())
    return data


@router.post('/push/gain_after')
async def push_chart_data_gain_after(data: GainAfterModel):
    queue_gain_after.push(data.dict())
    queue_migration.empty_queue()
    return data


@router.post('/push/vm_placement')
async def push_chart_data_vm_placement(data: VmPlacementModel):
    queue_placement.push(data.dict())
    return data
