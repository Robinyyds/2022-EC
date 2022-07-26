from pyb import UART #导入UART串口
uart = UART(3,500000)#初始化串口 UART3波特率 500000

class Receive(object):
    uart_buf = []
    _data_len = 0
    _data_cnt = 0
    state = 0

R=Receive() #接收数据缓存对象

# WorkMode=1为寻点模式
# WorkMode=2为寻线模式 包括直线 转角
class Ctrl(object):
    WorkMode = 0   #工作模式
    IsDebug = 1     #不为调试状态时关闭某些图形显示等，有利于提高运行速度
    T_ms = 0   #每秒有多少帧
    Shirk=0 #窗口是否缩放

#类的实例化
Ctr=Ctrl()


#串口发送数据
def UartSendData(Data):
    print("write data",Data[0],Data[1],Data[2],Data[3],Data[4],Data[5],Data[6])
    uart.write(Data)

#串口数据解析
def ReceiveAnl(data_buf,num):
    #和校验
    sum = 0
    i = 0
    while i<(num-1):
        sum = sum + data_buf[i]
        i = i + 1
    sum = sum%256 #求余
    if sum != data_buf[num-1]:
        return
    #和校验通过
    if data_buf[4]==0x06:
        #设置模块工作模式
        Ctr.WorkMode = data_buf[5]
        #设置窗口是否缩放
        Ctr.Shirk = data_buf[6]


#-----------------------------------通信协议::接收解帧----------------------------------------#
#串口通信协议接收:采用指针移动确定该放到哪个位置
#ReceivePrepare帧头校验
#  frame   header
#|---------------|
#                    len   data    和校验位
#0xAA 0xAF 0x05 0x01 0x06 [1,2,3]    x
def ReceivePrepare(data):
    if R.state==0:
        if data == 0xAA:
            R.uart_buf.append(data)
            R.state = 1
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==1:
        if data == 0xAF:
            R.uart_buf.append(data)
            R.state = 2
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==2:
        if data == 0x05:
            R.uart_buf.append(data)
            R.state = 3
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==3:
        if data == 0x01:#功能字
            R.state = 4
            R.uart_buf.append(data)
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==4:
        if data == 0x06:#数据个数
            R.state = 5
            R.uart_buf.append(data)
            R._data_len = data
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==5:
        if data==0 or data==1 or data==2 or data==3 or data==4:
            R.uart_buf.append(data)
            R.state = 6
        else:
            R.state = 0
            R.uart_buf=[]
    elif R.state==6:
        if data==0 or data==1:
            R.uart_buf.append(data)
            R.state=7
        else:
            R.state=0
            R.uart_buf=[]
    elif R.state==7:
        R.state = 0
        R.uart_buf.append(data)#
        ReceiveAnl(R.uart_buf,8)
        R.uart_buf=[]#清空缓冲区，准备下次接收数据
    else:
        R.state = 0
        R.uart_buf=[]





#读取串口缓存
def UartReadBuffer():
    i = 0
    Buffer_size = uart.any()
    #按字节读出,每个字节传进接收准备函数
    while i<Buffer_size:
        ReceivePrepare(uart.readchar())
        i = i + 1




#-----------------------------------通信协议::打包帧----------------------------------------#
#数据打包
def DataPack(x,y,dis,flag,code):#打包数据
    pack_data=bytearray([0xaa,0x41,0x00,int(x/256),x%256,int(y/256),y%256,int(dis/256),dis%256,int(flag/256),flag%256,int(code/256),code%256,0x00])
    lens = len(pack_data)#数据包大小
    pack_data[2] = 10;#有效数据个数
    i = 0
    sum = 0#和校验
    while i<(lens-1):
          sum = sum + pack_data[i]
          i = i+1
    pack_data[lens-1] = sum;
    return pack_data






#线检测数据打包
def LineDataPack(flag,angle,distance,crossflag,crossx,crossy,T_ms):
    if (flag == 0):
        print("found: angle",angle,"  distance=",distance,"   线状态   未检测到直线")
    elif (flag == 1):
        print("found: angle",angle,"  distance=",distance,"   线状态   直线")
    elif (flag == 2):
        print("found: angle",angle,"  distance=",distance,"   线状态   左转")
    elif (flag == 3):
        print("found: angle",angle,"  distance=",distance,"   线状态   右转")
    print("Send Data: ","flag: ",flag,"angle",angle,"dis: ",distance,"cross_flag: ",crossflag,"crossx ",crossx,"crossy ",crossy);
    line_data=bytearray([0xAA,0x29,0x05,0x42,0x00,flag,angle>>8,angle,distance>>8,distance,crossflag,crossx>>8,crossx,(-crossy)>>8,(-crossy),T_ms,0x00])
    lens = len(line_data)#数据包大小
    line_data[4] = 11;#有效数据个数
    i = 0
    sum = 0
    #和校验
    while i<(lens-1):
        sum = sum + line_data[i]
        i = i+1
    line_data[lens-1] = sum;
    return line_data


#用户数据打包
def UserDataPack(data0,data1,data2,data3,data4,data5,data6,data7,data8,data9):
    UserData=bytearray([0xAA,0x05,0xAF,0xF1,0x00
                        ,data0,data1,data2>>8,data2,data3>>8,data3
                        ,data4>>24,data4>>16,data4>>8,data4
                        ,data5>>24,data5>>16,data5>>8,data5
                        ,data6>>24,data6>>16,data6>>8,data6
                        ,data7>>24,data7>>16,data7>>8,data7
                        ,data8>>24,data8>>16,data8>>8,data8
                        ,data9>>24,data9>>16,data9>>8,data9
                        ,0x00])
    lens = len(UserData)#数据包大小
    UserData[4] = lens-6;#有效数据个数
    i = 0
    sum = 0
    #和校验
    while i<(lens-1):
        sum = sum + UserData[i]
        i = i+1
    UserData[lens-1] = sum;
    return UserData

