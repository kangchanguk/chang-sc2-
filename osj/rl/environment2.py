from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
import numpy as np

class Environment:
    def __init__(self, bot):
        self.bot = bot
        self.map_obs = np.zeros([64, 64, 21])
        self.map_obs_size = 64 * 64 * 21
        self.state_size = self.map_obs_size + 17
        self.state = np.zeros(self.state_size)
        self.reward = 0
        self.prev_reward = 0
        self.done = False

    def set_army(self, army):
        self.army = army
        self.state_size = self.map_obs_size + 17
        self.state = np.zeros(self.state_size)
        self.reward = 0
        self.prev_reward = 0
        self.done = False

        if self.bot.map.invert:
            self.map_obs[:,:,20] = self.bot.map.height_map[::-1, ::-1]
        else:
            self.map_obs[:,:,20] = self.bot.map.height_map

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

    def addunit(self, unit, isenemy):
        isenemy = 10 if isenemy else 0
        typ = self.gettype(unit.type_id)
        x = int(unit.position.x - 12)
        y = int(unit.position.y - 12)
        if self.bot.map.invert:
            x = 63 - x
            y = 63 - y
        if typ == 0:
            self.map_obs[x, y, 0+isenemy] += 0.36
        elif typ == 1:
            self.map_obs[x, y, 1+isenemy] += 0.56
        elif typ == 2:
            self.map_obs[x, y, 2+isenemy] += 0.3
        elif typ == 3:
            self.map_obs[x, y, 3+isenemy] += 0.36
        else:
            self.map_obs[x, y, typ+isenemy] += unit.health_percentage

            

    def step(self):
        self.done = self.bot.tracker.finished != -1
        self.map_obs[:, :, 0:20] = 0
        '''
        for x in range(0, 64):
            for y in range(0, 64):
                if self.bot.map.invert:
                    self.map_obs[x, y, 20] = 1 if self.bot.is_visible(Point2((75 - x, 75 - y))) else 0
                else:
                    self.map_obs[x, y, 20] = 1 if self.bot.is_visible(Point2((x+12, y+12))) else 0
        '''
            
        for enemy in self.bot.known_enemy_units:
            self.addunit(enemy, True)

        for mine in self.bot.units:
            self.addunit(mine, False)

        self.state[:self.map_obs_size] = np.ndarray.flatten(self.map_obs)

        i = self.map_obs_size
        self.state[i] = (self.bot.tracker.my_gold - self.bot.tracker.enemy_gold) / 7
        self.state[i + 1] = (self.bot.tracker.total_my_gold - self.bot.tracker.total_enemy_gold) / 500
        self.state[i + 2 : i + 7] = (self.bot.tracker.total_units[0:5]) / np.array([30, 20, 10, 6, 6])
        self.state[i + 7 : i + 12] = (self.bot.tracker.unknown_units[0:5]) / np.array([30, 20, 10, 6, 6])
        if self.bot.map.invert:
            self.state[i + 12] = (73 - self.army.center.x) / 64
            self.state[i + 13] = (73 - self.army.center.y) / 64
        else:
            self.state[i + 12] = (self.army.center.x - 12) / 64
            self.state[i + 13] = (self.army.center.y - 12) / 64
        self.state[i+14] = self.army.state
        self.state[i+15] = self.bot.rtime / 600
        if self.bot.supply_cap == 0:
            self.state[i+16] = 0
        else:
            self.state[i+16] = self.bot.supply_used / self.bot.supply_cap
            
        self.reward = (self.bot.tracker.reward - self.prev_reward - self.bot.tracker.enemy_gold / 7) / 10
        if self.bot.tracker.finished == 1:
            self.reward += 5
        elif self.bot.tracker.finished == 2:
            self.reward -= 5
        
        self.prev_reward = self.bot.tracker.reward
        