import sc2
from . import unitwrapper
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.units import Units

class SiegeTank(unitwrapper.UnitWrapper):
    def __init__(self, tag, army, tracker):
        super().__init__(tag, army)
        self.tracker = tracker
        self.priority += [UnitTypeId.MARAUDER, UnitTypeId.AUTOTURRET]

    async def step(self, enemys):
        if self.isriding:
            return None
        self.update()
        
        if self.state == -1:
            return self.unit.attack(self.dropship.start)
        elif self.state == -2:
            return None

        neartank = self.tracker.nearestTank(self.unit.position)
        closest = 100
        ground_enemys = enemys
        if ground_enemys.exists:
            ground_enemys = enemys.of_type({UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED, UnitTypeId.REAPER, UnitTypeId.AUTOTURRET, UnitTypeId.BUNKER, UnitTypeId.COMMANDCENTER})
        if ground_enemys.exists:
            closest = ground_enemys.closest_to(self.unit)
            closest = self.unit.distance_to(closest) - closest.radius
        if self.to != None:
            to = self.to
        else:
            to = self.army.center

        dist_to = self.unit.distance_to(to)

        if self.state == 1:
            if self.unit.type_id == UnitTypeId.SIEGETANK:
                return self.unit(AbilityId.SIEGEMODE_SIEGEMODE)

            if closest > 13 and (neartank > 15.5 + self.unit.radius or (not self.tracker.is_visible(self.unit) and neartank > 13 + self.unit.radius)) and dist_to > 2.5:
                self.state = 0
                return self.unit(AbilityId.UNSIEGE_UNSIEGE)

            toattack = ground_enemys.in_attack_range_of(self.unit)

            for pri in self.priority:
                alsopri = toattack.of_type((pri))
                if alsopri.exists:
                    lowest = alsopri.first
                    for tohit in alsopri:
                        if lowest.health > tohit.health:
                            lowest = tohit
                    return self.unit.attack(lowest)
            return self.unit.attack(to)
        else:
            if self.unit.type_id == UnitTypeId.SIEGETANKSIEGED:
                return self.unit(AbilityId.UNSIEGE_UNSIEGE)

            if dist_to < 2.5:
                self.state = 1
                return self.unit(AbilityId.SIEGEMODE_SIEGEMODE)

            if not self.tracker.is_visible(self.unit):
                if neartank < 13 + self.unit.radius or closest <= 13:
                    self.state = 1
                    return self.unit(AbilityId.SIEGEMODE_SIEGEMODE)
            else:
                if neartank < 14.5 + self.unit.radius:
                    return self.unit.move(self.army.start)
                elif neartank < 15.5 + self.unit.radius or closest <= 13:
                    self.state = 1
                    return self.unit(AbilityId.SIEGEMODE_SIEGEMODE)

            return self.unit.attack(to)


            