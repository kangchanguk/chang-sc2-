from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point3

class DropArmy(army.Army):
    def __init__(self, bot, start, end, droppos):
        super().__init__(bot, start, end)
        self.name = "Drop"
        self.droppos = droppos
        self.isup = self.bot.map.height_map[int(start.x - 12), int(start.y - 12)] < self.bot.map.height_map[int(droppos.x - 12), int(droppos.y - 12)]
        self.state = 1
    
    async def step(self):
        self.center = self.end

        for unitw in self.unitws:
            if unitw.unit.type_id in (UnitTypeId.MARAUDER, UnitTypeId.MARINE, UnitTypeId.SIEGETANK) and unitw.state == 0:
                if (not self.isup and unitw.unit.position3d.z > 11) or (self.isup and unitw.unit.position3d.z < 11):
                    self.getRideShip(unitw, self.start, self.droppos, force=True)

        actions = list()

        actions.extend(await self.updateUnits())
        return actions