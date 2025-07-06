from .queue import Queue

queue_maintenance = Queue("maintenance_save.json")
queue_temperature = Queue("temperature_save.json")
queue_migration = Queue("migration_save.json")
# queue_migration_prime = Queue("migration_prime_save.json")
queue_migration.change_max_amount(1)
# queue_migration_prime.change_max_amount(1)
queue_gain_before = Queue("gain_before_save.json")
queue_gain_before.change_max_amount(1)
queue_gain_after = Queue("gain_after_save.json")
queue_gain_after.change_max_amount(1)
queue_placement = Queue("gain_vm_placement.json")
queue_placement.change_max_amount(1)
