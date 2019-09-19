from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

class HomeArmy(army.Army):
    def __init__(self, bot):
        super().__init__(bot, bot.map.points[0], bot.map.points[16])
        self.name = "HomeArmy"

    
    async def step(self):
        if self.bot.known_enemy_units.closer_than(11, self.start).exists:
            self.center = self.bot.map.points[15]
        else:
            self.center = self.bot.map.points[16]

        actions = list()
        actions.extend(await self.updateUnits())
        return actions