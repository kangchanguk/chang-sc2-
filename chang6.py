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
import time

ARMY_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER)

SOL_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER,
    UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.MEDIVAC, UnitTypeId.REAPER, UnitTypeId.BUNKER,UnitTypeId.AUTOTURRET)

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
    FIRST = 1
   
class CombatGroupManager(object):
    def __init__(self, bot_ai, tactics):
        self.bot = bot_ai
        self.strategy = None
        self.target = None
        self.unit_tags = None
        self.count = 0
        self.count1 = 0
        self.tactics = tactics
        self.state = ''
        self.shy=0
        self.state1=0
        self.switch=0
        self.perimeter_radious = 13
        self.region_radius = 10
        self.searchpoint = None
        self.state=0
        
        self.strategic_points = [
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]
        self.goal_point = [
            Point3((37.16,49.47,9)),
            Point3((40.04,47.29,9)),
            Point3((44,44,10)),
            Point3((47.96,40.71,9)),
            Point3((50.83,38.53,9.99)),
        ]
        self.reaper=[]
        self.marine=[]
        self.siege=[]
        self.pet=0

    def reset(self):
        self.target = self.bot.terrein_manager.strategic_points[2]
        self.unit_tags = (self.bot.units & list()).tags

    def units(self):
        return self.bot.units.filter(lambda unit: unit.tag in self.unit_tags)

    async def step(self):
        actions = list()
        n_unit= self.bot.units.of_type(SOL_TYPES).closer_than(11, self.strategic_points[2]).amount
        n_enemy = self.bot.known_enemy_units.closer_than(7,self.strategic_points[2]).amount
        
        # 이 전투그룹에 속한 아군 유닛들
        units = self.units()

        if units.amount == 0 or self.target is None:
            return actions

        # 이 전투그룹 근처의 적군 유닛들
        enemy = self.bot.known_enemy_units.closer_than(
            self.perimeter_radious, units.center)
        
        
    
        
        for unit in units:

            if self.tactics == Tactics.NORMAL and self.count == 0:
                actions += await self.normal_step(unit, units, enemy)
            elif self.tactics == Tactics.NORMAL and self.count ==1:
                actions += await self.attack_step(unit,units,enemy)
                
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
        self.target=self.strategic_points[2]
        base = self.bot.start_location
        center = self.strategic_points[2]
        bush_backward = Point3(
                ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
        )
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        homeenemy = self.bot.known_enemy_units.closer_than(10, base).amount
        medi=self.bot.units.of_type(UnitTypeId.MEDIVAC).owned
        if base.x<50:
            protectplace = Point3((7.04,53.42,11.99))
            protectplace1 = Point3((25.32,52.24,11.99))
            firstplace=Point3((13.39,29.10,10.00))
            lastplace=Point3((18.46,21.42,10.00)) 
            lastplace1=Point3((16.46,21.42,10.00))
            bunkerplace=Point3((47.5,47.5,9.999828))
            frontplace =self.strategic_points[1]
        else:
            firstplace=Point3((74.61,58.88,10.00))
            lastplace=Point3((69.54,66.58,10.00))
            lastplace1=Point3((71.54,66.58,10.00))
            protectplace = Point3((73,34.6,11.99))
            protectplace1= Point3((62,35,11.99))
            bunkerplace=Point3((40.5,40.5,10))
            frontplace = self.strategic_points[3]

        if unit.type_id == UnitTypeId.MARINE:
            n=0
            for i in range(len(self.marine)):
                if unit.tag==self.marine[i]:
                    n=1
            if n==0:
                self.marine.append(unit.tag)
            
            distance=((frontplace.x-unit.position3d.x)**2 + (frontplace.y-unit.position3d.y)**2)**0.5 
            distance1=((firstplace.x-unit.position3d.x)**2 + (firstplace.y-unit.position3d.y)**2)**0.5 
            distance2 =((lastplace.x-unit.position3d.x)**2 + (lastplace.y-unit.position3d.y)**2)**0.5 

            if self.bot.time < 9:
                actions.append(unit.move(upper_bush))
            
            else:
                if unit.tag == self.marine[0]:
                    if unit.position3d.z>11:
                        actions.append(unit.move(upper_bush))
                    else:
                        if distance1>0 and self.state1==0:
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
                        
                        
                elif unit.tag == self.marine[1]:
                    if unit.position3d.z>11:
                        actions.append(unit.move(upper_bush))
                    else:
                        
                        if self.marine[0] in self.bot.state.dead_units:
                            self.state1=3

                        if distance1>0 and self.state1==3:
                            if unit.health_percentage > 0.5 and not unit.has_buff(BuffId.STIMPACK):
                                order = unit(AbilityId.EFFECT_STIM)
                                actions.append(order)
                            elif distance1<=0.5:
                                self.state1=4
                            else:
                                actions.append(unit.move(firstplace))
                   
                        elif self.state1==4 and distance2>0.5:
                            if unit.health_percentage > 0.5 and not unit.has_buff(BuffId.STIMPACK):
                                order = unit(AbilityId.EFFECT_STIM)
                                actions.append(order)
                            else:
                                actions.append(unit.move(lastplace))
                                self.state1=5
                        elif self.state1==5:
                            distance=((lastplace.x-unit.position3d.x)**2 + (lastplace.y-unit.position3d.y)**2)**0.5 
                            distance1=((lastplace1.x-unit.position3d.x)**2 + (lastplace1.y-unit.position3d.y)**2)**0.5 
                            if distance1>0.5:
                                actions.append(unit.move(lastplace1))
                                time.sleep(2)
                            elif distance>0.5:
                                actions.append(unit.move(lastplace))
                                time.sleep(2)
                        else:
                            actions.append(unit(AbilityId.HOLDPOSITION,bush_backward))

                elif unit.tag == self.marine[2] or unit.tag == self.marine[3] or unit.tag == self.marine[4] or unit.tag == self.marine[5]:       
                    if homeenemy>0:
                        if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACK):
                            order = unit(AbilityId.EFFECT_STIM)
                            actions.append(order)
                        else:    
                            target1 = self.bot.known_enemy_units.closer_than(13,self.bot.start_location).closest_to(unit.position),position
                            actions.append(unit.attack(target1.to2))   
                    else:
                        actions.append(unit.move(protectplace1))
                else:
                    bunk = self.bot.units.of_type(UnitTypeId.BUNKER).owned
                    if self.bot.vespene<=1:
                        if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACKMARAUDER):
                        # 스팀팩 사용
                            order = unit(AbilityId.EFFECT_STIM_MARAUDER)
                            actions.append(order)
                        else:
                            target1=frontplace
                            actions.append(unit.attack(target1.to2))
                    elif homeenemy>0:
                        if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACKMARAUDER):
                        # 스팀팩 사용
                            order = unit(AbilityId.EFFECT_STIM_MARAUDER)
                            actions.append(order)
                        else:    
                            target1 = protectplace1
                            actions.append(unit.attack(target1.to2))

                    elif bunk.amount==2:
                        actions.append(unit.move(bunkerplace))
                    else:
                        actions.append(unit.move(self.target))
                            
                             

        elif unit.type_id ==  UnitTypeId.MEDIVAC:
            if homeenemy>0:
                actions.append(unit(AbilityId.MEDIVACHEAL_HEAL, base))
            
            else:      
                target_pssn1=self.bot.units.filter(lambda u: u.position3d.z>=11).closer_than(3,upper_bush)
                if unit.cargo_used>0:
                    actions.append(unit(AbilityId.UNLOADALLAT,bush_backward))
                elif target_pssn1.exists:
                    if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                        order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                        actions.append(order)
                    else:
                        actions.append(unit(AbilityId.LOAD,target_pssn1.closest_to(upper_bush)))
                else:
                    n_enemy = self.bot.known_enemy_units.of_type(SOL_TYPES).closer_than(8,unit.position)
                    if n_enemy.amount>0:
                        actions.append(unit.move(upper_bush))
                    else:
                        actions.append(unit.move(self.target))
                   
                
           

        elif unit.type_id == UnitTypeId.REAPER:
            if homeenemy>0:
                enemy=self.bot.known_enemy_units.closer_than(7,unit.position)
                if enemy.amount==0:
                    actions.append(unit.move(protectplace1))
                else:
                    pos = await self.bot.find_placement(
                        UnitTypeId.AUTOTURRET, unit.position)
                    order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                    actions.append(order)
                 
            else:
                threaten = self.bot.known_enemy_units.closer_than(
                        self.perimeter_radious, unit.position)
                
                if unit.health_percentage > 0.8 and unit.energy >= 50:
                    if threaten.amount > 0:
                        if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                            closest_threat = threaten.closest_to(unit.position)
                            pos = unit.position.towards(closest_threat.position, 5)
                            pos = await self.bot.find_placement(
                                UnitTypeId.AUTOTURRET, pos)
                            order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                            actions.append(order)
                    else:
                        if unit.distance_to(self.target) > 5:
                            order = unit.move(self.target)
                            actions.append(order)

                else:
                    if unit.distance_to(self.bot.terrein_manager.start_location) > 5:
                        order = unit.move(self.bot.terrein_manager.start_location)
                        actions.append(order)


        elif unit.type_id == UnitTypeId.MARAUDER:
            bunk = self.bot.units.of_type(UnitTypeId.BUNKER).owned
            
            if self.bot.vespene<=1:
                target1=frontplace
                actions.append(unit.attack(target1.to2))
            elif homeenemy>0:
                if unit.health_percentage > 0.8 and not unit.has_buff(BuffId.STIMPACKMARAUDER):
                # 스팀팩 사용
                    order = unit(AbilityId.EFFECT_STIM_MARAUDER)
                    actions.append(order)
                else:    
                    target1 = protectplace1
                    actions.append(unit.attack(target1.to2))
            else: 
                if medi.amount>0 and unit.position3d.z>10:
                    actions.append(unit.move(upper_bush))
                elif unit.position3d.z<=11:
                    actions.append(unit.move(bunkerplace))
                else:
                    actions.append(unit.move(self.target))
        
        elif unit.type_id == UnitTypeId.BUNKER and unit.position3d.x>40 and unit.position3d.x<50:
            if self.bot.vespene<=1:
                actions.append(unit(AbilityId.UNLOADALL_BUNKER))
                
            elif self.bot.units.of_type(UnitTypeId.MARAUDER).closer_than(5, bunkerplace).amount > 0:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z<=10).of_type(UnitTypeId.MARAUDER) 
                actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(bunkerplace)))
            elif self.bot.units.of_type(UnitTypeId.MARINE).closer_than(5, bunkerplace).amount > 0:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z<=10).of_type(UnitTypeId.MARINE) 
                actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(bunkerplace)))

        elif unit.type_id == UnitTypeId.SIEGETANK:
            distance2=((upper_bush.x-unit.position3d.x)**2 + (upper_bush.y-unit.position3d.y)**2)**0.5 
            distance=((center.x-unit.position3d.x)**2 + (center.y-unit.position3d.y)**2)**0.5 
            if homeenemy>0:
                order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                actions.append(order)
            else:

                if medi.amount>0 and unit.position3d.z>11:
                    actions.append(unit.move(upper_bush))
                elif unit.position3d.z<11:
                    n_enemy=self.bot.units.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(13,unit.position).amount
                    if n_enemy==0:
                        actions.append(unit.move(self.target))
                    else:
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                        actions.append(order)               
                    
       
        return actions

    async def normal_step(self, unit, friends, foes):
        n_unit= self.bot.units.of_type(SOL_TYPES).closer_than(11, self.strategic_points[2]).amount
        n_enemy = self.bot.known_enemy_units.closer_than(7,self.strategic_points[2]).amount
        n_enemy1 = self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).amount
        if n_unit>0 and n_enemy<=1 and self.bot.vespene>3:
            self.count=1
        
        actions = list()
        self.target = self.strategic_points[2]   
        
        base = self.bot.start_location
        center = self.strategic_points[2]
        homeenemy = self.bot.known_enemy_units.closer_than(10, base).amount
        
        if base.x<50:
            searchpoint = self.goal_point[3]
            bunkerplace=Point3((47.5,47.5,9.999828))
            protectplace1 = Point3((25.32,52.24,11.99))
            frontplace = Point3((68.82,66,9))

        else:
            searchpoint = self.goal_point[1]
            bunkerplace=Point3((40.5,40.5,10))
            protectplace1= Point3((62,35,11.99))
            frontplace = Point3((19.18,17.97,9))
            
            
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
        marine = self.bot.units.of_type(UnitTypeId.MARINE).owned
        reap = self.bot.units.of_type(UnitTypeId.REAPER).owned
        can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
        
    
        '''

        elif unit.type_id == UnitTypeId.MEDIVAC:   
            n_enemy=self.bot.known_enemy_units.of_type(CARE_TYPES).closer_than(7,unit.position).amount
            if n_enemy==0:
                actions.append(unit.move(searchpoint))
            else:
                actions.append(unit.move(center))
            
        '''    

        return actions
    
    async def attack_step(self, unit, friends, foes):
        actions = list()
        self.target = self.goal_point[3]   
        
        base = self.bot.start_location
        center = self.strategic_points[2]
        homeenemy = self.bot.known_enemy_units.closer_than(10, base).amount
        
        if base.x<50:
            searchpoint = self.goal_point[3]
            bunkerplace=Point3((47.5,47.5,9.999828))
            frontenemy= self.strategic_points[3]
            enemycenter= self.strategic_points[4]
            arriveplace= Point3((31.21,45.91,13.76))
            

        else:
            searchpoint = self.goal_point[1]
            bunkerplace=Point3((40.5,40.5,10))
            frontenemy= self.strategic_points[1]
            enemycenter = self.strategic_points[0]
            arriveplace =Point3((56.79,42.09,13.76))
            
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
        rep = self.bot.units.of_type(UnitTypeId.REAPER).owned.amount
        can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
        if unit.type_id == UnitTypeId.MARINE:
            actions.append(unit.move(self.strategic_points[2]))
        elif unit.type_id == UnitTypeId.REAPER:
            self.reaper.append(unit.tag)
            n_units = self.bot.units.of_type(UnitTypeId.REAPER).closer_than(13,frontenemy).amount
            n_enemy=self.bot.known_enemy_units.closer_than(13,frontenemy).amount
            if unit.tag==self.reaper[0]:
                threaten = self.bot.known_enemy_units.closer_than(
                        self.perimeter_radious, unit.position)
                enemy=self.bot.known_enemy_units.of_type(UnitTypeId.AUTOTURRET).closer_than(6,unit.position).amount
                if unit.health_percentage > 0.8 and unit.energy >= 50:
                    if threaten.amount > 0:
                        if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET and enemy==0:
                            closest_threat = threaten.closest_to(unit.position)
                            pos = unit.position.towards(closest_threat.position, 5)
                            pos = await self.bot.find_placement(
                                UnitTypeId.AUTOTURRET, pos)
                            order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                            actions.append(order)
                    else:
                        if unit.distance_to(base) > 5:
                            order = unit.move(base)
                            actions.append(order)
            else:
                if n_enemy>0:
                    threaten = self.bot.known_enemy_units.closer_than(
                            self.perimeter_radious, unit.position)
                    if unit.health_percentage > 0.8 and unit.energy >= 50:
                        if threaten.amount > 0:
                            if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                                closest_threat = threaten.closest_to(unit.position)
                                pos = unit.position.towards(closest_threat.position, 5)
                                pos = await self.bot.find_placement(
                                    UnitTypeId.AUTOTURRET, pos)
                                order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                                actions.append(order)
                                self.pet=1
                        else:
                            if unit.distance_to(frontenemy) > 5:
                                order = unit.move(frontenemy)
                                actions.append(order)
                                self.pet=0

                    else:
                        if unit.distance_to(self.bot.terrein_manager.start_location) > 5:
                            order = unit.move(self.bot.terrein_manager.start_location)
                            actions.append(order)
                else:
                    threaten = self.bot.known_enemy_units.closer_than(
                            self.perimeter_radious, unit.position)

                    if unit.health_percentage > 0.8 and unit.energy >= 50:
                        if threaten.amount > 0:
                            if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                                closest_threat = threaten.closest_to(unit.position)
                                pos = unit.position.towards(closest_threat.position, 5)
                                pos = await self.bot.find_placement(
                                    UnitTypeId.AUTOTURRET, pos)
                                order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                                actions.append(order)
                                
                        else:
                            if unit.distance_to(enemycenter) > 5:
                                order = unit.move(enemycenter)
                                actions.append(order)
                                

                    else:
                        if unit.distance_to(frontenemy) > 5:
                            order = unit.move(frontenemy)
                            actions.append(order)



        elif unit.type_id == UnitTypeId.MARAUDER:
            can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
            bunk = self.bot.units.of_type(UnitTypeId.BUNKER).owned
            n_enemy=self.bot.known_enemy_units.closer_than(13,frontenemy).amount
            n_unit=self.bot.units.of_type(UnitTypeId.MARAUDER).closer_than(5,arriveplace)
            n_unit1=self.bot.units.of_type(UnitTypeId.MARAUDER).closer_than(5,frontenemy)
            if n_unit.amount>=2:
                self.shy=1
            if n_unit1.amount>5 and n_enemy==0:
                self.shy=2
            if self.shy==0:
                actions.append(unit.move(arriveplace))
            elif self.shy==1:
                if n_enemy>0:
                    target1=frontenemy
                    actions.append(unit.attack(target1.to2)) 
                else:
                    actions.append(unit.move(frontenemy))
            elif self.shy==2:
                target1=enemycenter
                actions.append(unit.attack(target1.to2))
                  
        elif unit.type_id == UnitTypeId.BUNKER and unit.position3d.x>40 and unit.position3d.x<50:
            if unit.cargo_used>0:
                actions.append(unit(AbilityId.UNLOADALLAT))

        elif unit.type_id == UnitTypeId.SIEGETANK or unit.type_id == UnitTypeId.SIEGETANKSIEGED: 
            n=0
            for i in range(len(self.siege)):
                if unit.tag==self.siege[i]:
                    n=1
            if n==0:
                self.siege.append(unit.tag)
            
            distance=((center.x-unit.position3d.x)**2 + (center.y-unit.position3d.y)**2)**0.5 
            n_enemy=self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(13,unit.position)
            '''
            if unit.type_id == UnitTypeId.SIEGETANKSIEGED and n_enemy==0:
                order = unit(AbilityId.UNSIEGE_UNSIEGE)
                actions.append(order)
                '''
            if distance>3:
                actions.append(unit.move(center))
            else:    
                order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                actions.append(order)
       

        elif unit.type_id == UnitTypeId.MEDIVAC:   
            n_enemy = self.bot.known_enemy_units.of_type(CARE_TYPES).closer_than(11,unit.position).amount
            if n_enemy>0:
                actions.append(unit.move(self.strategic_points[2]))
            else:
                actions.append(unit.move(enemycenter))
            
            

        return actions

    def debug(self):
        text = [

            f'Tactics: {self.tactics}, state: {self.state},state:{self.count}',
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
            units = self.bot.units.of_type(ARMY_TYPES).owned
            unit_tags = units.tags
            manager.unit_tags = unit_tags

        elif manager.tactics is Tactics.NORMAL:
          
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

        if self.time <= 300:
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
        if self.time <= 300:
            actions += await self.first_manager.step()
        else:
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