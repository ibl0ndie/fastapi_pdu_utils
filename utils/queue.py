import json
import os
from pydantic import BaseModel

class Queue:
    def __init__(self, file_name):
        self.queue = []
        self.max_amount = 100
        self.length = 0
        self.file_name = file_name
        self.save_ct = 0
        
        try:
            with open(self.file_name, 'r') as ofile:
                self.queue = json.loads(ofile.read())  # Deserialize from JSON
                self.length = len(self.queue)
        except Exception as e:
            print("error at reading file ", self.file_name)
            print(e)
            self.save_to_file()
    
    def push(self, data):
        if len(self.queue) == self.max_amount:
            self.queue.pop(0)
        self.queue.append(
            data.dict() if hasattr(data, 'dict') else data
        )
        self.length = len(self.queue)

        if self.max_amount == 1 or self.save_ct == 3:
            self.save_to_file()
        self.save_ct += 1

    def save_to_file(self):
        self.save_ct = 0
        try:
            with open(self.file_name, 'w') as ofile:
                json_data = [item.dict() if isinstance(item, BaseModel) else item for item in self.queue]
                json.dump(json_data, ofile, indent=4)
                ofile.flush()
                os.fsync(ofile.fileno())
            print(f"Data successfully saved to {self.file_name}.")
        except Exception as e:
            print(f"Error writing to file {self.file_name}. Reason: {e}")

    def change_max_amount(self, new_max_amount):
        self.max_amount = new_max_amount

    def get_data(self, num=100):
        num = int(num)
        length = self.length
        if num > length:
            return self.queue
        else:
            return self.queue[-num:length]

    def empty_queue(self):
        self.queue = []
        self.length = 0
        self.save_to_file()
