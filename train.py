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
from dummy_bot import DummyBot

x=DummyBot()

print(x.on_step(60))
print(x.on_step(60))