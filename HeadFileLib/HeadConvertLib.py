# -*- coding: utf-8 -*-
"""

Scope:
    1.Convert hdf to raw data that python can read
    
Update:
2021-09-26:
    1. update the function "revise_hdf_file_ch_order(hdf_filepath)", that function can revise the hdf file read bug
        Bug root cause : if record device has too many channels, the head file will use the dot dot (..)
        to represent the channels , like below:
        ch order:    16*1,16*2,16*3,16*4,16*5,16*6,16*7,16*8,16*9,16*10,16*11,
        16*12,16*13,16*14,16*15,16*16,16*17,16*18,16*19,16*20,21,..,25
2021-05-28: 
    1.  update the output of HeadFile._read_hdf() function , Param:rawMetaData , 
        it will convenient for python save data to hdf in some cases.
2021-02-19:
    1.  chinese path will fail to acess and read from tdms, need decode filepath 
        before read from tdms

@author: Zhao Bing
@Email: zhaobingtech@163.com
Created on Mon Jan  4 12:41:33 2021
Version 4

"""

import ctypes as ctypes  # 导入C类型库
import pytdms as pytdms  # 导入pytdms库
# import nptmds  # 导入
from nptdms import TdmsFile
import os as os
import time as time
import shutil
import sys


#

# sys.path.append(os.path.dirname(__file__))

# *****************************************************************************#
# -------------------------------  Class HdfFile-------------------------------#
# *****************************************************************************#
class HeadFile:
    """
    __init__
    open()
    read_data()
    close()
    ----
    read_grp_chns()
    read_key()   usually use key word: unit_string, wf_increment, wf_samples, 
                 wf_start_offset

    """

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

    # ------------------------------- method open -------------------------#
    # *------------------------------ method open -------------------------#
    def open(self, path, data_batch_size=1000000):
        self.path = path
        self.data_batch_size = data_batch_size
        self.err, self.meta, self.attri, self.rawdata = self.__read_hdf(
            self.path, 10000000)
        self.group, self.channels = self.read_grp_chns()
        return

    # ------------------------------- method read_chns_data ----------------#
    # *------------------------------ method read_chns_data ----------------#

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

    # ------------------------------- method read_grp_chns ------------------#
    # *------------------------------ method read_grp_chns ------------------#

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
                chns.append(key[chn_st_idx + 3:-1])
                grp = key[2:chn_st_idx]

        self.group = grp
        self.channels = chns

        return grp, chns

    # ------------------------------- method read_key ---------------------------#
    # *------------------------------ method read_key ---------------------------#

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

    # ------------------------------- method __read_hdf ----------------------#
    # *------------------------------ method __read_hdf ----------------------#
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

        # ---------------------------数据格式check---------------------------------#
        # try:
        #     hdfpath = os.unicode(hdfpath, 'utf-8') # 经过编码处理
        # except:
        #     pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转
        # # os.listdir(hdfpath)

        tmp_hdfpath = hdfpath
        _delete_tmp_tdms_file(tmp_hdfpath)

        if type(hdfpath) == str:
            hdfpath = hdfpath.encode('gbk')

        # -------------------------- 动态链接库调用--------------------------------#

        # 加载dll动态链接库函数
        path_convert = "dll_convert_hdf_v3.dll"
        path_pre = os.path.dirname(__file__)
        path_convert = path_pre + '/' + path_convert

        converthdf = ctypes.CDLL(path_convert)
        # converthdf= WinDLL(path_convert)

        # 创建C语言数据类型进行输入 bytes 类型
        len_ifn = len(hdfpath) + 512  # 输入 char source_input[] C语言类型
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
        print('convert cost time:', end - start)
        ##↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ ----- 动态链接库调用 ----- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑##

        Error_status = err_code.value  # 读取错误状态码
        print('Error:', str(Error_status))
        filename = ofn.value  # 读取tdms 数据
        # print('ofn.value:', filename)

        # filename = filename.decode('utf-8')
        # print("filename.decode('utf-8'):",filename)
        filename = filename.decode('gbk')
        # print(filename)

        # print("filename.unicode('utf-8'):",filename)

        # -----------------------  读取临时文件数据到内存 ------------------------#

        attribution, rawdata = pytdms.read(filename)  # obj 头文件，数据rawdata
        #  如果需要的化，保存元信息_用于后面保存为hdf 未见
        rawMetaData = TdmsFile.read_metadata(filename)  # obj 头文件，数据rawdata
        os.remove(filename)  # 删除tdms 临时文件
        # _delete_tmp_tdms_file(tmp_hdfpath)

        return Error_status, rawMetaData, attribution, rawdata

    # ------------------------------- method close del ---------------------------#
    # *------------------------------ method close del ---------------------------#
    def __del__(self):
        del self

    def close(self):
        del self


# *****************************************************************************#
# -------------------------------  Class Waveform------------------------------#
# *****************************************************************************#
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


class Waveform_2:

    # time_start = []
    def __init__(self):
        self.data = []
        self.increment = int(1)
        self.start_time = 0
        self.attrs = dict()
        self.attrs['unit'] = ''
        return


def _delete_tmp_tdms_file(hdfpath):
    folder_path, filename = os.path.split(hdfpath)

    test_tdms_path = folder_path + '/' + 'test.tdms'
    test_tdms_index_path = folder_path + '/' + 'test.tdms_index'

    op_log = ''
    if os.path.isfile(test_tdms_path):
        try:
            os.remove(test_tdms_path)
        except:
            ...
        op_log += ' remove test.tdms !'
    if os.path.isfile(test_tdms_index_path):
        try:
            os.remove(test_tdms_index_path)
        except:
            ...
        op_log += ' remove test.tdms_index!'

    if len(op_log) == 0:
        op_log = 'no tmp file'

    return op_log


def trans_hdf_2_tdms(hdfpath, tdms_folder=None, data_batch_size=10000000, encoding='utf-8'):
    """


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
        DESCRIPTION.
        """
    version = 'dll_convert_hdf_v4.dll'
    if encoding == 'utf8':
        encoding = 'utf-8'
    # ---------------------------数据格式check---------------------------------#
    # try:
    #     hdfpath = os.unicode(hdfpath, 'utf-8') # 经过编码处理
    # except:
    #     pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转
    # # os.listdir(hdfpath)
    print('trans_hdf_2_tdms')
    # pre_delete the test.tdms file
    print('1')
    tmp_hdf_path = hdfpath
    _delete_tmp_tdms_file(tmp_hdf_path)

    if type(hdfpath) == str:
        hdfpath_ = '\\'.join(hdfpath.split('/'))
        if encoding == 'gbk':
            hdfpath_ = hdfpath_.encode('gbk')
        else:
            hdfpath_ = hdfpath_.encode('utf-8')

    # -------------------------- 动态链接库调用--------------------------------#
    print('2')
    # 加载dll动态链接库函数

    if version == 'dll_convert_hdf_v4.dll':
        path_convert = r"dll_convert_hdf_v4.dll"
    elif version == 'dll_convert_hdf_v3.dll':
        path_convert = r"dll_convert_hdf_v3.dll"
    path_pre = os.path.dirname(__file__)
    path_convert = path_pre + r'/' + path_convert

    converthdf = ctypes.CDLL(path_convert)
    # converthdf= WinDLL(path_convert)

    # 创建C语言数据类型进行输入 bytes 类型
    len_ifn = len(hdfpath_) + 512  # 输入 char source_input[] C语言类型
    ifn = ctypes.create_string_buffer(len_ifn)
    ifn.raw = hdfpath_
    print('3')
    print('hdfpath_:', hdfpath_)
    # 输出 char path_out[], # C语言类型为文件路径输入端分配内存
    len_ofn = len_ifn
    ofn = ctypes.create_string_buffer(len_ofn)

    # char ErrorStatus[]
    err_code = ctypes.create_string_buffer(256)

    # remove test.tdms before generate tdms

    ##↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ ----- 动态链接库调用 ----- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##
    start = time.time()

    # 调用dll函数,并计算时间
    '''DLL_hdf_convert(char source_input[], 
        int64_t data_mini_batch_size, char path_out[], char ErrorStatus[], 
        int32_t len_path_out, int32_t len_Err_Status);'''
    if version == 'dll_convert_hdf_v4.dll':
        Enum_gbkCode = ctypes.c_uint16(1)
        Enum_utf8Code = ctypes.c_uint16(0)
        if encoding == 'gbk':
            code_enum = Enum_gbkCode
        else:
            code_enum = Enum_utf8Code
        converthdf.DLL_hdf_convert_v4(ifn, ctypes.pointer(code_enum), data_batch_size, ofn, err_code, len_ofn, 256)
    elif version == 'dll_convert_hdf_v3.dll':
        converthdf.DLL_hdf_convert(
            ifn, data_batch_size, ofn, err_code, len_ofn, 256)

    end = time.time()
    print('convert cost time:', end - start)
    ##↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ ----- 动态链接库调用 ----- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑##

    Error_status = err_code.value  # 读取错误状态码
    print('Error:', str(Error_status))
    filename = ofn.value  # 读取tdms 数据
    print('ofn.value:', filename)

    # filename = filename.decode('utf-8')
    # print("filename.decode('utf-8'):",filename)
    if encoding == 'gbk':
        srcfilename = filename.decode('gbk')
    else:
        srcfilename = filename.decode('utf-8')

    tdms_index_fn = srcfilename[:-4] + 'tdms_index'

    print('srcfilename:', srcfilename)
    # if .tdms already exsit, delet it first
    if os.path.isfile(tdms_index_fn):
        try:
            os.remove(tdms_index_fn)
        except:
            pass

    # -----------------------  读取临时文件数据到内存 ------------------------#

    # attribution, rawdata = pytdms.read(filename)  # obj 头文件，数据rawdata
    #  如果需要的化，保存元信息_用于后面保存为hdf 未见
    # rawMetaData = TdmsFile.read_metadata(filename)  # obj 头文件，数据rawdata
    if type(hdfpath) == bytes:
        if encoding == 'gbk':
            hdfpath = hdfpath.decode('gbk')
        else:
            hdfpath = hdfpath.decode('utf-8')

    dstPath = hdfpath[:-4] + '.tdms'
    print(dstPath)

    # if .tdms already exsit, delet it first
    if os.path.isfile(dstPath):
        try:
            # os.remove(dstPath)
            pass
        except:
            pass

    # print(srcfilename)

    # rename test.tdms to destination file name
    # if os.path.isfile(srcfilename):
    #     try:
    #         os.rename(srcfilename, dstPath)
    #     except:
    #         print('%s not exsit', dstPath)
    #         pass
    # else:
    #     print('no tdms file')
    print('end')
    # del test.tdms
    # _delete_tmp_tdms_file(tmp_hdf_path)

    # move new tdms files to tdmspath
    # if tdms_folder is not None:
    #     print('--' * 10)
    #     if os.path.isdir(tdms_folder):
    #         try:
    #             shutil.copy(dstPath, tdms_folder)
    #             os.remove(dstPath)
    #         except IOError as e:
    #             print("Unable to copy file. %s" % e)
    #         except:
    #             print("Unexpected error:", sys.exc_info())

    return dstPath


def _trans_hdf_2_tdms_v4(hdfpath, tdms_folder=None, data_batch_size=10000000, encoding='utf-8'):
    """


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
        DESCRIPTION.
        """
    version = 'dll_convert_hdf_v4.dll'
    if encoding == 'utf8':
        encoding = 'utf-8'
    # ---------------------------数据格式check---------------------------------#
    # try:
    #     hdfpath = os.unicode(hdfpath, 'utf-8') # 经过编码处理
    # except:
    #     pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转
    # # os.listdir(hdfpath)
    print('trans_hdf_2_tdms')
    # pre_delete the test.tdms file
    print('1')
    tmp_hdf_path = hdfpath
    _delete_tmp_tdms_file(tmp_hdf_path)

    if type(hdfpath) == str:
        hdfpath_ = '\\'.join(hdfpath.split('/'))
        if encoding == 'gbk':
            hdfpath_ = hdfpath_.encode('gbk')
        else:
            hdfpath_ = hdfpath_.encode('utf-8')

    # -------------------------- 动态链接库调用--------------------------------#
    print('2')
    # 加载dll动态链接库函数

    if version == 'dll_convert_hdf_v4.dll':
        path_convert = r"dll_convert_hdf_v4.dll"
    elif version == 'dll_convert_hdf_v3.dll':
        path_convert = r"dll_convert_hdf_v3.dll"
    path_pre = os.path.dirname(__file__)
    path_convert = path_pre + r'/' + path_convert

    converthdf = ctypes.CDLL(path_convert)
    # converthdf= WinDLL(path_convert)

    # 创建C语言数据类型进行输入 bytes 类型
    len_ifn = len(hdfpath_) + 512  # 输入 char source_input[] C语言类型
    ifn = ctypes.create_string_buffer(len_ifn)
    ifn.raw = hdfpath_
    print('3')
    print('hdfpath_:', hdfpath_)
    # 输出 char path_out[], # C语言类型为文件路径输入端分配内存
    len_ofn = len_ifn
    ofn = ctypes.create_string_buffer(len_ofn)

    # char ErrorStatus[]
    err_code = ctypes.create_string_buffer(256)

    # remove test.tdms before generate tdms

    ##↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ ----- 动态链接库调用 ----- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##
    start = time.time()

    # 调用dll函数,并计算时间
    '''DLL_hdf_convert(char source_input[], 
        int64_t data_mini_batch_size, char path_out[], char ErrorStatus[], 
        int32_t len_path_out, int32_t len_Err_Status);'''
    if version == 'dll_convert_hdf_v4.dll':
        Enum_gbkCode = ctypes.c_uint16(1)
        Enum_utf8Code = ctypes.c_uint16(0)
        if encoding == 'gbk':
            code_enum = Enum_gbkCode
        else:
            code_enum = Enum_utf8Code
        converthdf.DLL_hdf_convert_v4(ifn, ctypes.pointer(code_enum), data_batch_size, ofn, err_code, len_ofn, 256)
    elif version == 'dll_convert_hdf_v3.dll':
        converthdf.DLL_hdf_convert(
            ifn, data_batch_size, ofn, err_code, len_ofn, 256)

    end = time.time()
    print('convert cost time:', end - start)
    ##↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ ----- 动态链接库调用 ----- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑##

    Error_status = err_code.value  # 读取错误状态码
    print('Error:', str(Error_status))
    filename = ofn.value  # 读取tdms 数据
    print('ofn.value:', filename)

    # filename = filename.decode('utf-8')
    # print("filename.decode('utf-8'):",filename)
    if encoding == 'gbk':
        srcfilename = filename.decode('gbk')
    else:
        srcfilename = filename.decode('utf-8')

    tdms_index_fn = srcfilename[:-4] + 'tdms_index'

    print('srcfilename:', srcfilename)
    # if .tdms already exsit, delet it first
    if os.path.isfile(tdms_index_fn):
        try:
            os.remove(tdms_index_fn)
        except:
            pass

    # -----------------------  读取临时文件数据到内存 ------------------------#

    # attribution, rawdata = pytdms.read(filename)  # obj 头文件，数据rawdata
    #  如果需要的化，保存元信息_用于后面保存为hdf 未见
    # rawMetaData = TdmsFile.read_metadata(filename)  # obj 头文件，数据rawdata
    if type(hdfpath) == bytes:
        if encoding == 'gbk':
            hdfpath = hdfpath.decode('gbk')
        else:
            hdfpath = hdfpath.decode('utf-8')

    dstPath = hdfpath[:-4] + '.tdms'
    print(dstPath)

    # if .tdms already exsit, delet it first
    if os.path.isfile(dstPath):
        try:
            # os.remove(dstPath)
            pass
        except:
            pass

    # print(srcfilename)

    # rename test.tdms to destination file name
    # if os.path.isfile(srcfilename):
    #     try:
    #         os.rename(srcfilename, dstPath)
    #     except:
    #         print('%s not exsit', dstPath)
    #         pass
    # else:
    #     print('no tdms file')
    print('end')
    # del test.tdms
    # _delete_tmp_tdms_file(tmp_hdf_path)

    # move new tdms files to tdmspath
    # if tdms_folder is not None:
    #     print('--' * 10)
    #     if os.path.isdir(tdms_folder):
    #         try:
    #             shutil.copy(dstPath, tdms_folder)
    #             os.remove(dstPath)
    #         except IOError as e:
    #             print("Unable to copy file. %s" % e)
    #         except:
    #             print("Unexpected error:", sys.exc_info())

    return dstPath


def _trans_hdf_2_tdms_v3(hdfpath, tdms_folder=None, data_batch_size=10000000, encoding='utf-8'):
    """
    this is a back for 'dll_convert_hdf_v3.dll' files


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
        DESCRIPTION.
        """
    # ---------------------------数据格式check---------------------------------#

    # pre_delete the test.tdms file
    tmp_hdf_path = hdfpath
    _delete_tmp_tdms_file(tmp_hdf_path)

    if type(hdfpath) == str:
        hdfpath_ = '\\'.join(hdfpath.split('/'))
        hdfpath_ = hdfpath_.encode('utf-8')  # dll v3 version use utf-8 as input bytes string

    # -------------------------- 动态链接库调用--------------------------------#
    # 加载dll动态链接库函数

    path_convert = r"dll_convert_hdf_v3.dll"
    path_pre = os.path.dirname(__file__)
    path_convert = path_pre + r'/' + path_convert

    converthdf = ctypes.CDLL(path_convert)
    # converthdf= WinDLL(path_convert)

    # 创建C语言数据类型进行输入 bytes 类型
    len_ifn = len(hdfpath_) + 512  # 输入 char source_input[] C语言类型
    ifn = ctypes.create_string_buffer(len_ifn)
    ifn.raw = hdfpath_
    print('hdfpath_:', hdfpath_)
    # 输出 char path_out[], # C语言类型为文件路径输入端分配内存
    len_ofn = len_ifn
    ofn = ctypes.create_string_buffer(len_ofn)
    # char ErrorStatus[]
    err_code = ctypes.create_string_buffer(256)

    # remove test.tdms before generate tdms

    ##↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ ----- 动态链接库调用 ----- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##
    start = time.time()

    # 调用dll函数,并计算时间
    '''DLL_hdf_convert(char source_input[], 
        int64_t data_mini_batch_size, char path_out[], char ErrorStatus[], 
        int32_t len_path_out, int32_t len_Err_Status);'''

    converthdf.DLL_hdf_convert(
        ifn, data_batch_size, ofn, err_code, len_ofn, 256)

    end = time.time()
    print('convert cost time:', end - start)
    ##↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ ----- 动态链接库调用 ----- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑##

    Error_status = err_code.value  # 读取错误状态码
    print('Error:', str(Error_status))
    filename = ofn.value  # 读取tdms 数据
    print('ofn.value:', filename)

    # filename = filename.decode('utf-8')
    # print("filename.decode('utf-8'):",filename)

    srcfilename = filename.decode('utf-8')
    print('srcfilename:', srcfilename)

    # 保存的tdms文件路径
    dstPath = hdfpath[:-4] + '.tdms'
    print(dstPath)

    # if .tdms already exsit, delet it first
    if os.path.isfile(dstPath):
        try:
            os.remove(dstPath)
        except:
            pass

    # rename test.tdms to destination file name
    if os.path.isfile(srcfilename):
        try:
            os.rename(srcfilename, dstPath)
        except:
            print('%s not exsit', dstPath)
            pass
    else:
        print('no tdms file')

    # del test.tdms and test.tdms_index
    _delete_tmp_tdms_file(tmp_hdf_path)

    # move new tdms files to tdmspath if nessersary
    if tdms_folder is not None:
        print('--' * 10)
        if os.path.isdir(tdms_folder):
            try:
                shutil.copy(dstPath, tdms_folder)
                os.remove(dstPath)
                fp, fn = os.path.split(dstPath)
                dstPath = tdms_folder + '/' + fn
            except IOError as e:
                print("Unable to copy file. %s" % e)
            except:
                print("Unexpected error:", sys.exc_info())

    return dstPath


def trans_hdf_2_h5_file(hdf_path, h5_path=None, keep_tdms=False):
    """

    Parameters
    ----------
    hdf_path: path string
        hdf path

    Returns
    -------
    h5filepath: path string.
        h5 file path , converted file

    """
    tmp_hdf_path = hdf_path
    print('1')
    print(hdf_path)
    tdmsFileInst = trans_hdf_2_tdms(hdf_path)
    print(tdmsFileInst)
    print('2')
    h5FileObj = TdmsFile(tdmsFileInst)  # read the tdms obj
    # TdmsFile.
    print('3')
    h5filepath = tdmsFileInst[:-5] + '.h5'
    h5FileObj.as_hdf(tdmsFileInst[:-5] + '.h5')  # trans tdms to hdf
    print('4')
    # delete the test.tdms
    _delete_tmp_tdms_file(tmp_hdf_path)

    if keep_tdms == False:
        try:
            os.remove(tdmsFileInst)
        except IOError as e:
            print('io error')
        except:
            print('remove error')

    # try:
    #     os.remove(tdmsFileInst)
    # except:
    #         pass

    if h5_path is not None:
        ...
    return h5filepath


# *****************************************************************************#
# -------------------------------     Test      -------------------------------#
# *****************************************************************************#
def test():
    import matplotlib.pyplot as plt
    import numpy as np

    from HeadConvertLib import HeadFile
    # from HeadConvertLib import HeadFile # 从自定义文件中导入HeadFile库

    c = 2

    if c == 0:

        path = b"D:\\test\\test3.hdf"
        path = "D:\\test\\test3.hdf"

        # create HeadFile Object
        testfile = HeadFile()

        # open HeadFile data
        testfile.open(path)

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
                0, data_slt1.increment[i] * (len(chn_data) - 1), data_slt1.increment[i])
            plt.plot(t, chn_data[0:np.size(t)])
            plt.title(testfile.channels[i])
            i = i + 1

        # close HeadFile Object
        del testfile

    elif c == 2:
        path = r'C:\Users\zhaob\Desktop\ASUVE AP1-31 Base- S1 Com+ VZ run06'

        x = trans_hdf_2_h5_file(path)


def _has_key_start_of_data(fr, st_of_data=65536, inc_chunk=65536):
    """
    Check the .hdf file whether has the start of data information in header

    Parameters
    ----------
    fr: file instance
        file instance,must need read by 'rb' mode
    st_of_data: int
        the start of head file raw data, before is header of the file

    Returns
    -------

    """

    start_of_data_key = b'start of data:'
    start_of_data_flag = False
    start_of_data_int = 0

    max_search_length = 63356 * 3

    EOF_Flag = False
    st_of_data = int(st_of_data)
    if st_of_data <= 0:
        raise ValueError('input parameter is error, need a value bigger than zero')
    if st_of_data <= 2000:
        st_of_data = 2000

    if inc_chunk <= 2000:
        inc_chunk = 2000

    pos = fr.tell()
    fr.seek(0)
    while not EOF_Flag:

        bytes_blk = fr.read(st_of_data)

        if len(bytes_blk) == st_of_data:
            EOF_Flag = False
        else:
            EOF_Flag = True

        if start_of_data_key in bytes_blk:
            idx_start = bytes_blk.index(start_of_data_key)
            if b'\r\n' in bytes_blk[idx_start:]:
                idx_range = bytes_blk[idx_start:].index(b'\r\n')
                start_of_data_content = bytes_blk[idx_start:idx_start + idx_range]
                start_of_data_str = start_of_data_content.decode('utf-8')

                start_of_data_str = start_of_data_str[len('start of data:'):].lstrip().rstrip('\r')
                start_of_data_int = int(start_of_data_str)
                start_of_data_flag = True

                fr.seek(pos)
                return start_of_data_flag, start_of_data_int
            else:
                seek_point = st_of_data - 1000 if (st_of_data - 1000 >= 0) else 0
                fr.seek(seek_point)
                st_of_data = inc_chunk
        else:
            seek_point = st_of_data - 1000 if (st_of_data - 1000 >= 0) else 0
            fr.seek(seek_point)
            st_of_data = inc_chunk

            if fr.tell() >= max_search_length:
                break

    fr.seek(pos)
    return start_of_data_flag, start_of_data_int


def _has_key_dot_dot(fr, file_header_bytes_size=65000):
    """
    check whether .hdf has a '..' element in header
    Require file open as 'rb' mode, espcailly as binary mode

    Parameters
    ----------
    fr : require that file open as 'rb' mode
    file_header_bytes_size

    Returns
    -------

    """

    dot_dot_line_key = b'ch order:'
    dot_dot_key = b'..'
    dot_dot_flag = False
    dot_dot_bytes = b''

    pos = fr.tell()
    fr.seek(0)
    file_header_bytes_size = int(file_header_bytes_size)

    if file_header_bytes_size <= 0:
        raise ValueError('input parameter is error, need a value bigger than zero')
    if file_header_bytes_size <= 2000:
        file_header_bytes_size = 2000

    pos = fr.tell()
    fr.seek(0)
    bytes_blk = fr.read(file_header_bytes_size)
    if dot_dot_line_key in bytes_blk:
        idx_start = bytes_blk.index(dot_dot_line_key)
        if b'\r\n' in bytes_blk[idx_start:]:
            try:
                idx_range = bytes_blk[idx_start:].index(b'\r\n')
            except:
                print('Not right find the ch order header infomation')
                dot_dot_flag = False

                fr.seek(pos)
                return dot_dot_flag, dot_dot_bytes
            dot_dot_bytes = bytes_blk[idx_start:idx_start + idx_range]
            if dot_dot_key in dot_dot_bytes:
                dot_dot_flag = True

            fr.seek(pos)
            return dot_dot_flag, dot_dot_bytes
        else:
            dot_dot_flag = False
    else:
        dot_dot_flag = False

    fr.seek(pos)
    return dot_dot_flag, dot_dot_bytes


def search_list_element_index_s(ls, element):
    """
    Search the demand element index in list
    Parameters
    ----------
    ls: list
        the list that to be searched
    element

    Returns
    -------
    index_list: list
        the demand element index list,
        if no demand element , return []
    """
    idx_ls = []
    idx_scale = -1
    step = -1

    for _e_ in ls:
        try:
            idx_scale_tmp = ls[step + 1:].index(element)
        except:
            break

        step = step + idx_scale_tmp + 1
        idx_scale = step
        idx_ls.append(idx_scale)

    return idx_ls


def reformat_dot_dot(dot_dot_bytes):
    dot_dot_str = dot_dot_bytes.decode()
    ch_order_ls = dot_dot_str.split(',')
    idx_ls = search_list_element_index_s(ch_order_ls, '..')
    add_con_ls = []
    for idx in idx_ls:
        former = ch_order_ls[idx - 1]
        after = ch_order_ls[idx + 1]
        former_ls = former.split('*')
        after_ls = after.split('*')

        former_chn_seq = former_ls[-1]
        former_mul_factor = former_ls[0] if len(former_ls) == 2 else ''
        after_chn_seq = after_ls[-1]
        after_mul_factor = after_ls[0] if len(after_ls) == 2 else ''
        former_chn_seq = int(former_chn_seq)
        after_chn_seq = int(after_chn_seq)
        ls_tmp_ = list(range(former_chn_seq + 1, after_chn_seq))

        if former_mul_factor == '':
            ls_tmp = [str(x) for x in ls_tmp_]
        else:
            ls_tmp = [former_mul_factor + '*' + str(x) for x in ls_tmp_]

        add_temp = ','.join(ls_tmp)
        add_con_ls.append(add_temp)
    for i, idx in enumerate(idx_ls):
        ch_order_ls[idx] = add_con_ls[i]
    print(add_con_ls)
    print(ch_order_ls)
    chr_order_str = ','.join(ch_order_ls)
    chr_order_byte = chr_order_str.encode()
    new_chn_line = chr_order_byte
    return new_chn_line


def revise_hdf_file_ch_order(hdf_filepath):
    revise_flag = False
    with open(file_path, 'rb') as f:

        start_flag, start_bytes = _has_key_start_of_data(f, 65536)

        if start_flag is True:
            header_length = start_bytes
        else:
            header_length = 65536

        margin_length = 150
        part1_length = header_length - margin_length

        dot_dot_flag, dot_dot_bytes = _has_key_dot_dot(f, part1_length)

    if dot_dot_flag is False:
        return revise_flag

    new_chn_order_byte = reformat_dot_dot(dot_dot_bytes)

    fr = open(hdf_filepath, 'rb')
    fr.read(part1_length)
    fw = open(hdf_filepath[:-4] + '_new.hdf', 'wb')
    if len(new_chn_order_byte) <= part1_length:
        new_chn_order_byte = new_chn_order_byte + b'\t' * (part1_length - len(new_chn_order_byte))
    else:
        new_chn_order_byte = new_chn_order_byte[:part1_length]
        fw.write(new_chn_order_byte)

        # copy the data context from part1_length_end:end
        data_context = fr.read()
        fw.write(data_context)

        fr.close()
        fw.close()
        revise_flag = True
        return revise_flag


if __name__ == '__main__':
    run_code = 5

    if run_code == 1:
        # hdf_file = r'E:\01_SQL\AAAWORK\database\2020-07-23_B89-001 P ohneAC CS_02.hdf'

        hdf_file = r'E:\h5_files\2017-03-31_D65 F4 VZ run02.hdf'
        hdf_file = r'E:/h5_files/2018-08-13_T cross waf 1.4 F3 Mit ac vz10 ( 0.00-11.24 s).1.hdf'
        hdf_file = r'E:/h5_files/2020_test_中文13打飞机0.hdf'
        hdf_file2 = r'E:/h5_files/2017-03-31_D65 F4 VZ run02.hdf'
        hdf_file1 = r'E:/h5_files/2021-03-03_B SUV_BC8-418_(N)G3 VZ_B SUV BC8418 engine absorb acousticground run06.hdf'
        # hdf_file1_TDMS = r'E:/h5_files/2021-03-03_B SUV_BC8-418_(N)G3 VZ_B SUV BC8418 engine absorb acousticground run06.tdms'
        hdf_file2 = r'E:/h5_files/2021-03-03_B SUV_BC8-418_(N)G3 VZ_B SUV BC8418 engine absorb acousticground run06_CAN.hdf'
        hdf_file3 = r'E:\h5_files\bug_source_hdf_data\2021-01-26_Tiguan L_A9R-926_(N)G5 VZ_A9R-926 Aus F4 VZ_202_CAN.hdf'
        print('hdf_file1:', hdf_file1)

        # trans_hdf_2_h5_file
        # _trans_hdf_2_tdms_v3(hdf_file)
        # _trans_hdf_2_tdms_v4(hdf_file,encoding='gbk')
        trans_hdf_2_h5_file(hdf_file1, keep_tdms=True)
        print('*' * 10)
        trans_hdf_2_h5_file(hdf_file2, keep_tdms=True)
        print('*' * 10)
        _trans_hdf_2_tdms_v3(hdf_file3)
        # trans_hdf_2_h5_file(hdf_file3, keep_tdms=True)
        print('*' * 10)
        trans_hdf_2_h5_file(hdf_file1, keep_tdms=True)
        print('*' * 10)

        # trans_hdf_2_tdms(hdf_file1)
        # trans_hdf_2_tdms(hdf_file2)


    elif run_code == 3:

        hdf_file2 = r'E:\h5_files\test2\AE2-410 D 10-100 VZ RUN06_1.0_7.8s.hdf'
        trans_hdf_2_h5_file(hdf_file2, keep_tdms=True)


    elif run_code == 4:
        file_path = r'E:\h5_files\bug_source_hdf_data/2021-01-26_Tiguan L_A9R-926_(N)G5 VZ_A9R-926 Aus F4 VZ_202_CAN.hdf'
        x = revise_hdf_file_ch_order(file_path)


    elif run_code == 5:
        file_path = r'E:\h5_files\bug_source_hdf_data/2021-01-26_Tiguan L_A9R-926_(N)G5 VZ_A9R-926 Aus F4 VZ_202_CAN.hdf'
        # file_path = r'E:/h5_files/2018-08-13_T cross waf 1.4 F3 Mit ac vz10 ( 0.00-11.24 s).1.hdf'
        status = revise_hdf_file_ch_order(file_path)
        print(status)
