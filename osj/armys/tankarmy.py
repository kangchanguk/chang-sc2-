from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

class TankArmy(army.Army):
    def __init__(self, bot, start, end):
        super().__init__(bot, start, end)
        self.original_start = start
        self.name = "TankArmy"
        self.is_retreat = False
        self.follow = Point2((0, 0))

    async def step(self):
        if self.patrolship == None:
            newone = self.getFreeShip()
            if newone != None:
                self.setPatrolship(newone)
        elif self.patrolship.unit.distance_to(self.end) < 1:
            self.patrolship.end = self.bot.map.points[4]

        self.is_retreat = self.bot.tracker.nearestTank(self.original_start) < 15
        if self.bot.known_enemy_units.exists:
            self.is_retreat = self.is_retreat or (not self.bot.tracker.evaluate_units(self.bot.units.closer_than(4, self.original_start)) > 10 and self.bot.known_enemy_units.closer_than(4, self.original_start).exists)
        if self.is_retreat:
            self.start = self.bot.map.points[0]
        else:
            self.start = self.original_start

        tank = None
        for unitw in self.unitws:
            if (unitw.unit.type_id == UnitTypeId.SIEGETANK or unitw.unit.type_id == UnitTypeId.SIEGETANKSIEGED):
                if self.is_retreat:
                    unitw.to = self.bot.map.points[5]
                else:
                    unitw.to = self.bot.map.points[8]
                if unitw.unit.position.distance_to_point2(self.bot.map.points[0]) < 8 and not self.is_retreat and unitw.state == 0:
                    self.getRideShip(unitw, self.bot.map.points[5], self.bot.map.points[7], self.unit_count[4] <= 1)
                if unitw.state >= 0:
                    if tank == None:
                        tank = unitw
                    elif tank.unit.distance_to(self.end) > unitw.unit.distance_to(self.end):
                        tank = unitw

        if tank != None:
            if tank.state == 0:
                self.center = self.follow
            else:
                self.center = tank.unit.position

            if self.follow.distance_to(tank.unit) > 1.5:
                self.follow = tank.unit.position

            closest_distance = 100
            if self.bot.known_enemy_units.exists:
                closest = self.bot.known_enemy_units.filter(lambda u : u.can_attack_ground)
                if closest.exists:
                    closest = closest.closest_to(tank.unit.position)
                    closest_distance = tank.unit.distance_to(closest)
        
            if closest_distance < 8:
                self.state = 1
                self.center = closest.position
            elif self.bot.tracker.nearestTank(tank.unit.position) <= 13.5 + tank.unit.radius:
                self.state = 1
                self.center = self.bot.tracker.getnearestTank(tank.unit.position).position
            else:
                self.state = 0
        else:
            self.center = self.start
            self.state = 0

        actions = list()
        actions.extend(await self.updateUnits())
        return actions