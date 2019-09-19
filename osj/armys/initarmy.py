from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

class InitArmy(army.Army):
    def __init__(self, bot):
        super().__init__(bot, bot.map.points[5], bot.map.points[2])
        self.bunker = None
        self.name = "InitArmy"
        self.state = 0
    
    def onAddUnit(self, unitw):
        if unitw.unit.type_id == UnitTypeId.MARAUDER and unitw.unit.position.distance_to_point2(self.bot.map.points[0]) < 8:
            self.getRideShip(unitw, self.bot.map.points[5], self.bot.map.points[7], force=True)
        elif unitw.unit.type_id == UnitTypeId.BUNKER:
            if unitw.unit.distance_to(self.bot.map.points[2]) < 10:
                self.bunker = unitw
                self.bunker.state = 1
    
    async def step(self):
        if self.patrolship == None:
            newone = self.getFreeShip()
            if newone != None:
                self.setPatrolship(newone)
                newone.ready = False
        else:
            self.center = self.patrolship.unit.position

        actions = list()
        if self.bunker != None:
            if self.bunker.isalive:
                self.center = self.bunker.unit.position
        else:
            self.center = self.start

        if self.bot.tracker.my_gold == 1:
            self.bunker.state = 2
            self.center = self.bot.map.points[16]
        elif self.bot.tracker.my_gold == 2:
            self.bunker.state = 2
            self.center = self.bot.map.points[15]
        else:
            self.bunker.state = 1

        actions.extend(await self.updateUnits())
        return actions