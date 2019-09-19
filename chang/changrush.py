import random
from enum import Enum

import sc2
import math
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units
from mapinfo import TerreinManager
from combat import CombatGroupManager
from IPython import embed


# 주력부대에 속한 유닛 타입
ARMY_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.BUNKER,UnitTypeId.REAPER)

UNIT_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER)

class Tactics(Enum):
    NORMAL = 0
    FIRST = 1
   
class AssignManager(object):
    """
    유닛을 부대에 배치하는 매니저
    """
    def __init__(self, bot_ai, *args, **kwargs):
        self.bot = bot_ai

    def reset(self):
        pass

    def assign(self, manager):

        units = self.bot.units

        if manager.tactics is Tactics.FIRST:
            units = self.bot.units.owned
            unit_tags = units.tags
            manager.unit_tags = unit_tags

        elif manager.tactics is Tactics.NORMAL:
            #print('1')
            units = self.bot.units.of_type(ARMY_TYPES).owned
            unit_tags = units.tags
            unit_tags = unit_tags - self.bot.first_manager.unit_tags
            manager.unit_tags = unit_tags

        else:
            raise NotImplementedError

class ChangRush(sc2.BotAI):
    """
    병력이 준비되면 적 본직으로 조금씩 접근하는 가장 간단한 전략을 사용하는 봇
    """
    def __init__(self, debug=False,*args, **kwargs):
        super().__init__()
        self.debug = debug
        self.terrein_manager = TerreinManager(self)
        self.combat_manager = CombatGroupManager(self, Tactics.NORMAL)
        self.assign_manager = AssignManager(self)
       
        self.first_manager = CombatGroupManager(self, Tactics.FIRST)
           

    def on_start(self):
     
        self.assign_manager.reset()
        self.terrein_manager.reset()
        self.combat_manager.reset()
        self.first_manager.reset()
        

    async def on_step(self, iteration: int):
        """
        매니저 단위로 작업을 분리하여 보다 간단하게 on_step을 구현
        """
        if self.time <= 9:
            self.terrein_manager.step()
            self.assign_manager.assign(self.first_manager)

        else:
         
            self.terrein_manager.step()

            self.assign_manager.assign(self.combat_manager)
       
            self.combat_manager.target = self.terrein_manager.frontline()
            

        actions = list()
        if self.time <= 9:
            actions += await self.first_manager.step()
        else:
            actions += await self.combat_manager.step()
      
        await self.do_actions(actions)

        if self.debug:
            self.terrein_manager.debug()


            await self._client.send_debug()
