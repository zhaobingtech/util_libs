# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 21:02:50 2021

@author: zhaob
"""

#%%


import matplotlib.pyplot as plt
import numpy as np

from HeadConvertLib import HeadFile # 从自定义文件中导入HeadFile库


# path=b"D:\\test\\Test1.hdf"

# path=b"D:\\test\\test.hdf"
# path=b"D:\\test\\test2.hdf"
# path=b"D:\\test\\test3.hdf"
# path="D:\\test\\test3.hdf"
# path=b"D:\\test\\FAW D090 PV EOLT limit Veh_G36609_RUN3.hdf"
# path="D:\\test\\N012352 CS_02.hdf"

# path='E:\\City Road\\SHANGHAIdaq1\\anting-home1.hdf'


path=r"D:\Python\02_City_Road_Analysis\Raw_Data\中文\中文_英文——1223_!2.hdf"

folderPath= r'D:\10_Python\13_E_Matrix\01_provide_to_bingsoft\2021-07-05'
fileName = r'2021-06-03_A SUVe_AE-702_EKK-hochlauf_20210421 A SUVe AEA-702 EKK-CKD AC line-run03.hdf' # size 426 MB
hdfpath = folderPath + r'//' + fileName

# path.encode('utf-8')
# create HeadFile Object
testfile=HeadFile() 

# open HeadFile data
testfile.open(hdfpath)

# print attribution group and chennels
print('group:',testfile.group)
print('channels:',testfile.channels)

# method 1: read some selected data by object attribution , 
#           last 1000 quantities,some channels
data_slt1 = testfile.read_data(testfile.group,testfile.channels[1:3],-1000)

# method 2: read selected data , with str name
s = testfile.channels[1]
print('channel 1 Name:', s)
data_slt2 = testfile.read_data(testfile.group,s)

# method 3: read all data 
data_slt_all = testfile.read_data(testfile.group,testfile.channels[:])





# # plot some channles data
# i=0
# for chn_data in data_slt_all.data:
#     plt.figure()
#     t=np.arange(0,data_slt_all.increment[i]*(len(chn_data)-1),data_slt_all.increment[i])
#     plt.plot(t,chn_data[0:np.size(t)])
#     plt.title(testfile.channels[i])
#     i=i+1
    
# # close HeadFile Object
# del testfile



#%%
# method 2
# from HeadConvertLib import test
# test()
