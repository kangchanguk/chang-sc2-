from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

class TankAiArmy(army.Army):
    def __init__(self, bot, start, end, agent):
        super().__init__(bot, start, end)
        self.original_start = start
        self.name = "TankAiArmy"
        self.follow = Point2((0, 0))
        self.interval = 10
        self.is_retreat = False
        self.prevtime = bot.rtime
        self.agent = agent

    async def step(self):
        if self.bot.rtime - self.prevtime >= 1:
            self.agent.step()
            self.prevtime = self.bot.rtime
            self.state = self.agent.action // 2
            self.is_retreat = self.agent.action % 2 == 0
        self.agent.debug()

        if self.patrolship == None:
            newone = self.getFreeShip()
            if newone != None:
                self.setPatrolship(newone)
        elif self.patrolship.unit.distance_to(self.end) < 1:
            self.patrolship.end = self.bot.map.points[4]

       
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
            if self.state == 0:
                if tank.state == 0:
                    self.center = self.follow
                else:
                    self.center = tank.unit.position
            elif self.state == 1:
                if self.bot.known_enemy_units.exists:
                    self.center = self.bot.known_enemy_units.closest_to(tank.unit.position).position
                else:
                    self.center = self.end

            if self.follow.distance_to(tank.unit) > 1.5:
                self.follow = tank.unit.position
        else:
            if self.state == 0:
                self.center = self.start
            elif self.state == 1:
                self.center = self.end
        actions = list()
        actions.extend(await self.updateUnits())
        return actions