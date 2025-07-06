from fastapi import APIRouter
from typing import List
from pydantic import ValidationError, parse_obj_as

# Import your models and queues here
from utils.models import (
    MigrationModel,
    GainAfterModel,
    GainBeforeModel,
    VmPlacementModel,
)
from utils.queues import (
    queue_temperature,
    queue_maintenance,
    queue_migration,
    queue_gain_after,
    queue_gain_before,
    queue_placement,
)

router = APIRouter(prefix="/prom/get_chart_data")


@router.get("/temperature/{n}")
async def get_limited_temperature_chart_data(n: int):
    data = queue_temperature.get_data(n)
    return {"data": data}

@router.get("/temperature")
async def get_all_temperature_chart_data():
    data = queue_temperature.get_data()
    return {"data": data}

@router.get("/maintenance/{n}")
async def get_limited_maintenance_chart_data(n: int):
    data = queue_maintenance.get_data(n)
    return {"data": data}

@router.get("/maintenance")
async def get_all_maintenance_chart_data():
    data = queue_maintenance.get_data()
    return {"data": data}

@router.get("/migration")
async def get_migration_chart_data():
    data = queue_migration.get_data()
    try:
        parsed_data = parse_obj_as(List[MigrationModel], data)
    except ValidationError as e:
        return {"error": "Data validation failed", "details": e.errors()}
    return parsed_data[0] if parsed_data else parsed_data

@router.get("/gain_after")
async def get_gain_after_chart_data():
    data = queue_gain_after.get_data()
    try:
        parsed_data = parse_obj_as(List[GainAfterModel], data)
    except ValidationError as e:
        return {"error": "Data validation failed", "details": e.errors()}
    return parsed_data[0] if parsed_data else parsed_data

@router.get("/gain_before")
async def get_gain_before_chart_data():
    data = queue_gain_before.get_data()
    try:
        parsed_data = parse_obj_as(List[GainBeforeModel], data)
    except ValidationError as e:
        return {"error": "Data validation failed", "details": e.errors()}
    return parsed_data[0] if parsed_data else parsed_data

@router.get("/vm_placement")
async def get_vm_placement_chart_data():
    data = queue_placement.get_data(1)
    try:
        parsed_data = parse_obj_as(List[VmPlacementModel], data)
    except ValidationError as e:
        return {"error": "Data validation failed", "details": e.errors()}
    return parsed_data[0] if parsed_data else parsed_data
