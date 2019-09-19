from . import unitwrapper
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.units import Units

class Reaper(unitwrapper.UnitWrapper):
    def __init__(self, tag, army, bot):
        super().__init__(tag, army)
        self.bot = bot

    async def step(self, enemys):
        if self.isriding:
            return None
        self.update()
        if self.state == -1:
            return self.unit.attack(self.dropship.start)
        elif self.state == -2:
            return None

        if self.unit.health_percentage > 0.8 and self.unit.energy >= 50 and self.bot.tracker.nearestTank(self.unit.position) > 15:
            if enemys.exists:
                ground_enemys = enemys.of_type({UnitTypeId.AUTOTURRET, UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED, UnitTypeId.COMMANDCENTER})
                if ground_enemys.exists and (self.army.state == 1 or self.unit.energy == 150):
                    closest_threat = ground_enemys.closest_to(self.unit.position)
                    pos = closest_threat.position.towards(self.unit.position, 4.5)
                    pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                    return self.unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
            return self.unit.attack(self.army.center)
        else:
            return self.unit.move(self.bot.map.points[0])