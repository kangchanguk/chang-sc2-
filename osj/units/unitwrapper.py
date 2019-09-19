import sc2
import osj.osjbot
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units

class UnitWrapper:
    
    def __init__(self, tag, army):
        self.unit = None
        self.tag = tag
        self.state = 0
        self.prevhp = 0
        self.damaged = 0
        self.timer = 0
        self.skill_cooltime = 11
        self.dropship = None
        self.isalive = True
        self.isriding = False
        self.army = army
        self.ready = False
        self.priority = [UnitTypeId.SIEGETANKSIEGED, UnitTypeId.REAPER, UnitTypeId.SIEGETANK]
        self.to = None

    def check_alive(self, units: Units, deads):
        my_unit = units.find_by_tag(self.tag)
        self.isalive = not self.tag in deads
        if self.isalive:
            if my_unit == None:
                self.isriding = True
                self.state = -2
            else:
                self.unit = my_unit
                self.isriding = False
        return self.isalive

    def update(self):
        self.damaged = self.prevhp - self.unit.health
        self.prevhp = self.unit.health
        if self.timer > 0:
            self.timer -= self.army.bot.elapsed_time
        if self.state == -1:
            if self.dropship == None:
                self.state = 0
            elif not self.dropship.isalive or self.dropship.state != -4:
                self.dropship = None
                self.state = 0
        if self.state == -2:
            self.state = 0
            self.dropship = None

        if self.unit.distance_to(self.army.center) < 5:
            self.ready = True
        if osj.osjbot.DEBUG:
            self.army.bot._client.debug_text_world("{}: {}".format(self.army.name, self.state), self.unit.position3d, size=16)


    async def step(self, enemys):
        if self.isriding:
            return None
        self.update()

        if self.state == -1:
            return self.unit.attack(self.dropship.start)
        elif self.state == -2:
            return None
        else:
            inrange = enemys.in_attack_range_of(self.unit)
            
            if inrange.exists and self.timer <= 0:
                if self.unit.type_id == UnitTypeId.MARINE:
                    if self.unit.health > 35:
                        self.timer = self.skill_cooltime
                        return self.unit(AbilityId.EFFECT_STIM_MARINE)
                if self.unit.type_id == UnitTypeId.MARAUDER:
                    if self.unit.health > 90:
                        self.timer = self.skill_cooltime
                        return self.unit(AbilityId.EFFECT_STIM_MARAUDER)
            attacking_enemys = enemys.of_type({UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK, UnitTypeId.AUTOTURRET})
            friends = self.army.bot.units.of_type({UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK, UnitTypeId.AUTOTURRET}).tags_not_in({self.tag})
            closest = None
            closest_distance = 100
            closest_friend = None
            closest_friend_distance = 100
            if attacking_enemys.exists:
                closest = attacking_enemys.closest_to(self.unit)
                closest_distance = closest.distance_to(self.unit)
            if friends.exists:
                closest_friend = friends.closest_to(self.unit)
                closest_friend_distance = closest_friend.distance_to(self.unit)

            if self.to != None:
                target = self.to
            elif (self.army.state != 1 and self.army.bot.tracker.nearestTank(self.unit.position) < 14.5 + self.unit.radius):
                target = self.army.start
            elif closest_distance < self.unit.ground_range and self.unit.weapon_cooldown > 10:
                target = closest.position.towards(self.unit.position, self.unit.ground_range)
            elif closest_friend_distance < 0.5:
                target = closest_friend.position.towards(self.unit.position, 0.5)
            else:
                target = self.army.center

            if self.unit.weapon_cooldown > 3 and self.state != 2:
                return self.unit.move(self.unit.position.towards(target, 1))
            for pri in self.priority:
                alsopri = inrange.of_type((pri))
                if alsopri.exists:
                    lowest = alsopri.first
                    for tohit in alsopri:
                        if lowest.health > tohit.health:
                            lowest = tohit
                    return self.unit.attack(lowest)

            if inrange.exists:
                return self.unit.attack(target)

            if self.state == 2:
                return self.unit.move(target)
                
            if self.unit.distance_to(target) < 2:
                return None
            if self.army.state == 1 and self.ready:
                return self.unit.move(self.unit.position.towards(target, 1))
            return self.unit.move(target)