import sc2
from sc2.ids.unit_typeid import UnitTypeId
from . import unitwrapper

class AutoTurret(unitwrapper.UnitWrapper):
    def __init__(self, tag, army):
        super().__init__(tag, army)
        self.priority += [UnitTypeId.MARAUDER, UnitTypeId.AUTOTURRET]

        
    async def step(self, enemys):
        self.update()
        inrange = enemys.in_attack_range_of(self.unit)
        for pri in self.priority:
            alsopri = inrange.of_type((pri))
            if alsopri.exists:
                lowest = alsopri.first
                for tohit in alsopri:
                    if lowest.health > tohit.health:
                        lowest = tohit
                return self.unit.attack(lowest)

        if inrange.exists:
            return self.unit.attack(self.army.center)
        return None