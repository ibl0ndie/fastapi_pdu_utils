from enum import Enum

class LogFile(str, Enum):
    default = "default.log"
    migration = "migration"
    vm_reg = "vm_reg"
    environmental = "environmental"
    preventive = "preventive"
