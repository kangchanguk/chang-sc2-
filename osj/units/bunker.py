import sc2
from . import unitwrapper
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

class Bunker(unitwrapper.UnitWrapper):
    def __init__(self, tag, army):
        super().__init__(tag, army)
        self.load_type = {UnitTypeId.MARINE, UnitTypeId.MARAUDER}

    async def step(self, enemys):
        self.update()
        if self.unit.cargo_used >= 4:
            self.load_type = {UnitTypeId.MARAUDER}
        else:
            self.load_type = {UnitTypeId.MARINE, UnitTypeId.MARAUDER}


        if self.state == 1:
            toloads = self.army.bot.units.of_type(self.load_type)
            if toloads.exists:
                unit = toloads.closest_to(self.unit.position)
                if unit.distance_to(self.unit) < 4:
                    return self.unit(AbilityId.LOAD_BUNKER, unit)
        elif self.state == 2:
            return self.unit(AbilityId.UNLOADALL_BUNKER)
