import sc2
from sc2.ids.unit_typeid import UnitTypeId
from . import unitwrapper

class Marine(unitwrapper.UnitWrapper):
    def __init__(self, tag, army):
        super().__init__(tag, army)
        self.priority.append(UnitTypeId.MARINE)
