from . import strategy
from ..armys import initarmy, aipusharmy, homearmy
from ..rl.agents import armyagent
from sc2.ids.unit_typeid import UnitTypeId
from ..units import unitwrapper
import tensorflow as tf
import os

class AiStrategy(strategy.Strategy):
    def __init__(self, bot):
        super().__init__(bot)
        self.aipusharmy = None
        self.agent = self.bot.agents["PushArmyAgent"]
        
    def on_start(self):
        self.aipusharmy = aipusharmy.AiPushArmy(self.bot, self.bot.map.points[0], self.bot.map.points[4], self.agent)
        self.agent.set_army(self.aipusharmy)
        self.armys.append(self.aipusharmy)

    def addUnit(self, unit):
        if isinstance(unit, unitwrapper.UnitWrapper):
            typ = unit.unit.type_id
        else:
            typ = unit.type_id
            
        self.aipusharmy.addUnit(unit)

    async def step(self, iteration):
        return await self.update()
