from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

class DisturbArmy(army.Army):
    def __init__(self, bot):
        super().__init__(bot, bot.map.points[0], bot.map.points[15])
        self.name = "Disturb"
        self.dropm = None
        self.medivac = None
        self.ride = False
        self.finished = False

    def onAddUnit(self, unitw):
        if self.dropm == None and unitw.unit.type_id == UnitTypeId.MARINE:
            self.dropm = unitw

    async def step(self):
        self.center = self.bot.map.points[15]

        if not self.ride:
            if self.dropm != None:
                if not self.dropm.isalive:
                    self.dropm = None
                    self.finished = False
                elif self.dropm.state != 2:
                    if self.getRideShip(self.dropm, self.center, self.bot.map.points[13]):
                        self.medivac = self.dropm.dropship
                        self.dropm.to = self.bot.map.points[14]
                        self.ride = True
        else:
            if not self.dropm.isalive:
                self.dropm = None
                self.finished = False
                self.ride = False
            elif self.dropm.state == 0:
                self.dropm.state = 2
            elif self.dropm.state == 2 and self.medivac.unit.distance_to(self.center) < 6:
                self.finished = True
            

        actions = list()
        actions.extend(await self.updateUnits())
        return actions