""" 
测试仿真： 车辆使用的例子
"""
import simpy


# 1. 定义车辆的行为，使用python的生成器，车辆在行驶和停止之间循环，需要写一个循环语句
def car(env_temp):
    while True:
        print('开始停车的时间为{}'.format(env_temp.now))
        parking_time = 5
        yield env_temp.timeout(parking_time) # 告诉时间控制器停车5小时
        print('开始行驶的时间为{}'.format(env_temp.now))
        driving_time = 2
        yield env_temp.timeout(driving_time) # 告诉时间控制器行驶2小时

# 创建时间控制器
env = simpy.Environment()
# 创建过程
env.process(car(env))
# 运行仿真
env.run(until=15)