from fastapi import APIRouter
from typing import Dict

from pydantic import ValidationError
from your_project.models import (
    MaintenanceModel,
    TemperatureModel,
    MigrationModel,
    GainBeforeModel,
    GainAfterModel,
    VmPlacementModel,
    MigrationDecModel,
    MigrationMessageModel,
    SaveMigrationModel,
)
from your_project.queues import (
    queue_temperature,
    queue_maintenance,
    queue_migration,
    queue_gain_after,
    queue_gain_before,
    queue_placement
)

router = APIRouter(prefix="/prom")

# Simulated in-memory store for messages
migration_text = ""
message_ew = {'messages': [{'message': 'Current power utilization :420.5 Watt <br>Proposed power utilization: 405.3<br>Expected power gain: %3.58', 'show': 1, 'message_id': 1}]}


@router.post('/push/maintenance_data')
async def push_chart_data_maintenance(data: MaintenanceModel):
    queue_maintenance.push(data)
    return data


@router.post('/push/temperature_data')
async def push_chart_data_temperature(data: TemperatureModel):
    queue_temperature.push(data)
    return data


@router.post('/migration2/decisions')
async def get_migration_decisions(data: MigrationDecModel):
    for message in message_ew['messages']:
        if data.message_id == message['message_id'] and data.status == 'decline':
            message['show'] = 0
    return {"status": "updated", "messages": message_ew}


@router.post('/push/migration_text')
async def save_new_migration(data: MigrationMessageModel):
    global message_ew
    gain_dict = data.data
    migration_text = (
        f"Current Power: {gain_dict['power_cur']}<br>"
        f"Proposed Power: {gain_dict['pow_prop']}<br>"
        f"Gain: {gain_dict['gain']}"
    )
    message_ew = {'messages': [{'message': migration_text, 'show': 1, 'message_id': 1}]}
    return data


@router.post('/save/migration')
async def save_new_migration(data: SaveMigrationModel):
    print(data)
    return {"status": "saved"}


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
