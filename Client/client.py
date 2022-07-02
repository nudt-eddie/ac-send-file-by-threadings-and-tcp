import socket
import json
import struct
import os
from socket import SOL_SOCKET,SO_REUSEADDR
import struct
import threading
import zipfile

s = socket.socket()
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1) #就是它，在bind前加
s.bind(('0.0.0.0',8081))  #把地址绑定到套接字
s.listen()          #监听链接
def getFileInfo(file_path):
    if os.path.exists(file_path):
        size = os.path.getsize(filename=file_path)
        name = os.path.basename(file_path)
        return (size, name)
    else:
        return


'''client 把存储打包发送'''
def zip(filedir):
    """
    压缩文件夹至同名zip文件
    """
    file_news = filedir + '.zip'
    z = zipfile.ZipFile(file_news,'w',zipfile.ZIP_DEFLATED) #参数一：文件夹名
    for dirpath, dirnames, filenames in os.walk(filedir):
        fpath = dirpath.replace(filedir,'') #这一句很重要，不replace的话，就从根目录开始复制
        fpath = fpath and fpath + os.sep or ''#这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
        for filename in filenames:
            z.write(os.path.join(dirpath, filename),fpath+filename)
    z.close()

def send():
    
    while True:
        file_path = input("请输入文件路径:")
        file_size, file_name = getFileInfo(file_path)
        if not file_name:
            print("请输入正确路径!")
            return
        zip(file_path)
        file_path +=('.zip')
        file_size, file_name = getFileInfo(file_path)

        #自定制报头
        header={'file_size':file_size,'file_name':file_name}

        #为了该报头能传送,需要序列化并且转为bytes
        head_bytes=bytes(json.dumps(header),encoding='utf-8')
        #为了让客户端知道报头的长度,用struck将报头长度这个数字转成固定长度:4个字节
        #借助struct模块,我们知道长度数字可以被转换成一个标准大小的4字节数字。因此可以利用这个特点来预先发送数据长度。
        head_len_bytes=struct.pack('i',len(head_bytes)) #这4个字节里只包含了一个数字,该数字是报头的长度

        s = socket.socket()
        s.connect(('127.0.0.1',8080))
        #客户端开始发送
        s.send(head_len_bytes) #先发报头的长度,4个bytes
        s.send(head_bytes) #再发报头的字节格式
        with open(file_path, "rb") as f:
            s.send(f.read())
        # 关闭客户套接字
        s.close()
        os.remove(file_path)

def receive():
    while True:
        conn,addr = s.accept() #接受客户端链接

        head_len_bytes=conn.recv(4) #先收报头4个bytes,得到报头长度的字节格式
        x=struct.unpack('i',head_len_bytes)[0] #提取报头的长度，解包

        head_bytes=conn.recv(x) #按照报头长度x,收取报头的bytes格式
        header=json.loads(str(head_bytes, encoding="utf8")) #提取报头

        # 获取报头数据
        file_size = header["file_size"]
        file_name = header["file_name"]
        # 获取并保存文件数据
        
        with open(file_name, "wb") as f:
            while True:
                data = conn.recv(file_size)
                if not data:
                    print('接收完毕！')
                    break
                f.write(data)
                f.flush() #刷新缓冲区
                print("已经写入")




if __name__ == "__main__":
    t1 = threading.Thread(target = receive)
    t2 = threading.Thread(target = send)
    t1.start()
    t2.start()