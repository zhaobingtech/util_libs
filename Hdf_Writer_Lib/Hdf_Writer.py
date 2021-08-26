# -*- coding: utf-8 -*-
"""
    Python Module for write the data to a Head acoustic HDF Data Format
    
    This module contains:
        the Class
            - Hdf_Writer : 
                -- method:  
                        init_()
                        Generator()
                -- member:  
                        RootObj
                        GrpObj
                        ChnObj
            - RootObj
            - GrpObj
            - ChnObj
                    
            
Created on Thu May 27 14:44:57 2021

@author: ZhaoBing
"""

from nptdms import RootObject, TdmsWriter, ChannelObject, GroupObject
import numpy as np
import sys
import clr
import os


class Hdf_Writer:

    def __init__(self, path=''):
        self.path = path
        self.RootObjects = []
        self.RootGroups = []
        self.Channels = []

    def Generator(self, KeepTdms=False):
        # 1. build the tdms file

        tdms_Path = self.path[:-4]+'.tdms'
        with TdmsWriter(tdms_Path) as generated_file:
            generated_file.write_segment(
                self.RootObjects + self.RootGroups + self.Channels)

        # --- 2. translate to hdf file
        
        #    --- 2.1 导入 .net dll

        # use for give the dll path , especailly not in the same folder
        current_file_folder = os.path.dirname(__file__)
        sys.path.append(current_file_folder)  # soft code , current folder

        clr.AddReference('tdms2hdf2')
        import tdms2hdf2 as tdms2hdf2  # 导入命名空间
        save2hdf = tdms2hdf2.LabVIEWExports.tdms2hdf3

        clr.AddReference('NationalInstruments.LabVIEW.Interop')

        #   --- 2.2 tdms2hdf
        import NationalInstruments.LabVIEW.Interop as lv
        path = lv.LVPath(tdms_Path)
        err_str = lv.ErrorCluster(False, 0, '')

        try:
            save2hdf(path, err_str)
        except lv.VIAssemblyException as e:
            err_str.Status = True
            err_str.Source = e.ErrorSource
            err_str.Code = e.ErrorCode

        # remove the .tdms file if needed
        if KeepTdms == False:
            os.remove(tdms_Path)
            tdms_index_Path = tdms_Path + '_index'
            os.remove(tdms_index_Path)

        # return err_status
        return err_str


class RootObj(RootObject):
    pass


class GrpObj(GroupObject):
    pass


class ChnObj(ChannelObject):
    pass


if __name__ == '__main__':

    grp_name = 'ddd'  # grp name struture needs,not too much reality meanings
    root = RootObj({'path': '112s', 'new': 3})
    grups = GrpObj(grp_name)
    channel_1 = ChnObj(grp_name, 'VL', np.array(
        [1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1]), properties={'wf_increment': 0.5})
    channel_2 = ChnObj(grp_name, 'VR', np.array(
        [7, 5, 3, 1, 0, 3, 5, 7, 5, 3, 1, 3, 1]), properties={'wf_increment': 1})

    # channel_3 = ChnObj('Unname','VR',np.array([7,5,3,1,0,3,5,7,5,3,1,3,5]), properties = { 'wf_increment' : 1} ) # 不能同时写重复名称的两个不同通道
    hdf_writer = Hdf_Writer()
    path_pre = os.path.dirname(__file__)
    print(path_pre)
    hdf_writer.path = path_pre + r'/dddd5.hdf'
    hdf_writer.RootObjects = [root]  # build root obj
    hdf_writer.RootGroups = [grups]  # build group obj
    hdf_writer.Channels = [channel_1, channel_2]  # build channels obj

    # 生成 hdf 文件
    err_str = hdf_writer.Generator()  # generate the hdf data

    # err_str = hdf_writer.Generator(KeepTdms=True) # generate the hdf data , and generate the tmds file at the same time.

    # del hdf_writer
    print('err_status:', err_str.Status)
    if err_str.Status:
        print('err_Source:', err_str.Source)
        print('err_Code:', err_str.Code)
