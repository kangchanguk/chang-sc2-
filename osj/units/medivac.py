import sc2
from . import unitwrapper
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
import math

class Medivac(unitwrapper.UnitWrapper):
    def __init__(self, tag, army):
        super().__init__(tag, army)
        self.start = Point2((0, 0))
        self.end = Point2((0, 0))
        self.toLoad = list()
        self.loadsize = 0
        self.enemyViewed = None
        self.burner = False
        self.safePos = Point2((0, 0))
        self.skill_cooltime = 8.6

    def setState(self, state, start=None, end=None):
        if self.state == 1:
            self.army.patrolship = None

        self.state = state

        if self.state == 1:
            self.army.patrolship = self

        if state != 0:
            self.start = start
            self.end = end

    def addLoad(self, unitw):
        if unitw.tag in self.toLoad:
            return True

        if self.unit.cargo_max >= self.loadsize + unitw.unit.cargo_size:
            self.toLoad.append(unitw)
            unitw.dropship = self
            unitw.state = -1
            self.loadsize += unitw.unit.cargo_size
            return True
        return False

    
    def check_alive(self, units, deads):
        super().check_alive(units, deads)
        if not self.isalive and self.state == 1:
            self.army.patrolship = None
        return self.isalive

    async def step(self, enemys):
        self.update()

        self.enemyViewed = enemys.closer_than(16, self.unit.position)
        
        if self.damaged > 0 and self.timer <= 0:
            return self.unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
    
        if self.state == -4:
            print(f"{self.loadsize} / {self.unit.cargo_used}")
            if self.loadsize <= self.unit.cargo_used:
                self.toLoad.clear()
                self.state = -5
                self.loadsize = 0
                return self.unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)

            for unitw in self.toLoad:
                if not unitw.isalive or unitw.unit.tag in self.unit.passengers_tags or unitw.state >= 0:
                    print(f"unit left {unitw.state} {unitw.isalive}")
                    self.toLoad.remove(unitw)
                    if not unitw.isalive or unitw.state >= 0:
                        self.loadsize -= unitw.unit.cargo_size
            if len(self.toLoad) > 0:
                return self.unit(AbilityId.LOAD_MEDIVAC, self.toLoad[0].unit)

        if self.state == -5:
            if self.damaged > 0:
                self.end = self.start
            if self.unit.distance_to(self.end) > 1:
                return self.unit.move(self.end)
            elif self.unit.cargo_used > 0:
                return self.unit(AbilityId.UNLOADALLAT_MEDIVAC, self.end)
            else:
                self.state = 0

        if self.state == 0:
            if enemys.empty:
                return self.unit.attack(self.army.center)

            self.start = self.army.start
            self.end = self.army.center
            if not self.ready:
                self.end = self.army.center
                self.start = self.army.bot.map.points[0]
        
        air_attack_enemys = enemys.filter(lambda u: u.can_attack_air or u.type_id == UnitTypeId.BUNKER)
        if air_attack_enemys.empty:
            if self.state == 1:
                return self.unit.move(self.end)
            else:
                return self.unit.attack(self.end)
        else:
            closest = air_attack_enemys.closest_to(self.unit.position)
            distance = closest.distance_to(self.unit) - self.unit.radius - 6.5
            if distance < 1:
                if self.unit.distance_to(self.start) < 1:
                    self.start = self.army.bot.map.points[0]
                return self.unit.move(self.start)
            elif distance < 2:
                return self.unit.hold_position()
            elif self.state == 1:
                return self.unit.move(self.end)
            else:
                return self.unit.attack(self.end)