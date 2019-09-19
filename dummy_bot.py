import sc2
import random
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units
import time
from IPython import embed
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import csv
import sys
import os

learning_rate = 0.0005

UNIT_TYPES = (UnitTypeId.MARINE, UnitTypeId.MARAUDER, 
    UnitTypeId.SIEGETANK, UnitTypeId.MEDIVAC, UnitTypeId.REAPER)

class network(nn.Module):
    def __init___(self):
        super(network, self).__init__()
        self.fc1 = nn.Linear(10,256)
        self.fc2=nn.Linear(256,1)
    
    def forward(self,x):
        x= F.relu(self.fc1(x))
        x= self.fc(x)
        return x
    
def train(q,input,expect,optimizer):
    loss=q.forward.item-expect
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()




class DummyBot(sc2.BotAI):    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.count1=0
        self.count2=0
        self.count3=0
        self.count4=0
        self.count5=0
        self.region_radius=13
        self.count=0
        self.switch=0
        self.vic=0
        self.defence=[]
        self.drop=[]
        self.l1=[]
        

    async def on_step(self, iteration: int):
        marine = [4,5,6,7,8,9]
        sieze = [1]
        sasine = [1]
        marauder = [1,2]
        med = [0,1]
        lie = [1,2,3]
        lie1 = [1,2,3]
        base = self.start_location
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
            transplace = Point3((50.30,66.31,9))
            arriveplace = Point3((63.92,34.5,11.99))
            arriveplace2 =  Point3((56.08,36.39,11.99))
        else:
            protectplace = Point3((62,35,11.99))
            transplace = Point3((37,21.6,9))
            arriveplace = Point3((24.08, 53.0,11.99))
            arriveplace2 = Point3((31.62,52.17,11.99))

        if self._client._player_id == 1: 
           
            if self.units.amount == 9 and self.time < 10:
                a=random.choice(marine)
                await self._client.debug_create_unit([[UnitTypeId.MARINE,a, protectplace,1]]) 
                self.count1=a
                
                if random.choice(lie1)==1:
                    b=random.choice(sasine)
                    await self._client.debug_create_unit([[UnitTypeId.REAPER,b, protectplace,1]]) 
                    self.count2=b
                    
                if random.choice(lie1)==1:
                    c=random.choice(sieze)
                    await self._client.debug_create_unit([[UnitTypeId.SIEGETANK,c, protectplace,1]])
                    self.count3=c
                                 
                if random.choice(lie)==1:
                    d=random.choice(marauder)
                    await self._client.debug_create_unit([[UnitTypeId.MARAUDER,d, protectplace,1]]) 
                    self.count4=d
                
                if random.choice(lie1)==1:
                    await self._client.debug_create_unit([[UnitTypeId.MEDIVAC,1, protectplace,1]])
                    self.count5=1
                
                    
                time.sleep(10)
               
                self.defence.append(self.count1)
                self.defence.append(self.count2)
                self.defence.append(self.count3)
                self.defence.append(self.count4)
                self.defence.append(self.count5)
                
            elif self.units.amount==9 and self.switch==0 and self.known_enemy_units.amount>0 and self.time>=40:
                print('ze')
                self.switch=1
                time.sleep(5)
                f=open('chang.csv','a',encoding='utf-8',newline='')
                wr=csv.writer(f)
                wr.writerow(self.defence)
                wr.writerow({1})
                f.close()
                

                

            elif self.units.amount>9 and self.known_enemy_units.amount==0 and self.switch==0 and self.time>=40:
                print('shy')
                self.switch=1
                time.sleep(5)
                f=open('chang.csv','a',encoding='utf-8',newline='')
                wr=csv.writer(f)
                wr.writerow(self.defence)
                wr.writerow({0})
                f.close()
                

            actions = list()
            for unit in self.units.of_type(UNIT_TYPES):
                if unit.type_id == UnitTypeId.REAPER:
                    threaten = self.known_enemy_units.closer_than(
                        7, unit.position)

                    if unit.energy >= 50:
                        if unit.health_percentage >= 0.9  and threaten.amount > 0:
                            if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                                closest_threat = threaten.closest_to(unit.position)
                                
                                pos = unit.position.towards(closest_threat.position, 7)
                                pos = await self.find_placement(
                                    UnitTypeId.AUTOTURRET,pos, 7)
                                
                                order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                                actions.append(order)
                await self.do_actions(actions)
            
            
            

        else:
                     
            if self.units.amount == 9:
                await self._client.debug_create_unit([[UnitTypeId.MARINE,random.choice(marine), transplace,2]]) 
                
                if random.choice(lie1)!=1:
                    await self._client.debug_create_unit([[UnitTypeId.REAPER,random.choice(sasine), transplace,2]]) 
                    
                if random.choice(lie1)!=1:
                    await self._client.debug_create_unit([[UnitTypeId.SIEGETANK,random.choice(sieze), transplace,2]])
                                 
                if random.choice(lie1)!=1:
                    await self._client.debug_create_unit([[UnitTypeId.MARAUDER,random.choice(marauder), transplace,2]]) 
                    
                await self._client.debug_create_unit([[UnitTypeId.MEDIVAC,1,transplace,2]])
                time.sleep(5)

            elif self.time >= 40 and not self.drop:
                self.count1=0
                self.count2=0
                self.count3=0
                self.count4=0
                for i in range(len(self.l1)):
                    if self.l1[i].name == 'Marine':
                        self.count1+=1
                    elif self.l1[i].name== 'Marauder':
                        self.count2+=1
                    elif self.l1[i].name == 'SiegeTank':
                        self.count3+=1
                    elif self.l1[i].name == 'Reaper':
                        self.count4+=1
                    
                self.count5=1
                self.drop.append(self.count1)
                self.drop.append(self.count2)
                self.drop.append(self.count3)
                self.drop.append(self.count4)
                self.drop.append(self.count5)
                time.sleep(5)
                f=open('chang1.csv','a',encoding='utf-8',newline='')
                wr=csv.writer(f)
                wr.writerow(self.drop)
                f.close()
                
                
                   
            else:
                

                actions = list()
                
                for unit in self.units.of_type(UNIT_TYPES):
                    n_units = self.units.closer_than(self.region_radius, arriveplace).amount
                    if unit.type_id == UnitTypeId.REAPER:
                        distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
                        '''
                       
                        n_enemy = enemy.closer_than(5, unit.position).amount
                        print(n_enemy)
                        if n_enemy>0:
                            
                        if distance3 <10:    
                            enemy = self.known_enemy_units
                            if unit.energy >= 50:
                                
                                closest_threat = enemy.closest_to(unit.position)
                                pos = closest_threat.position.towards(unit.position, 7)
                                pos = await self.find_placement(UnitTypeId.AUTOTURRET, pos)
                                order=unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)  
                                actions.append(order)
                        '''
                        if distance3<10:
                            threaten = self.known_enemy_units.closer_than(
                                7, unit.position)

                            if unit.energy >= 50:
                                if unit.health_percentage >= 0.9  and threaten.amount > 0:
                                    if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                                        closest_threat = threaten.closest_to(unit.position)
                                        
                                        pos = unit.position.towards(closest_threat.position, 5)
                                        pos = await self.find_placement(
                                            UnitTypeId.AUTOTURRET,pos, 7)
                                        
                                        order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                                        actions.append(order)
                    elif unit.type_id == UnitTypeId.MARINE:
                        distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
                        distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
                        distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
                        
                        if unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK) and distance3<5:
                            order = unit(AbilityId.EFFECT_STIM)
                            actions.append(order)
               
                
                    
                                
                    

                    elif unit.type_id == UnitTypeId.MARAUDER:
                        distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
                        enemy = self.known_enemy_units
                        n_enemy = enemy.closer_than(5, unit.position).amount
                        if n_enemy >= 1:
                            if unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK):
                                order = unit(AbilityId.EFFECT_STIM)
                                actions.append(order)
                        else:
                                order = unit(AbilityId.HOLDPOSITION)
                                actions.append(order)

                    elif unit.type_id == UnitTypeId.MEDIVAC:
                        distance2=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
                        distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
                        target_pssn = self.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE) 
                        target_pssn3 = self.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.SIEGETANK)   
                        target_pssn2 = self.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.REAPER) 
                        target_pssn4 = self.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARAUDER)
                        
                    
                        if target_pssn3.exists and unit.cargo_used<5 and distance<10:
                            actions.append(unit(AbilityId.LOAD,target_pssn3.closest_to(unit.position) ))
                            
                    
                         
                            
                        elif target_pssn4.exists and unit.cargo_used<7 and distance<10:
                            actions.append(unit(AbilityId.LOAD,target_pssn4.closest_to(unit.position) ))
                          
                          
                          
                        elif target_pssn2.exists and unit.cargo_used<8 and distance<10:
                            actions.append(unit(AbilityId.LOAD,target_pssn2.closest_to(unit.position) ))
                            
                         
                         
                        elif target_pssn.exists and unit.cargo_used<8 and distance<10:
                            actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(unit.position) ))
                
                           
                        elif unit.cargo_used==8 or self.units.amount==10:
                            if self.switch==0:
                                self.switch=1   
                                self.l1=list(unit.passengers)
                                for i in range( len(self.l1)):
                                    print(self.l1[i].name)
                                                  

                            '''
                                    if l1[i].name == 'Marine':
                                        self.count1+=1
                                    elif l1[i].name== 'Marauder':
                                        self.count2+=1
                                    elif l1[i].name == 'Siegetank':
                                        self.count3+=1
                                    else:
                                        self.count4+=1
                            '''            
                           
                            if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                                order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                                actions.append(order)
                            else:
    
                                if distance2 >10:
                                    actions.append(unit.move(arriveplace))
                                else:
                                    enemy = self.known_enemy_units
                                    n_enemy1 = enemy.closer_than(11, unit.position).amount
                               
                                    
                                        
                                    if n_enemy1 >5:
                                        
                                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                                    
                                    elif n_enemy1 <=5:
                                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))
                        elif distance2<10 and unit.cargo_used==0:
                            order = unit(AbilityId.HOLDPOSITION)
                            actions.append(order)
                                    
                                   
                                    
                    await self.do_actions(actions)
                

            
        self.debug()      
        await self._client.send_debug()
        

    def defencelist(self):
        return self.defence

    def droplist(self):
        return self.drop

    def debug(self):
        text = [

            f'marine: {self.count1}, marauder: {self.count2}, siegetank:{self.count3},reaper:{self.count4}',
        ]
        self._client.debug_text_screen(
            '\n\n'.join(text), pos=(0.02, 0.02), size=20)

        
    
        
 
        '''
        actions = list()
        await self.do_actions(actions)
        '''