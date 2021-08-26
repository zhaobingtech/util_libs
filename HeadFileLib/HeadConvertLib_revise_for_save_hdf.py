# -*- coding: utf-8 -*-
"""

Scope:
    1.Convert hdf to raw data that python can read
    
Update: 
2021-05-28: 
    1.  update the output of HeadFile._read_hdf() function , Param:rawMetaData , 
        it will convenient for python save data to hdf in some cases.
2021-02-19:
    1.  chinese path will fail to acess and read from tdms, need decode filepath 
        before read from tdms

@author: Zhao Bing

Created on Mon Jan  4 12:41:33 2021
Version 4

"""

import ctypes as ctypes  # 导入C类型库
import pytdms as pytdms  # 导入pytdms库
# import nptmds  # 导入
from nptdms import TdmsFile
import os as os
import time as time


#*****************************************************************************#
#-------------------------------  Class HdfFile-------------------------------#
#*****************************************************************************#
class HeadFile:
    '''
    __init__
    open()
    read_data()
    close()
    ----
    read_grp_chns()
    read_key()   usually use key word: unit_string, wf_increment, wf_samples, 
                 wf_start_offset

    '''

    def __init__(self):
        # self.path = path
        self.path = ''
        self.data_batch_size = 0
        self.group = ''
        self.channels = []
        self.err = ''
        self.attri = []
        self.rawdata = []
        return

    #------------------------------- method open -------------------------#
    #*------------------------------ method open -------------------------#
    def open(self, path, data_batch_size=1000000):
        self.path = path
        self.data_batch_size = data_batch_size
        self.err, self.meta, self.attri, self.rawdata = self.__read_hdf(
            self.path, 10000000)
        self.group, self.channels = self.read_grp_chns()
        return

    #------------------------------- method read_chns_data ----------------#
    #*------------------------------ method read_chns_data ----------------#

    def read_data(self, grp, chns, offset=0):
        '''
        read input channels data
        .

        Parameters
        ----------
        grp : TYPE
            DESCRIPTION.
        chns : TYPE
            DESCRIPTION.
        offset : TYPE, optional
            DESCRIPTION. The default is 0.

        Returns
        -------
        slt_data : TYPE
            DESCRIPTION.

        '''
        wf = Waveform()

        # 先转化位str进行结合
        slt_data = []

        # str数组化
        if (type(chns) == str or type(chns) == bytes):
            chns = [chns]

        # str数组化
        for chn in chns:
            if type(chn) == bytes:
                chn = bytes.decode(chn)
            if type(grp) == bytes:
                grp = bytes.decode(grp)

            key = "/'" + grp + "'/'" + chn + "'"
            key = str.encode(key)
            # print(key)
            wf.data.append(self.rawdata[key][offset::])
            wf.increment.append(self.read_key(grp, chn, 'wf_increment'))
            wf.unit.append(self.read_key(grp, chn, 'unit_string'))
            wf.name.append(chn[:])
            wf.x_name.append(self.read_key(grp, chn, 'wf_xname'))
            wf.x_offset.append(self.read_key(grp, chn, 'wf_start_offset'))
            wf.x_unit.append(self.read_key(grp, chn, 'wf_xunit_string'))

        return wf

    #------------------------------- method read_grp_chns ------------------#
    #*------------------------------ method read_grp_chns ------------------#

    def read_grp_chns(self):
        ''' 
        read group and channels name , return the group str, and channels' 
        name list
        '''
        grp = []
        chns = []

        list_chn = list(self.attri.keys())

        for key in list_chn:
            if type(key) == bytes:
                key = key.decode()

            chn_st_idx = str.find(key, "'/'")
            if (len(key) > 3) & (chn_st_idx > 0):
                # chns.append( key[chn_st_idx+1:-1].decode() )
                chns.append(key[chn_st_idx+3:-1])
                grp = key[2:chn_st_idx]

        self.group = grp
        self.channels = chns

        return grp, chns

    #------------------------------- method read_key ---------------------------#
    #*------------------------------ method read_key ---------------------------#

    def read_key(self, grp, chn, property_key):
        '''
        read file's key value by key words.
        usually use key word: unit_string, wf_increment, wf_samples,
        wf_start_offset

        Parameters
        ----------
        grp : str
            DESCRIPTION.
        chn : str or bytes
            DESCRIPTION.
        property_key : str or bytes
            DESCRIPTION.

        Returns
        -------
        value : TYPE
            DESCRIPTION.

        '''

        # 先转化位str进行结合
        if type(chn) == bytes:
            chn = bytes.decode(chn)
        if type(grp) == bytes:
            grp = bytes.decode(grp)
        if type(property_key) == str:
            property_key = property_key.encode()

        key = "/'" + grp + "'/'" + chn + "'"

        key = str.encode(key)
        # print(key)
        # 读取key下的属性
        property_datatype, value = self.attri[key][3][property_key]
        if type(value) == bytes:
            value = value.decode()
        # value.dtype = property_datatype
        return value

    #------------------------------- method __read_hdf ----------------------#
    #*------------------------------ method __read_hdf ----------------------#
    def __read_hdf(self, hdfpath, data_batch_size=10000000):
        '''
        Parameters
        ----------
        hdfpath : TYPE
            DESCRIPTION.
        data_batch_size : TYPE
            转化时处理的数据块size大小，硬件内存小的时候小，硬件内润大的时候使用大,默认
            推荐 10000000

        Returns
        -------
        Error_status : str
            DESCRIPTION.
        attribution : tuple
            DESCRIPTION.
        rawdata : tuple
            DESCRIPTION.'''

        #---------------------------数据格式check---------------------------------#
        # try:
        #     hdfpath = os.unicode(hdfpath, 'utf-8') # 经过编码处理
        # except:
        #     pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转
        # # os.listdir(hdfpath)

        if type(hdfpath) == str:
            hdfpath = hdfpath.encode('gbk')

        #-------------------------- 动态链接库调用--------------------------------#

        # 加载dll动态链接库函数
        path_convert = "dll_convert_hdf_v3.dll"
        path_pre = os.path.dirname(__file__)
        path_convert = path_pre + path_convert

        # print('path_convert', path_convert)
        # path_convert = path_convert.decode('utf-8')
        converthdf = ctypes.CDLL(path_convert)
        # converthdf= WinDLL(path_convert)

        # 创建C语言数据类型进行输入 bytes 类型
        len_ifn = len(hdfpath)+512  # 输入 char source_input[] C语言类型
        ifn = ctypes.create_string_buffer(len_ifn)
        ifn.raw = hdfpath

        # 输出 char path_out[], # C语言类型为文件路径输入端分配内存
        len_ofn = len_ifn
        ofn = ctypes.create_string_buffer(len_ofn)

        # char ErrorStatus[]
        err_code = ctypes.create_string_buffer(256)

        ##↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ ----- 动态链接库调用 ----- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##
        start = time.time()
        # 调用dll函数,并计算时间
        '''DLL_hdf_convert(char source_input[], 
        	int64_t data_mini_batch_size, char path_out[], char ErrorStatus[], 
        	int32_t len_path_out, int32_t len_Err_Status);'''
        converthdf.DLL_hdf_convert(
            ifn, data_batch_size, ofn, err_code, len_ofn, 256)

        end = time.time()
        print('convert cost time:', end-start)
        ##↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ ----- 动态链接库调用 ----- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑##

        Error_status = err_code.value  # 读取错误状态码
        print('Error:', str(Error_status))
        filename = ofn.value    # 读取tdms 数据
        # print('ofn.value:', filename)

        # filename = filename.decode('utf-8')
        # print("filename.decode('utf-8'):",filename)
        filename = filename.decode('gbk')
        # print(filename)
        # try:
        #     path = os.unicode(filename, 'utf-8') # 经过编码处理
        # except:
        #     pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转

        # print("filename.unicode('utf-8'):",filename)

        #-----------------------  读取临时文件数据到内存 ------------------------#

        attribution, rawdata = pytdms.read(filename)  # obj 头文件，数据rawdata
        #  如果需要的化，保存元信息_用于后面保存为hdf 未见
        rawMetaData = TdmsFile.read_metadata(filename)  # obj 头文件，数据rawdata
        os.remove(filename)    # 删除tdms 临时文件

        return Error_status, rawMetaData, attribution, rawdata

    #------------------------------- method close del ---------------------------#
    #*------------------------------ method close del ---------------------------#
    def __del__(self):
        del self

    def close(self):
        del self


#*****************************************************************************#
#-------------------------------  Class Waveform------------------------------#
#*****************************************************************************#
class Waveform:

    # time_start = []
    def __init__(self):

        self.data = []
        self.increment = []
        self.unit = []
        self.name = []
        self.x_name = []
        self.x_offset = []
        self.x_unit = []
        return


#*****************************************************************************#
#-------------------------------     Test      -------------------------------#
#*****************************************************************************#
def test():

    import matplotlib.pyplot as plt
    import numpy as np

    from HeadConvertLib import HeadFile
    # from HeadConvertLib import HeadFile # 从自定义文件中导入HeadFile库

    path = b"D:\\test\\test3.hdf"
    path = "D:\\test\\test3.hdf"
    
    folderPath= r'D:\10_Python\13_E_Matrix\01_provide_to_bingsoft\2021-07-05'
    fileName = r'2021-06-03_A SUVe_AE-702_EKK-hochlauf_20210421 A SUVe AEA-702 EKK-CKD AC line-run03.hdf' # size 426 MB
    hdfpath = folderPath + r'//' + fileName

    # create HeadFile Object
    testfile = HeadFile()

    # open HeadFile data
    testfile.open(path)
    
    testfile.open(hdfpath)

    # print attribution group and chennels
    print('group:', testfile.group)
    print('channels:', testfile.channels)

    # method 1: read selected data , last 1000 quantities,some channels
    data_slt1 = testfile.read_data(
        testfile.group, testfile.channels[1:3], -1000)

    # method 2: read selected data , with str name
    s = testfile.channels[1]
    print('channel 1 Name:', s)
    data_slt2 = testfile.read_data(testfile.group, s)

    # method 3: read all data , with str name
    data_slt_all = testfile.read_data(testfile.group, testfile.channels[:])

    # plot some channles data
    i = 0
    for chn_data in data_slt1.data:
        plt.figure()
        t = np.arange(
            0, data_slt1.increment[i]*(len(chn_data)-1), data_slt1.increment[i])
        plt.plot(t, chn_data[0:np.size(t)])
        plt.title(testfile.channels[i])
        i = i+1

    # close HeadFile Object
    del testfile
    
    
