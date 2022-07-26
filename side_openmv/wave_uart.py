from pyb import UART #导入UART串口
uart = UART(1,9600)#初始化串口 UART1波特率 9600


def wave_dis():
    read=uart.read()
    if read[0]==82:
        dis=1000*read[1]+100*read[2]+10*read[3]+read[4]
    return dis
