# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 21:43:05 2021

@author: Bing Zhao
"""
import os

def list_paths(folder_path , suffix):
    
    # # 获得文件夹下的文件名称
    # filepaths = os.listdir(folder_path)
    
    # #返回包含文件后缀的文件，比如 .tdms
    # # if filepaths[:] [-:-51]==  '.tdms'
    
    # find()   
    # #合并文件夹与文件名
    # for filepath in filepaths:
    
    # print(pathlist)
    pass

    
def get_filenames(folder_path,filetype,subFoder='False'):  
    """
    # 输入路径、文件类型例如'.csv'
    Parameters
    ----------
    folder_path : TYPE
        DESCRIPTION.
    filetype : TYPE
        DESCRIPTION.

    Returns
    -------
    size : num
        符合的文件个数
    path_file_name : list
        带路径文件名
    filename: list
        文件名

    """
    filename = []
    path_file_name=[]
    size=[]

    if filetype[0] != '.':
        filetype = '.'+ filetype
    
    for roots,dirs,files in os.walk(folder_path):
        
        # roots 是输入的folder,dirs 是包含的子文件夹，files是文件名称
        # 每次循环得到的结果
        # item1 root D:\Python\02_City_Road_Analysis\原始文件 dirs ['中文'] files ['test1.hdf', '中文_英文——1223_2 - 副本.hdf']
        # item2 root D:\Python\02_City_Road_Analysis\原始文件\中文 dirs [] files
        # ['test.tdms', 'test.tdms_index', '中文.tdms', '中文_英文——1223_!2.hdf', '中文_英文——1223_2.hdf']

        # if subFolder == Fasle 并且 根路径不等于输入的路径 ,则跳出
        if subFoder=='False' and folder_path != roots:
            break

        # 循环得到文件名，并且将文件路径与文件名拼接，得到一个带路径的列表
        for i in files:
            if os.path.splitext(i)[1]==filetype:
                filename.append(i) # 添加文件名
                pt_fn = roots +'\\'+ i

                path_file_name.append(pt_fn) #添加路径名
    
        
    size = len(filename)    # 得到文件的长度
    
   
    return size, path_file_name, filename            # 输出由有后缀的文件名组成的列表# 输入路径、文件类型例如'.csv'


def use_chinese_path(path):
    try:
        path = os.unicode(path, 'utf-8') # 经过编码处理 
    except:
        pass # python3 已经移除 unicode，而且默认是 utf8 编码，所以不用转
    os.listdir(path)
    return path


 
def mkdir(path):
    
    # 去除首部空格
    path=path.strip()

    # 去除尾部 \ 符号

    path=path.rstrip("\\")
    folder = os.path.exists(path)
    if not folder :                   #判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)             #makedirs 创建文件时如果路径不存在会创建这个路径
        print("new folder Create")
        print("OK ")
    else:
        print("Already Exsit ")
        

#%% main
# if __mian__='main'
# folder="D:"
# num,path,files=get_filenames(folder,'.csv')
# print(files)


if __name__ == '__main__':
    # s=0
    folder_path =r'E:/h5_files'
    folder_path= 'E:/data_selected_02/hdf'

    folder_path = '\\'.join(folder_path.split('/'))
    print('folder_path:', folder_path.encode('gbk'))
    _,file_path_s,_=get_filenames(folder_path,'hdf',subFoder=False)
    s1=file_path_s[10]
    print(s1)