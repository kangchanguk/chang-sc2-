from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2, Point3
import numpy as np
import osj.osjbot


def gettype(typeid):
        if typeid == UnitTypeId.MARINE:
            return 0
        elif typeid == UnitTypeId.MARAUDER:
            return 1
        elif typeid == UnitTypeId.MEDIVAC:
            return 2
        elif typeid == UnitTypeId.REAPER:
            return 3
        elif typeid == UnitTypeId.SIEGETANK or typeid == UnitTypeId.SIEGETANKSIEGED:
            return 4
        elif typeid == UnitTypeId.AUTOTURRET:
            return 6
        elif typeid == UnitTypeId.BUNKER:
            return 7
        elif typeid == UnitTypeId.COMMANDCENTER:
            return 8
        else:
            return 9

class Tracker:
    UNIT_VALUE = np.array([1, 3, 4, 10, 10, 10, 6, 9, 100, 1])
    def __init__(self, bot):
        self.my_gold = 3
        self.enemy_gold = 3
        self.total_my_gold = 0
        self.total_enemy_gold = 0
        self.enemy_counter = 0
        self.enemy_predict: dict = dict()
        self.enemy_tags = dict()
        self.unknown_units = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 2])
        self.total_units = np.array([5, 0, 0, 0, 0, 0, 0, 2, 1, 2])
        self.my_units = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.bot = bot
        self.prev_mineral = 0
        self.reward = 0
        self.finished = -1

    def addunit(self, unit):
        unittype = gettype(unit.type_id)
        self.my_units[unittype] += 1
        self.reward += self.UNIT_VALUE[unittype]

    def killunit(self, unit):
        unittype = gettype(unit.type_id)
        self.my_units[unittype] -= 1
        self.reward -= self.UNIT_VALUE[unittype]

    def on_start(self):
        self.total_my_gold = self.bot.minerals
        self.prev_mineral = self.bot.minerals
        self.total_enemy_gold = self.total_my_gold

    def nearestTank(self, pos: Point2):
        nearest = 100
        for tank in self.enemy_predict.values():
            if tank.type_id == UnitTypeId.SIEGETANKSIEGED:
                dist = pos.distance_to_point2(tank.position)
                if dist < nearest:
                    nearest = dist
        return nearest

    def getnearestTank(self, pos: Point2):
        nearest = 100
        nt = None
        for tank in self.enemy_predict.values():
            if tank.type_id == UnitTypeId.SIEGETANKSIEGED:
                dist = pos.distance_to_point2(tank.position)
                if dist < nearest:
                    nearest = dist
                    nt = tank
        return nt


    def is_visible(self, unit):
        for enemy in self.enemy_predict.values():
            if enemy.distance_to(unit) <= enemy.radius + enemy.sight_range + unit.radius:
                return True
        return False

    def estimate_enemy(self, pos, dist):
        estimation = self.unknown_units.copy()
        for enemy in self.enemy_predict.values():
            if enemy.distance_to_point2(pos) <= dist:
                unittype = gettype(enemy.type_id)
                estimation[unittype] += 1
        return estimation

    def evaluate_unit(self, unit, is_attack=False):
        unittype = unit.type_id
        val = 0
        if unittype == UnitTypeId.MARINE:
            val = 0.5 * (unit.health_percentage + 1)
        elif unittype == UnitTypeId.MARAUDER:
            val = 2 * (unit.health_percentage + 0.5)
        elif unittype == UnitTypeId.MEDIVAC:
            val = 3
        elif unittype == UnitTypeId.REAPER:
            val = (unit.energy // 50 * 6) + 1
        elif unittype == UnitTypeId.SIEGETANKSIEGED or unittype == UnitTypeId.SIEGETANK:
            val = 7 - (unit.health_percentage) * 2
            if not is_attack:
                val += 2
        elif unittype == UnitTypeId.AUTOTURRET and not is_attack:
            val = 6 - unit.health_percentage * 3
        elif unittype == UnitTypeId.BUNKER and not is_attack:
            val = unit.health_percentage * 9

        return val

    def evaluate_units(self, units, is_attack=False):
        val = 0
        for unit in units:
            val += self.evaluate_unit(unit, is_attack)
        return val
    
    def evaluate_unknowns(self):
        return self.unknown_units[0] + self.unknown_units[1] * 3 + self.unknown_units[2] * 4 + self.unknown_units[3] * 10 + self.unknown_units[4] * 10

    def step(self):
        self.enemy_gold = 7
        if self.bot.units.exists:
            for i in range(0, 5):
                if self.bot.units.closest_distance_to(self.bot.map.points[i]) <= 7:
                    self.enemy_gold -= 1 + (i % 2 == 1)
        self.my_gold = self.bot.vespene
        if self.my_gold == 0:
            self.reward -= 0.01
        if self.prev_mineral < self.bot.minerals:
            self.total_my_gold += self.my_gold
            self.total_enemy_gold += self.enemy_gold
            self.enemy_counter += self.enemy_gold
            if self.enemy_counter > 0:
                self.enemy_counter -= 10
                toadd = (self.total_enemy_gold // 10) % 10
                if toadd % 2 == 1:
                    unittype = 0
                elif toadd == 2:
                    unittype = 2
                elif toadd == 8:
                    unittype = 3
                elif toadd == 0:
                    unittype = 4
                else:
                    unittype = 1
                self.total_units[unittype] += 1
                self.reward -= self.UNIT_VALUE[unittype]
        self.prev_mineral = self.bot.minerals

        visibles = self.bot.known_enemy_units
        self.unknown_units = self.total_units.copy()
        for unit in visibles:
            unittype = gettype(unit.type_id)
            if unittype == 6 and not unit.tag in self.enemy_tags:
                self.total_units[unittype] += 1
                self.unknown_units[unittype] += 1
                self.reward -= self.UNIT_VALUE[unittype]
            self.enemy_predict[unit.tag] = unit
            self.enemy_tags[unit.tag] = unit
            self.unknown_units[unittype] -= 1
        todel = set()
        
        for tag in self.bot.state.dead_units:
            if tag in self.enemy_tags:
                if tag in self.enemy_predict:
                    todel.add(tag)
                unit = self.enemy_tags[tag]
                unittype = gettype(unit.type_id)
                self.total_units[unittype] -= 1
                self.reward += self.UNIT_VALUE[unittype]
                del self.enemy_tags[tag]


        for tag, unit in self.enemy_predict.items():
            if self.bot.is_visible(unit.position) and visibles.find_by_tag(tag) == None:
                todel.add(tag)
            
        for key in todel:
            del self.enemy_predict[key]

        if osj.osjbot.DEBUG:
            self.bot._client.debug_text_screen(f"Total Gold:{self.total_my_gold}\nTotal Enemy Gold:{self.total_enemy_gold}\nTotal my units:{self.my_units}\nTotal Enemy Units:{self.total_units}\nTotal Unknown Enemys:{self.unknown_units}\nTotal Reward:{self.reward}", pos=(0.02, 0.14), size=15)

        if self.my_units[8] == 0:
            self.finished = 2
        elif self.total_units[8] == 0:
            self.finished = 1
        elif self.bot.rtime > 600:
            if self.total_enemy_gold > self.total_my_gold:
                self.finished = 2
            elif self.total_enemy_gold < self.total_my_gold:
                self.finished = 1
            else:
                self.finished = 0

        