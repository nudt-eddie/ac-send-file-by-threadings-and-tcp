import socket
from socket import SOL_SOCKET,SO_REUSEADDR
import json
import struct
import os
import threading
import zipfile

from isort import file
s = socket.socket()
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)   #允许在同一端口上启动同一服务器的多个实例,还允许此IP 地址和端口捆绑到另一个套接口上
s.bind(('0.0.0.0',8080))  #把地址绑定到套接字
s.listen()          #监听链接
def receive():
    while True:
        conn,addr = s.accept() #接受客户端链接

        head_len_bytes=conn.recv(4) #先收报头4个bytes,得到报头长度的字节格式
        x=struct.unpack('i',head_len_bytes)[0] #提取报头的长度

        head_bytes=conn.recv(x) #按照报头长度x,收取报头的bytes格式
        header=json.loads(str(head_bytes, encoding="utf8")) #提取报头
        #print(header)

        # 获取报头数据
        file_size = header["file_size"]
        file_name = header["file_name"]
        # 获取并保存文件数据

        with open(file_name, "wb") as f:
            n = 0
            while True:
                n += 1
                data = conn.recv(file_size)
                if not data:
                    print('接收完毕！')
                    break
                f.write(data)
                f.flush()
                print("已经写入")
        unzip(file_name)
        os.remove(file_name)

def getFileInfo(file_path):
    if os.path.exists(file_path):
        size = os.path.getsize(filename=file_path)
        name = os.path.basename(file_path)
        return (size, name)
    else:
        return


def send():
    while True:
        file_path = input("请输入文件路径:")
        file_size, file_name = getFileInfo(file_path)
        if not file_name:
            print("请输入正确路径!")
            return
        
        #自定制报头
        header={'file_size':file_size,'file_name':file_name}

        #为了该报头能传送,需要序列化并且转为bytes
        head_bytes=bytes(json.dumps(header),encoding='utf-8')
        #为避免粘包
        #为了让客户端知道报头的长度,用struck将报头长度这个数字转成固定长度:4个字节
        #借助struct模块,我们知道长度数字可以被转换成一个标准大小的4字节数字。因此可以利用这个特点来预先发送数据长度。
        head_len_bytes=struct.pack('i',len(head_bytes)) #这4个字节里只包含了一个数字,该数字是报头的长度

        s = socket.socket()
        s.connect(('127.0.0.1',8081))
        #客户端开始发送
        s.send(head_len_bytes) #先发报头的长度,4个bytes
        s.send(head_bytes) #再发报头的字节格式
        with open(file_path, "rb") as f:
            s.send(f.read())
        # 关闭客户套接字
        s.close()
'''为了目录结构结构一致 解压缩'''
def unzip(file_name):
    """
    解压缩zip文件至同名文件夹
    """
    zip_ref = zipfile.ZipFile(file_name) # 创建zip 对象
    dic_path = "C:\\Users\\Lenovo\\Desktop\\eddieproject\\uploads\\"+ file_name.replace(".zip","")
    # 用os.remove()删除文件夹报错
    try:
        os.remove(dic_path)
    except Exception as result:
        print("报错1：%s"% result)
    # 用os.rmdir()删除非空文件夹报错
    try:
        os.rmdir(dic_path)
    except Exception as result:
        print("报错2：%s"%result)
    # 先删除文件夹中的文件，再删除空文件夹
    try:
        # for 循环删除文件夹中的文件
        for i in os.listdir(dic_path):
            # print(i)
            txt_path=os.path.join(dic_path,i)
            os.remove(txt_path)
        os.rmdir(dic_path)
    except Exception as result:
        print("报错3：%s"%result)
    os.mkdir(file_name.replace(".zip","")) # 创建同名子文件夹
    zip_ref.extractall(file_name.replace(".zip","")) # 解压zip文件内容到子文件夹,无法覆盖。

    zip_ref.close() # 关闭zip文件


if __name__ == "__main__":
    t1 = threading.Thread(target = receive)
    t2 = threading.Thread(target = send)
    t1.start()
    t2.start()