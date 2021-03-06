#!/usr/bin/env python
import rospy
from std_msgs.msg import Float32, Int16
from rosserial_arduino.msg import wheelchair_base  

initiate = 0
compassX_old = 0
count = 0
answer = 0.0
gyro_ans = 0.0
delta_t = 0.05
x_bias = -0.02612
encoderL=0
encoderR=0
compass_data =0

def callback(data):
     global delta_t, x_bias, gyro_ans
     global answer
     global compassX_old
     global initiate
     global encoderL, encoderR
     if initiate == 0:
       kc.x_angle = data.compass
       compassX_old = data.compass
       initiate = 1
       gyro_ans = kc.x_angle
     new_rate = data.gyro
     new_angle = angle_converter(data)
     kal = kc()
     answer = kal.kalmanFilter(new_angle, new_rate)
     gyro_ans += delta_t*(new_rate - x_bias)
     answer = answer - count*360.0
     encoderL=data.lwheel
     encoderR=data.rwheel
     #rospy.loginfo(answer)
     

def listener():
       global answer, encoderL, encoderR
       global gyro_ans
       # In ROS, nodes are uniquely named. If two nodes with the same
       # node are launched, the previous one is kicked off. The
       # anonymous=True flag means that rospy will choose a unique
       # name for our 'listener' node so that multiple listeners can
       # run simultaneously.
       
       pub = rospy.Publisher('kalmanOutput', Float32, queue_size = 10)
       pub2 = rospy.Publisher('lwheel', Int16, queue_size = 10)
       pub3 = rospy.Publisher('rwheel', Int16, queue_size = 10)
       rospy.init_node('kalman', anonymous=True)
   
       rospy.Subscriber("base_node", wheelchair_base, callback)
       r=rospy.Rate(20.0)
       while not rospy.is_shutdown():       
           pub.publish(answer)
           pub2.publish(encoderL)
           pub3.publish(encoderR)
           #rospy.loginfo(encoderL)
           r.sleep()
       # spin() simply keeps python from exiting until this node is stopped
       rospy.spin()
 
def angle_converter(data):
    global compassX_old
    global count
    if ((data.compass - compassX_old) < -300):
      count += 1;
    elif (data.compass - compassX_old > 300):
      count -= 1;
    compass_data = data.compass + count*360
    compassX_old = data.compass
    #rospy.loginfo(compass_data)
    return compass_data


class kc:
    Q_gyro = 0.0008351
    Q_bias = 0.001
    R_compass = 0.099856
    x_angle = 0.0
    x_bias = -0.02612
    P_00 = 0.0
    P_01 = 0.0
    P_10 = 0.0
    P_11 = 0.0
    dt =0.05
    y = 0.0
    S = 0.0
    K_0 =0.0
    K_1 = 0.0
    
    def kalmanCalculate(self,newAngle,newRate):
        kc.x_angle += kc.dt*(newRate - kc.x_bias)
        kc.P_00 +=  - kc.dt * (kc.P_10 + kc.P_01) + kc.Q_gyro * kc.dt
        kc.P_01 +=  - kc.dt * kc.P_11
        kc.P_10 +=  - kc.dt * kc.P_11
        kc.P_11 +=  + kc.Q_bias * kc.dt

        kc.y = newAngle - kc.x_angle
        kc.S = kc.P_00 + kc.R_compass
        kc.K_0 = kc.P_00 / kc.S
        kc.K_1 = kc.P_10 / kc.S

        kc.x_angle +=  kc.K_0 * kc.y
        kc.x_bias  +=  kc.K_1 * kc.y
        kc.P_00 -= kc.K_0 * kc.P_00
        kc.P_01 -= kc.K_0 * kc.P_01
        kc.P_10 -= kc.K_1 * kc.P_00
        kc.P_11 -= kc.K_1 * kc.P_01
        return kc.x_angle

    def kalmanFilter(self,newAngle,newRate):    
        kc.x_angle += kc.dt*(newRate - kc.x_bias)

        kc.y = newAngle - kc.x_angle
        kc.S = kc.P_00 + kc.R_compass
        kc.K_0 = (kc.P_00 - kc.P_10*kc.dt) / kc.S
        kc.K_1 = kc.P_10 / kc.S

        kc.x_angle +=  kc.K_0 * kc.y
        kc.x_bias  +=  kc.K_1 * kc.y
        
        kc.P_00 = kc.P_00 - (kc.P_01 + kc.P_10) * kc.dt + kc.P_11 * kc.dt*kc.dt + kc.Q_gyro*kc.dt*kc.dt - kc.K_0 * kc.P_00 + kc.K_0 * kc.P_01 * kc.dt;
        kc.P_01 = kc.P_01 - kc.P_11*kc.dt - kc.K_0 * kc.P_01
        kc.P_10 = kc.P_10 - kc.P_11*kc.dt - kc.K_1 * kc.P_00 + kc.K_1*kc.P_01*kc.dt
        kc.P_11 = kc.P_11 + kc.Q_bias - kc.K_1 * kc.P_01
    
        return kc.x_angle
        
if __name__ == '__main__':
     listener()
