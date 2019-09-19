from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point3

class PushArmy(army.Army):
    def __init__(self, bot, mainarmy, end):
        self.mainarmy = mainarmy
        super().__init__(bot, mainarmy.center, end)
        self.name = "Push"
    
    async def step(self):
        if self.patrolship == None:
            newone = self.getFreeShip()
            if newone != None:
                self.setPatrolship(newone)
        elif self.patrolship.unit.distance_to(self.end) < 1 and self.enemy_power == 0:
            self.start = self.end
            self.end = self.bot.map.points[4]
            if self.patrolship != None:
                self.setPatrolship(self.patrolship)

        self.start = self.mainarmy.center
        self.bot._client.debug_text_world("{} power {}, enemy {}".format(self.name, self.attack_power, self.enemy_power), Point3((self.end.x, self.end.y + 3, 12)), size=16)
        if self.enemy_power + 10 > self.attack_power:
            self.state = self.mainarmy.state
            self.center = self.start
        else:
            self.state = 0
            self.center = self.end
        actions = list()

        actions.extend(await self.updateUnits())
        return actions