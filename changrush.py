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


# 주력부대에 속한 유닛 타입
ARMY_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.BUNKER,UnitTypeId.REAPER)

UNIT_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER)


class TerreinManager(object):
    """
    간단한 지형정보를 다루는 매니저
    """
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
        # 나와 적의 시작위치 설정
        self.start_location = self.bot.start_location
        self.enemy_start_location = self.bot.enemy_start_locations[0]

    def step(self):
        # 나와 적의 시작위치 설정
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

        # 어떤 조건도 만족시키지 않으면, 중앙에 유닛 배치
        return points[self.current_point_idx]

    def weak_point(self):
        """
        적 점령지역 중에 방어가 취약한 부분
        """
        points, _ = self._map_abstraction()

        if self.current_point_idx == 4:
            return points[4]
        else:
            return points[3]

    def drop_point(self):
        points, _ = self._map_abstraction()
        return points[1]

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
    FIRST = 1
   


class CombatGroupManager(object):
    """
    개별 유닛에게 직접 명령을 내리는 매니저
    """
    def __init__(self, bot_ai, tactics):
        self.bot = bot_ai
        self.strategy = None
        self.target = None
        self.unit_tags = None
        # 그룹의 경계 범위
        self.count = 0
        self.tactics = tactics
        self.state = ''
        self.count=0
        self.perimeter_radious = 13
        self.region_radius = 10
        self.strategic_points = [
            #        x   y   z
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]

        self.arriveplace = [
            Point3((67.78,37.33,11.99)),
            Point3((64.38,35.83,11.99)),
            Point3((56.08,37.39,11.99))

        ]

        self.arriveplace2 = [
            Point3((20.22,50.67,11.99)),
            Point3((23.62,52.17,11.99)),
            Point3((31,48.39,11.99)),
        ]


    def reset(self):
        self.target = self.bot.terrein_manager.strategic_points[2]
        self.unit_tags = (self.bot.units & list()).tags

    def units(self):
        return self.bot.units.filter(lambda unit: unit.tag in self.unit_tags)

    async def step(self):
        actions = list()

        # 이 전투그룹에 속한 아군 유닛들
        units = self.units()

        if units.amount == 0 or self.target is None:
            return actions

        # 이 전투그룹 근처의 적군 유닛들
        enemy = self.bot.known_enemy_units.closer_than(
            self.perimeter_radious, units.center)

        for unit in units:

            if self.tactics == Tactics.NORMAL:
                actions += await self.normal_step(unit, units, enemy)
            elif self.tactics == Tactics.FIRST:
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
    
    async def first_step(self, unit, friends, foes):
        actions = list()
        base = self.bot.start_location
        center = self.strategic_points[2]
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
        else:
            protectplace = Point3((62,35,11.99))

        if unit.type_id == UnitTypeId.MARINE or unit.type_id == UnitTypeId.MEDIVAC:
            if self.bot.time < 7:
                actions.append(unit.move(upper_bush))
            else:
                actions.append(unit.move(protectplace))

        return actions

    async def normal_step(self, unit, friends, foes):
        actions = list()
        base = self.bot.start_location
        center = self.strategic_points[2]
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
            arriveplace = Point3((63.92,34.5,11.99))
            arriveplace2 =  Point3((56.08,36.39,11.99))
            enemyplace = self.strategic_points[4]
            gatherplace = self.strategic_points[1]
            restplace = Point3((23.31,62.53,11.99 ))
            transplace = Point3((50.30,66.31,9))

        else:
            protectplace = Point3((62,35,11.99))
            arriveplace = Point3((24.08, 53.0,11.99))
            arriveplace2 = Point3((31.62,52.17,11.99))
            enemyplace = self.strategic_points[0]
            gatherplace = self.strategic_points[3]
            restplace = Point3((64.65,25.47,11.99))
            transplace = Point3((37,21.6,9))
            
        our_bush = Point2(
                (
                    (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5
                )
            )
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        bush_backward = Point3(
                ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
            )
        bush_center = Point2(
            (
                (bush_backward.x + our_bush.x) / 2, (bush_backward.y + our_bush.y) / 2
            )
        )
        last_point =  Point2(
                (
                    (our_bush.x + center.x * 1) / 2, (our_bush.y + center.y * 1) / 2
                )
            )
        bunk = self.bot.units.of_type(UnitTypeId.BUNKER).owned
        MEDI = self.bot.units.of_type(UnitTypeId.MEDIVAC).owned
        tank = self.bot.units.of_type(UnitTypeId.SIEGETANK).owned
        marine = self.bot.units.of_type(UnitTypeId.MARINE).owned
        reap = self.bot.units.of_type(UnitTypeId.REAPER).owned
        can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
        if reap.amount > 0:
            self.count = 1
            

        if unit.type_id == UnitTypeId.MARINE:
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if self.count == 0:
                actions.append(unit.move(protectplace))
            else:
                if distance > 10 and distance3 >20:
                    actions.append(unit.move(transplace))
                elif unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK) and distance3<5:
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                
                
                               


        elif unit.type_id == UnitTypeId.REAPER:
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            if distance>10 and distance3>20:
                order=unit.move(transplace)
                actions.append(order)
            else:
                threaten = self.bot.known_enemy_units.closer_than(
                        self.perimeter_radious, unit.position)

                if unit.energy >= 50:
                    if unit.health_percentage >= 0.7  and threaten.amount > 0:
                        if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                            closest_threat = threaten.closest_to(unit.position)
                            
                            pos = unit.position.towards(closest_threat.position, 5)
                            pos = await self.bot.find_placement(
                                UnitTypeId.AUTOTURRET,pos, 10)
                            
                            order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                            actions.append(order)
                

          

        elif unit.type_id == UnitTypeId.MARAUDER:
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            enemy = self.bot.known_enemy_units
            n_enemy = enemy.closer_than(5, unit.position).amount
            if distance2 > 5:
                actions.append(unit.move(protectplace))
            
           
            elif n_enemy >= 1:
                if unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK):
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)

                '''
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if self.count == 0:
                elif distance2 > 5 and distance3 >20:
                    actions.append(unit.move(protectplace))
            else:
                if distance > 10 and distance3 > 20:
                    actions.append(unit.move(transplace))
                elif unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK) and distance3<5:
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                else:
                    if foes.amount>0:
                        if (foes.of_type(UnitTypeId.REAPER) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.REAPER}).closest_to(unit.position))
                        elif(foes.of_type(UnitTypeId.AUTOTURRET) & can_atk):
                            order = unit.attack(foes.of_type({UnitTypeId.AUTOTURRET}).closest_to(unit.position))
                        else:
                            order = unit.attack(foes.closest_to(unit.position))
                '''

        elif unit.type_id == UnitTypeId.SIEGETANK:
            distance2=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if distance >= 10 and distance2 >= 20:
                actions.append(unit.move(transplace))
            
          

            else:
                if distance3<10:
                    enemy = self.bot.known_enemy_units
                    n_enemy = enemy.closer_than(10, unit.position).amount
                    if n_enemy <= 1:
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                        actions.append(order)
               
       

        elif unit.type_id == UnitTypeId.MEDIVAC:
          
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance2=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            
            
           
            target_pssn = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE) 
               
            target_pssn3 = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.SIEGETANK)   
            target_pssn2 = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.REAPER) 
                    
        
            if len(unit.passengers)==0 and distance > 2 and distance2 >= 20:
                actions.append(unit.move(transplace))
        
            elif target_pssn3.exists and unit.cargo_used==0 and distance2 >= 20 and distance <=2:
                
                actions.append(unit(AbilityId.LOAD,target_pssn3.closest_to(unit.position) ))
            elif target_pssn2.exists and unit.cargo_used==4 and distance2 >= 20 and distance <=2:
                
                actions.append(unit(AbilityId.LOAD,target_pssn2.closest_to(unit.position) ))
            elif target_pssn.exists and unit.cargo_used<8 and distance2 >= 20 and distance <=2 and unit.cargo_used>=5:
                actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(unit.position) ))

            elif unit.cargo_used>=8:
                if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                    order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                    actions.append(order)
                else:
                    
                    if distance2 >10:
                        actions.append(unit.move(arriveplace))
                    else:
                        enemy = self.bot.known_enemy_units
                        n_enemy1 = enemy.closer_than(10, unit.position).amount

                        if n_enemy1 >7:
                            print(n_enemy1)
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                        
                        elif n_enemy1 <=7:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))

                        elif friends.of_type({UnitTypeId.REAPER}).closest_to(unit.position).health_percentage < 0.7:
                            order = unit(AbilityId.MEDIVACHEAL_HEAL,friends.of_type({UnitTypeId.REAPER}).closest_to(unit.position))
                            actions.append(order)
                            
                    '''
                    enemy = self.bot.known_enemy_units
                    n_enemy1 = enemy.closer_than(3, self.arriveplace[0]).amount
                    n_enemy2 = enemy.closer_than(3, self.arriveplace[1]).amount
                    n_enemy3 = enemy.closer_than(3, self.arriveplace[2]).amount
                    if n_enemy1 < 5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[0])))
                    elif n_enemy2<5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[1])))
                    elif n_enemy3<5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[2])))
                    else:
                        actions.append(actions.append(unit.move(transplace)))
                    '''
                    '''
                    if len(unit.passengers)<=5:
                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                    else:
                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))
                    '''
                
            '''   
            else:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARAUDER) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.SIEGETANK) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.REAPER) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE)   
                    

                units = self.bot.units.of_type(ARMY_TYPES).owned
                n_units = units.closer_than(self.region_radius, arriveplace).amount
                full = self.bot.units.filter(lambda u : u.cargo_used >=7).of_type(UnitTypeId.MEDIVAC)
                if len(unit.passengers)==0 and distance > 2 and distance2 >= 20:
                    actions.append(unit.move(transplace))
            
                elif target_pssn.exists and len(unit.passengers) < 6 and distance2 >= 20:
                    actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(unit.position) ))

                elif unit.cargo_used == 8:  
                    if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                        order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                        actions.append(order)
                    else:
                        if len(unit.passengers)<=5:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                        else:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))
            '''
                
                
            

        

        return actions

    

    def debug(self):
        text = [

            f'Tactics: {self.tactics}, state: {self.state}',
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
        self.strategic_manager = StrategicManager(self)
        self.first_manager = CombatGroupManager(self, Tactics.FIRST)
           

    def on_start(self):
        self.strategic_manager.reset()
        self.assign_manager.reset()
        self.terrein_manager.reset()
        self.combat_manager.reset()
        self.first_manager.reset()
        

    async def on_step(self, iteration: int):
        """
        매니저 단위로 작업을 분리하여 보다 간단하게 on_step을 구현
        """

        if self.time <= 9:
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
        if self.time <= 9:
            actions += await self.first_manager.step()
        else:
            actions += await self.combat_manager.step()
      
        await self.do_actions(actions)

        if self.debug:
            # 현재 전략 게임화면에 시각화
            self.strategic_manager.debug()
            # 지형정보를 게임 화면에 시각화
            self.terrein_manager.debug()


            await self._client.send_debug()
