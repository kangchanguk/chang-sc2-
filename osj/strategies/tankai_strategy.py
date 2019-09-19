from . import strategy
from ..armys import disturbarmy, tankaiarmy, initarmy, droparmy, homearmy
from sc2.ids.unit_typeid import UnitTypeId
from ..units import unitwrapper

class TankAiStrategy(strategy.Strategy):
    def __init__(self, bot):
        super().__init__(bot)
        self.tankarmy = None
        self.disturbarmy = None
        self.initarmy = None
        self.homearmy = None
        self.agent = self.bot.agents["TankArmyAgent"]

    def on_start(self):    
        self.disturbarmy = disturbarmy.DisturbArmy(self.bot)
        self.initarmy = initarmy.InitArmy(self.bot)
        self.armys.append(self.initarmy)
        self.armys.append(self.disturbarmy)
        self.tankarmy = tankaiarmy.TankAiArmy(self.bot, self.bot.map.points[7], self.bot.map.points[8], self.agent)
        self.agent.set_army(self.tankarmy)
        self.homearmy = homearmy.HomeArmy(self.bot)
    
    def addUnit(self, unit):
        if isinstance(unit, unitwrapper.UnitWrapper):
            typ = unit.unit.type_id
        else:
            typ = unit.type_id
        if self.disturbarmy.dropm == None and typ == UnitTypeId.MARINE:
            self.disturbarmy.addUnit(unit)
        elif self.disturbarmy.finished == False and typ == UnitTypeId.MEDIVAC and self.disturbarmy.unit_count[2] == 0:
            self.disturbarmy.addUnit(unit)
        elif (typ == UnitTypeId.MARINE or typ == UnitTypeId.MARAUDER) and self.homearmy.attack_power < self.tankarmy.attack_power * 0.25:
            self.homearmy.addUnit(unit)
        else:
            self.armys[0].addUnit(unit)
        
    async def step(self, iteration):
        if self.disturbarmy.finished:
            self.disturbarmy.give_unit(self.armys[0], UnitTypeId.MEDIVAC)
        elif isinstance(self.armys[0], initarmy.InitArmy) and self.armys[0].unit_count[4] != 0:
            self.armys[0] = self.tankarmy
            self.initarmy.give_all(self.tankarmy)
            self.armys.append(self.homearmy)
        elif self.armys[0] == self.tankarmy and not self.tankarmy.is_retreat and self.tankarmy.end.distance_to(self.tankarmy.center) < 3 and self.bot.known_enemy_units.closer_than(9, self.tankarmy.center).empty:
            da = droparmy.DropArmy(self.bot, self.bot.map.points[8], self.bot.map.points[4], self.bot.map.points[6])
            self.tankarmy.give_all(da)
            self.armys[0] = da
        return await self.update()