from . import army
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2, Point3

class AiPushArmy(army.Army):
    def __init__(self, bot, start, end, agent):
        super().__init__(bot, start, end)
        self.name = "AiPush"
        self.interval = 10
        self.prevtime = bot.rtime
        self.agent = agent
    
    async def step(self):
        if self.bot.rtime - self.prevtime >= 1:
            self.agent.step()
            self.prevtime = self.bot.rtime
            action = self.agent.action
            self.state = action % 2
            action = action // 2
            if self.bot.map.invert:
                self.center = Point2((88 - (action / 8 * (64 / 8) + 12 + 64 / 16), 88 - (action % 8 * (64 / 8) + 12 + 64 / 16)))
            else:
                self.center = Point2((action / 8 * (64 / 8) + 12 + 64 / 16, action % 8 * (64 / 8) + 12 + 64 / 16))
        self.bot._client.debug_text_world(f"{self.name}: {self.state}", Point3((self.center.x, self.center.y, 12)), size=16)
        
        actions = list()

        actions.extend(await self.updateUnits())
        return actions