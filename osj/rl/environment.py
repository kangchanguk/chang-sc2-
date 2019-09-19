from sc2.ids.unit_typeid import UnitTypeId
import numpy as np


#Observation: [type:9, x, y, health, mana, cargo, attack_cool]
class Environment:
    MAXUNIT = 100
    PERUNIT = 15

    def __init__(self, bot):
        self.bot = bot
        self.tracker = bot.tracker
        self.unitdata_size = self.MAXUNIT * self.PERUNIT
        self.state_size = self.unitdata_size * 2 + 10
        self.state = np.zeros(self.state_size)
        self.reward = 0
        self.prev_reward = 0
        self.done = False

    def set_army(self, army):
        self.army = army

    def gettype(self, typeid):
        if typeid == UnitTypeId.MARINE:
            return 0
        elif typeid == UnitTypeId.MARAUDER:
            return 1
        elif typeid == UnitTypeId.MEDIVAC:
            return 2
        elif typeid == UnitTypeId.REAPER:
            return 3
        elif typeid == UnitTypeId.SIEGETANK:
            return 4
        elif typeid == UnitTypeId.SIEGETANKSIEGED:
            return 5
        elif typeid == UnitTypeId.AUTOTURRET:
            return 6
        elif typeid == UnitTypeId.BUNKER:
            return 7
        elif typeid == UnitTypeId.COMMANDCENTER:
            return 8
        else:
            return 9

    def getunitobs(self, unit, i):
        unittype = self.gettype(unit.type_id)
        self.state[i + unittype] = 1
        self.state[i+9] = (unit.position.x - 12) / 64.0
        self.state[i+10] = (unit.position.y - 12) / 64.0
        self.state[i+11] = unit.health_percentage
        if unittype == 2 or unittype == 3:
            self.state[i+12] = unit.energy_percentage
        if unittype == 2 or unittype == 7:
            if unit.cargo_max != 0:
                self.state[i+13] = unit.cargo_used / unit.cargo_max
        self.state[i+14] = unit.weapon_cooldown / 100
    
    def step(self):
        self.done = self.tracker.finished != -1
        self.state = np.zeros(self.state_size)
        i = 0
        for unit in self.bot.units:
            self.getunitobs(unit, i)
            i += self.PERUNIT
            if i == self.MAXUNIT * self.PERUNIT:
                print("Too many units")
                break
        i = self.unitdata_size
        for unit in self.bot.known_enemy_units:
            self.getunitobs(unit, i)
            i += self.PERUNIT
            if i == self.MAXUNIT * self.PERUNIT * 2:
                print("Too many units")
                break
        i = self.unitdata_size * 2
        self.state[i] = (self.tracker.my_gold - self.tracker.enemy_gold) / 7
        self.state[i + 1] = (self.tracker.total_my_gold - self.tracker.total_enemy_gold) / 100
        self.state[i + 2 : i + 7] = (self.tracker.unknown_units[0:5] + 0.01) / (self.tracker.total_units[0:5] + 0.01)
        self.state[i + 8] = (self.army.center[0] - 12) / 64
        self.state[i + 9] = (self.army.center[1] - 12) / 64
        self.reward = (self.tracker.reward - self.prev_reward - self.tracker.enemy_gold / 7) / 30
        if self.done:
            if self.tracker.finished == 1:
                self.reward += 10
            elif self.tracker.finished == 2:
                self.reward -= 10
        
        self.prev_reward = self.tracker.reward

