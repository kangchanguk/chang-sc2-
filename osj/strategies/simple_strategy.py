from . import strategy
from ..armys import initarmy, tankarmy, homearmy, pusharmy
from sc2.ids.unit_typeid import UnitTypeId
from ..units import unitwrapper

class SimpleStrategy(strategy.Strategy):
    def __init__(self, bot):
        super().__init__(bot)
        self.homearmy = None
        self.tankarmy = None
        self.pusharmy = None

    def on_start(self):    
        self.armys.append(initarmy.InitArmy(self.bot))
        self.homearmy = homearmy.HomeArmy(self.bot)
        self.tankarmy = tankarmy.TankArmy(self.bot.map.points[7], self.bot.map.points[8], self.bot)
        self.pusharmy = pusharmy.PushArmy(self.bot, self.tankarmy, self.bot.map.points[3])
        self.armys.append(self.homearmy)
    
    
    def addUnit(self, unit):
        if isinstance(unit, unitwrapper.UnitWrapper):
            typ = unit.unit.type_id
        else:
            typ = unit.type_id
        if typ == UnitTypeId.MARINE and self.homearmy.unit_count[0] < 4:
            self.homearmy.addUnit(unit)
        else:
            if self.bot.rtime <= 60:
                self.armys[0].addUnit(unit)
                return
                
            if typ == UnitTypeId.MEDIVAC:
                if self.tankarmy.patrolship == None:
                    self.tankarmy.addUnit(unit)
                    return
                elif self.pusharmy.patrolship == None:
                    self.pusharmy.addUnit(unit)
                    return
    
            if self.tankarmy.defence_power < 40 or self.tankarmy.is_retreat or ((typ == UnitTypeId.SIEGETANK or typ == UnitTypeId.SIEGETANKSIEGED) and self.tankarmy.unit_count[4] < 3):
                self.tankarmy.addUnit(unit)
            else:
                self.pusharmy.addUnit(unit)

    async def step(self, iteration):
        if isinstance(self.armys[0], initarmy.InitArmy) and self.bot.rtime > 59:
            self.armys[0].give_all(self.tankarmy)
            self.armys[0] = self.tankarmy
            self.armys.append(self.pusharmy)
        return await self.update()