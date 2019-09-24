"changbot"

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
from IPython import embed

ARMY_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER)

SOL_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER,UnitTypeId.AUTOTURRET, UnitTypeId.COMMANDCENTER)

UNIT_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.MEDIVAC, UnitTypeId.REAPER)

FIRST_TYPES=(UnitTypeId.MARINE,UnitTypeId.MEDIVAC)
CARE_TYPES=(UnitTypeId.MARINE,UnitTypeId.AUTOTURRET)
PETRO_TYPES=(UnitTypeId.SIEGETANK,UnitTypeId.MARINE,UnitTypeId.MARAUDER)
class TerreinManager(object):  
    def __init__(self, bot_ai):
        self.bot = bot_ai
        # 자원이 생산되는 주요 전략적 요충지 좌표
        #  A     B
        #     C
        #  D     E
        self.strategic_points = [
            #        x   y   z
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]
        self.region_radius = 10
        self.current_point_idx = 2

    def reset(self):
        self.start_location = self.bot.start_location
        self.enemy_start_location = self.bot.enemy_start_locations[0]

    def step(self):
        if self.start_location is None:
            self.reset()

    def occupied_points(self):
        """
        지점를 점령하고 있는지 여부를 검사
        """
        units = self.bot.units.of_type(ARMY_TYPES).owned
        enemy = self.bot.known_enemy_units

        occupied = list()
        for point in self.strategic_points:
            n_units = units.closer_than(self.region_radius, point).amount
            n_enemy = enemy.closer_than(self.region_radius, point).amount
            # 해당 위치 근처에 내 유닛이 더 많으면 그 지점을 점령하고 있다고 가정함
            #   (내 유닛 개수 - 적 유닛 개수) > 0 이면 점령 중
            occupied.append(n_units - n_enemy)

        return occupied

    def _map_abstraction(self):
        # 내 시작위치를 기준으로 가까운 지역부터 먼 지역까지 정렬함
        if self.start_location.distance2_to(self.strategic_points[0]) < 3:
            points = self.strategic_points
            occupancy = self.occupied_points()
        else:
            points = list(reversed(self.strategic_points))
            occupancy = list(reversed(self.occupied_points()))
        return points, occupancy

    def frontline(self):
        """
        주력 병력을 투입할 전선을 결정
        """
        points, occupancy = self._map_abstraction()

        if self.bot.strategic_manager.strategy == Strategy.ATTACK:
            # 공격 전략일 때는 전선을 전진
            if occupancy[self.current_point_idx] > 0:
                self.current_point_idx += 1
                self.current_point_idx = min(4, self.current_point_idx)

        elif self.bot.strategic_manager.strategy == Strategy.HOLD:
            # 방어 전략일 때는 전선을 후퇴
            if occupancy[self.current_point_idx] < 0:
                self.current_point_idx -= 1
                self.current_point_idx = max(1, self.current_point_idx)

        return points[self.current_point_idx]

    def debug(self):
        """
        지형정보를 게임에서 시각화
        """
        # 각 지역마다, 내가 점령하고 있는지 아닌지 구의 색상으로 시각화
        for occ, point in zip(self.occupied_points(), self.strategic_points):
            color = Point3((255, 0, 0)) if occ > 0 else Point3((0, 0, 255))
            self.bot._client.debug_sphere_out(point, self.region_radius, color)


class Tactics(Enum):
    NORMAL = 0
    PROTECT =1
    
   
class CombatGroupManager(object):
    def __init__(self, bot_ai, tactics):
        self.bot = bot_ai
        self.strategy = None
        self.target = None
        self.unit_tags = None
        self.count = 0
        self.tactics = tactics
        self.state = ''
        self.perimeter_radious = 13
        self.region_radius = 10
        self.searchpoint = None
        self.state1=0
        self.state2=0
        self.rep=0
        self.strategic_points = [
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]
        self.marine=[]
        

    def reset(self):
        self.target = self.bot.terrein_manager.strategic_points[2]
        self.unit_tags = (self.bot.units & list()).tags

    def units(self):
        return self.bot.units.filter(lambda unit: unit.tag in self.unit_tags)

    async def step(self):
        actions = list()
        n_unit= self.bot.units.of_type(SOL_TYPES).closer_than(11, self.strategic_points[2]).amount
        n_enemy = self.bot.known_enemy_units.closer_than(7,self.strategic_points[2]).amount
        n_enemy1 = self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).amount
        
        units = self.units()

        if units.amount == 0 or self.target is None:
            return actions

        
        enemy = self.bot.known_enemy_units.closer_than(
            self.perimeter_radious, units.center)
        
        
    
        
        for unit in units:

            if self.tactics == Tactics.PROTECT:
                actions += await self.protect_step(unit, units, enemy)
            elif self.tactics == Tactics.NORMAL and self.count == 0:
                actions += await self.first_step(unit, units, enemy)
           
             
           
          

            if self.bot.debug:
                # 모든 유닛의 공격목표롤 시각화
                if len(unit.orders) > 0:
                    # if unit.type_id == UnitTypeId.MARINE:
                    #     embed(); exit()
                    skill = unit.orders[0].ability.id.name
                    target = unit.orders[0].target

                    if type(target) is Point3:
                        self.bot._client.debug_line_out(unit.position3d, target)
                        self.bot._client.debug_text_world(skill, target, size=16)

                    elif type(target) is int:
                        all_units = self.bot.units | self.bot.known_enemy_units
                        target_unit = all_units.find_by_tag(target)
                        if target_unit is not None:
                            target = target_unit.position3d
                            self.bot._client.debug_line_out(unit.position3d, target)
                            self.bot._client.debug_text_world(skill, target, size=16)

        if self.bot.debug:
            # 전투그룹의 중심점과 목표지점 시각화
            p1 = units.center
            p2 = self.target.to3
            self.bot._client.debug_sphere_out(
                Point3((p1.x, p1.y, 12)), 5, Point3((0, 255, 0)))
            self.bot._client.debug_line_out(
                Point3((p1.x, p1.y, 12)), p2, color=Point3((0, 255, 0)))
            self.bot._client.debug_sphere_out(
                self.target.to3, 5, Point3((0, 255, 0)))

        return actions
    
    async def protect_step(self, unit, friends,foes):
        actions = list()
        base = self.bot.start_location
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
        else:
            protectplace = Point3((62,35,11.99))
        if unit.type_id == UnitTypeId.MARINE:
            
            if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACK) :
                # 스팀팩 사용
                order = unit(AbilityId.EFFECT_STIM)
                actions.append(order)
            else:    
                
                target1 = protectplace
                actions.append(unit.attack(target1.to2))

        elif unit.type_id == UnitTypeId.REAPER:
            enemy=self.bot.known_enemy_units.closer_than(6,unit.position)
            if enemy.amount==0:
                actions.append(unit.move(protectplace))
            else:
                pos = await self.bot.find_placement(
                    UnitTypeId.AUTOTURRET, unit.position)
                order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                actions.append(order)
        
        elif unit.type_id == UnitTypeId.MARAUDER:
            if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACKMARAUDER):
            # 스팀팩 사용
                order = unit(AbilityId.EFFECT_STIM_MARAUDER)
                actions.append(order)
            else:    
                target1 = protectplace
                actions.append(unit.attack(target1.to2))

        elif unit.type_id == UnitTypeId.SIEGETANK:
            order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
            actions.append(order)

        return actions
    
    async def first_step(self, unit, friends, foes):
        
        actions = list()
        base = self.bot.start_location
        center = self.strategic_points[2]
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        bush_backward = Point3(
                ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
        )
        if base.x<50:
            firstplace=Point3((13.39,29.10,10.00))
            lastplace=Point3((18.46,21.42,10.00)) 
            ready_point = Point3((61.4, 43.3, 10))
            enemycenter= self.strategic_points[4]
            arriveplace =Point3((58.08,36.39,11.99))
            frontplace = self.strategic_points[1]
            enemyplace = self.strategic_points[4]
            
        else:
            firstplace=Point3((74.61,58.88,10.00))
            lastplace=Point3((69.54,66.58,10.00))
            ready_point = Point3((26.6, 44.7, 10))
            enemycenter = Point3((28.5,57.68,11.99))
            frontplace = self.strategic_points[3]
            enemyplace = self.strategic_points[0]
            arriveplace = Point3((29.92,52.17,11.99))
        
        if unit.type_id == UnitTypeId.MARINE:
            self.marine.append(unit.tag)
            can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
            distance1=((firstplace.x-unit.position3d.x)**2 + (firstplace.y-unit.position3d.y)**2)**0.5 
            distance2 =((lastplace.x-unit.position3d.x)**2 + (lastplace.y-unit.position3d.y)**2)**0.5 
            distance3 =((ready_point.x-unit.position3d.x)**2 + (ready_point.y-unit.position3d.y)**2)**0.5 
            distance4 =((enemycenter.x-unit.position3d.x)**2 + (enemycenter.y-unit.position3d.y)**2)**0.5 
            if unit.tag == self.marine[0]:
                if unit.position3d.z>11 and distance4>20:
                    actions.append(unit.move(upper_bush))
                else:
                    
                    if distance1>0 and self.state1==0:
                        self.state2=1
                        if unit.health_percentage > 0.5 and not unit.has_buff(BuffId.STIMPACK):
                            order = unit(AbilityId.EFFECT_STIM)
                            actions.append(order)
                        elif distance1<=0.5:
                            self.state1=1
                        else:
                            actions.append(unit.move(firstplace))
                   
                    elif self.state1==1 and distance2>0.5:
                        if unit.health_percentage > 0.5 and not unit.has_buff(BuffId.STIMPACK):
                            order = unit(AbilityId.EFFECT_STIM)
                            actions.append(order)
                        else:
                            actions.append(unit.move(lastplace))
                    
            else:  
                if unit.position3d.z>11 and distance4<20:
                    if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACK):
                        order = unit(AbilityId.EFFECT_STIM)
                        actions.append(order)
                    else:
                        if (foes.of_type(UnitTypeId.MEDIVAC) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.MEDIVAC}).closest_to(unit.position))
                            actions.append(order)
                        else:
                            target1=enemycenter
                            actions.append(unit.attack(target1.to2)) 
                            self.state2=2      
                elif distance3>1  :
                    actions.append(unit.move(ready_point))
                    
                

            
        elif unit.type_id ==  UnitTypeId.MEDIVAC:
            if self.state2==0:
                target_pssn = self.bot.units.of_type(UnitTypeId.MARINE).filter(lambda u: u.position3d.z>=11).closer_than(3,upper_bush) 
                if target_pssn.exists:
                    actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(upper_bush)))
                elif unit.cargo_used>0:
                    actions.append(unit(AbilityId.UNLOADALLAT,bush_backward))
                    if self.bot.units.of_type(UnitTypeId.MARINE).filter(lambda u: u.position3d.z<10).closer_than(1,bush_backward)==1:
                        self.state2=1
            elif self.state2==1:
                target_pssn= self.bot.units.of_type(UNIT_TYPES).filter(lambda u: u.position3d.z<10).closer_than(3,ready_point)
                if unit.cargo_used>=5:
                    if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                        order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                        actions.append(order)
                    else:
                        actions.append(unit(AbilityId.UNLOADALLAT,arriveplace))
                        
                elif target_pssn.exists:
                    if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                        order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                        actions.append(order)
                    else:
                        actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(ready_point)))
            elif self.state2==2:
                target_pssn1= self.bot.units.of_type(UNIT_TYPES).filter(lambda u: u.position3d.z<11).closer_than(8,ready_point)
                if unit.cargo_used>0:
                    actions.append(unit(AbilityId.UNLOADALLAT,arriveplace))
                elif target_pssn1.exists:
                    actions.append(unit(AbilityId.LOAD,target_pssn1.closest_to(ready_point)))

        elif unit.type_id ==  UnitTypeId.MARAUDER:
            can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
            distance3 =((ready_point.x-unit.position3d.x)**2 + (ready_point.y-unit.position3d.y)**2)**0.5 
            distance4 =((enemycenter.x-unit.position3d.x)**2 + (enemycenter.y-unit.position3d.y)**2)**0.5 
            if self.bot.vespene<=1:
                if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACK):
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                else:
                    
                    target1=frontplace
                    actions.append(unit.attack(frontplace)) 

            elif unit.position3d.z>11 and distance4<20:
                if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACK):
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                else:
                   
                    if (foes.of_type(UnitTypeId.MEDIVAC) & can_atk) :
                        order = unit.attack(foes.of_type({UnitTypeId.MEDIVAC}).closest_to(unit.position))
                        actions.append(order)
                    else:
                        target1=enemycenter
                        actions.append(unit.attack(target1.to2)) 
                   
            elif distance3>1 :
                actions.append(unit.move(ready_point))
                    
             
        elif unit.type_id == UnitTypeId.REAPER:
            distance3 =((ready_point.x-unit.position3d.x)**2 + (ready_point.y-unit.position3d.y)**2)**0.5 
            if self.rep==1 and unit.position3d.z<11:
                actions.append(unit.move(enemycenter))        
            if unit.position3d.z > 11 and self.rep==1:
                enemy=self.bot.known_enemy_units.of_type(SOL_TYPES).closer_than(6,unit.position)
                if enemy.amount==0:
                    actions.append(unit.move(enemycenter))
                else:
                    pos = await self.bot.find_placement(
                        UnitTypeId.AUTOTURRET, unit.position)
                    order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                    actions.append(order)
            
            elif distance3 > 1:
                order = unit.move(ready_point)
                actions.append(order)
                if distance3 <2:
                    self.rep=1
            
        elif unit.type_id ==  UnitTypeId.SIEGETANK:
            distance3 =((ready_point.x-unit.position3d.x)**2 + (ready_point.y-unit.position3d.y)**2)**0.5 
            distance4 =((enemycenter.x-unit.position3d.x)**2 + (enemycenter.y-unit.position3d.y)**2)**0.5
            if unit.position3d.z>11 and distance4<20:
                order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                actions.append(order)
            elif distance3>1 :
                actions.append(unit.move(ready_point))
                    
           




       
        return actions

    
    
   

    def debug(self):
        text = [

            f'Tactics: {self.tactics}, state: {self.bot.known_enemy_units.of_type(SOL_TYPES).closer_than(13,self.bot.enemy_start_locations[0]).amount}',
        ]
        self.bot._client.debug_text_screen(
            '\n\n'.join(text), pos=(0.02, 0.14), size=10)


class Strategy(Enum):
    """
    Bot이 선택할 수 있는 전략
    Strategy Manager는 언제나 이 중에 한가지 상태를 유지하고 있어야 함
    """
    NONE = 0
    ATTACK = 1
    HOLD = 2


class StrategicManager(object):
    """
    Bot의 전략을 결정하는 매니저
    """
    def __init__(self, bot_ai):
        self.bot = bot_ai
        self.strategy = Strategy.NONE

    def reset(self):
        self.strategy = Strategy.HOLD

    def step(self):
        if self.bot.supply_cap > 25:
            if self.bot.supply_used / (self.bot.supply_cap + 0.01) > 0.5:
                # 최대 보급량이 25이상이고,
                # 최대 보급의 50% 이상을 사용했다면 병력이 준비된 것으로 판단
                # 공격전략 선택
                self.strategy = Strategy.ATTACK

            else:
            # else self.bot.supply_used / self.bot.supply_cap < 0.3:
            #     # 최대 보급의 0.3 밑이면 전선유지 전략 선택
                self.strategy = Strategy.HOLD
        else:
            self.strategy = Strategy.HOLD

    def debug(self):
        text = [
            f'Strategy: {self.strategy}',
            f'Supply used: {self.bot.supply_used / (self.bot.supply_cap + 0.01):1.3f}'
        ]
        self.bot._client.debug_text_screen(
            '\n\n'.join(text), pos=(0.02, 0.02), size=10)


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

       

        if manager.tactics is Tactics.NORMAL:
          
            units = self.bot.units.of_type(ARMY_TYPES).owned
            unit_tags = units.tags
            unit_tags = unit_tags - self.bot.first_manager.unit_tags
            manager.unit_tags = unit_tags

        elif manager.tactics is Tactics.PROTECT:
          
            units = self.bot.units.of_type(ARMY_TYPES).owned
            unit_tags = units.tags
            unit_tags = unit_tags - self.bot.combat_manager.unit_tags
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
        self.strategic_manager = StrategicManager(self)
        self.first_manager = CombatGroupManager(self, Tactics.PROTECT )
           

    def on_start(self):
        self.strategic_manager.reset()
        self.assign_manager.reset()
        self.terrein_manager.reset()
        self.combat_manager.reset()
        self.first_manager.reset()
      
        

    async def on_step(self, iteration: int):
        homeenemy=self.known_enemy_units.of_type(UNIT_TYPES).closer_than(13,self.start_location).amount
        
        if homeenemy>0:
            self.strategic_manager.step()
            self.terrein_manager.step()
            self.assign_manager.assign(self.first_manager)
        
        else:
            # 전략 변경
            self.strategic_manager.step()

            # 지형정보 분석
            self.terrein_manager.step()

            # 부대 구성 변경
            # self.assign_manager.step()
            
            self.assign_manager.assign(self.combat_manager)
           

            # 새로운 공격지점 결정
            self.combat_manager.target = self.terrein_manager.frontline()
            

        actions = list()
        
        actions += await self.combat_manager.step()
        actions += await self.first_manager.step()
            
      
        await self.do_actions(actions)

        if self.debug:
            # 현재 전략 게임화면에 시각화
            self.strategic_manager.debug()
            # 지형정보를 게임 화면에 시각화
            self.terrein_manager.debug()
            self.combat_manager.debug()


            await self._client.send_debug()