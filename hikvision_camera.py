"""
海康工业相机真实连接类
HikvisionCamera: 基于海康SDK的相机控制
"""

import sys
import time
import logging
import threading
import numpy as np
import cv2
import random
from ctypes import *
from typing import Optional

# 尝试导入海康SDK
try:
    from MvImport.MvCameraControl_class import *
    HIKVISION_SDK_AVAILABLE = True
    print("✓ 海康SDK加载成功")
except (ImportError, NameError, OSError) as e:
    HIKVISION_SDK_AVAILABLE = False
    print(f"✗ 海康SDK加载失败: {e}")

# 获取logger（确保已经过setup_logger配置）
logger = logging.getLogger('BetelNutVision.hikvision_camera')


class HikvisionCamera:
    """
    海康工业相机控制类
    
    使用方法：
    1. 创建实例: camera = HikvisionCamera(camera_ip)
    2. 连接相机: camera.connect()
    3. 拍照: image = camera.capture()
    4. 断开连接: camera.disconnect()
    """
    
    def __init__(self, camera_ip: str):
        """
        初始化相机
        
        Args:
            camera_ip: 相机IP地址
        """
        self.camera_ip = camera_ip
        self.cam = None
        self.connected = False
        self.device_info = None
        
        if HIKVISION_SDK_AVAILABLE:
            self.cam = MvCamera()
        
    def connect(self) -> bool:
        """
        连接相机
        
        Returns:
            bool: 连接成功返回True
        """
        print(f"[DEBUG] HikvisionCamera.connect() 被调用 - IP: {self.camera_ip}")
        logger.info("="*60)
        logger.info(f"开始连接海康相机: {self.camera_ip}")
        logger.info("="*60)
        
        if not HIKVISION_SDK_AVAILABLE:
            logger.error(f"海康SDK未加载，无法连接相机 {self.camera_ip}")
            print(f"[DEBUG] SDK不可用，HIKVISION_SDK_AVAILABLE={HIKVISION_SDK_AVAILABLE}")
            return False
        
        try:
            logger.info(f"1/7 枚举网络设备...")
            
            device_list = MV_CC_DEVICE_INFO_LIST()
            tlayer_type = MV_GIGE_DEVICE
            
            ret = MvCamera.MV_CC_EnumDevices(tlayer_type, device_list)
            if ret != 0:
                logger.error(f'❌ 枚举设备失败 ret[0x{ret:x}]')
                logger.error(f'   请检查：1.是否安装海康SDK 2.网卡是否正常')
                return False
            
            logger.info(f'✓ 发现 {device_list.nDeviceNum} 个网络设备')
            if device_list.nDeviceNum == 0:
                logger.error('❌ 未发现任何相机')
                logger.error('   请检查：1.相机电源 2.网线连接 3.网卡IP配置')
                return False
            
            # 2. 查找匹配IP的相机
            logger.info(f"2/7 查找目标IP: {self.camera_ip}")
            found_ips = []
            for i in range(device_list.nDeviceNum):
                mvcc_dev_info = cast(
                    device_list.pDeviceInfo[i], 
                    POINTER(MV_CC_DEVICE_INFO)
                ).contents
                
                if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                    nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                    nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                    nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                    nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                    current_ip = f"{nip1}.{nip2}.{nip3}.{nip4}"
                    found_ips.append(current_ip)
                    logger.info(f"  设备 {i+1}: IP={current_ip}")
                    
                    if current_ip == self.camera_ip:
                        self.device_info = device_list.pDeviceInfo[i]
                        logger.info(f"找到匹配的相机: {current_ip}")
                        break
            
            if self.device_info is None:
                logger.error(f'未找到IP为 {self.camera_ip} 的相机')
                logger.error(f'发现的相机IP: {", ".join(found_ips)}')
                logger.error(f'请检查config.py中的相机IP配置是否正确')
                return False
            
            # 3. 创建句柄
            logger.debug("创建设备句柄...")
            stDeviceList = cast(self.device_info, POINTER(MV_CC_DEVICE_INFO)).contents
            ret = self.cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                logger.error(f'创建句柄失败 ret[0x{ret:x}]')
                return False
            
            # 4. 打开设备
            logger.debug("打开设备...")
            ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                logger.error(f'打开设备 {self.camera_ip} 失败 ret[0x{ret:x}]')
                logger.error(f'可能原因：1.相机已被其他程序占用 2.相机断电或网络故障')
                self.cam.MV_CC_DestroyHandle()
                return False
            
            # 5. 设置网络最佳包大小
            logger.debug("设置网络参数...")
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        logger.warning(f'设置包大小失败 ret[0x{ret:x}]')
            
            # 6. 设置触发模式为软触发
            logger.debug("设置触发模式...")
            ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)
            if ret != 0:
                logger.error(f'设置触发模式失败 ret[0x{ret:x}]')
                self.disconnect()
                return False
            
            ret = self.cam.MV_CC_SetEnumValue("TriggerSource", MV_TRIGGER_SOURCE_SOFTWARE)
            if ret != 0:
                logger.error(f'设置触发源失败 ret[0x{ret:x}]')
                self.disconnect()
                return False
            
            # 7. 开始取流
            logger.debug("开始取流...")
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                logger.error(f'开始取流失败 ret[0x{ret:x}]')
                self.disconnect()
                return False
            
            self.connected = True
            logger.info(f'✓ 相机 {self.camera_ip} 连接成功')
            return True
            
        except Exception as e:
            logger.error(f'Connect camera {self.camera_ip} exception: {e}')
            return False
    
    def disconnect(self):
        """断开相机连接"""
        if not self.connected or not HIKVISION_SDK_AVAILABLE:
            return
        
        try:
            self.cam.MV_CC_StopGrabbing()
            self.cam.MV_CC_CloseDevice()
            self.cam.MV_CC_DestroyHandle()
            self.connected = False
            logger.info(f'Camera {self.camera_ip} disconnected')
        except Exception as e:
            logger.error(f'Disconnect camera {self.camera_ip} exception: {e}')
    
    def capture(self) -> Optional[np.ndarray]:
        """
        拍照获取图像
        
        Returns:
            np.ndarray: BGR格式图像，失败返回None
        """
        if not self.connected or not HIKVISION_SDK_AVAILABLE:
            logger.error(f'Camera {self.camera_ip} not connected')
            return None
        
        try:
            # 1. 发送软触发命令
            ret = self.cam.MV_CC_SetCommandValue("TriggerSoftware")
            if ret != 0:
                logger.error(f'Trigger software failed. ret[0x{ret:x}]')
                return None
            
            # 2. 获取payload大小
            stParam = MVCC_INTVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
            ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != 0:
                logger.error(f'Get payload size failed. ret[0x{ret:x}]')
                return None
            
            nDataSize = stParam.nCurValue
            pData = (c_ubyte * nDataSize)()
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            
            # 3. 获取一帧图像
            ret = self.cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 2000)
            if ret == 0:
                logger.info(f'Camera {self.camera_ip}: Get frame Width[{stFrameInfo.nWidth}], Height[{stFrameInfo.nHeight}]')
                
                # 4. 转换为numpy数组
                image = np.asarray(pData)
                image = image.reshape(stFrameInfo.nHeight, stFrameInfo.nWidth, -1)
                
                # 5. 颜色空间转换（根据相机配置调整）
                # 如果是BayerRG8格式
                # image = cv2.cvtColor(image, cv2.COLOR_BayerRG2RGB)
                # 如果是RGB8格式
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                return image
            else:
                logger.error(f'Get one frame timeout. ret[0x{ret:x}]')
                return None
                
        except Exception as e:
            logger.error(f'Capture image from {self.camera_ip} exception: {e}')
            return None


class ImageFolderCamera:
    """
    从test_img文件夹读取图片的测试相机
    用于在无真实相机时进行测试
    """
    
    def __init__(self, camera_ip: str, test_img_folder: str = "test_img"):
        """
        初始化图片测试相机
        
        Args:
            camera_ip: 相机IP（用于区分不同相机）
            test_img_folder: 测试图片文件夹路径
        """
        self.camera_ip = camera_ip
        self.test_img_folder = test_img_folder
        self.connected = False
        self.image_files = []
        self.current_index = 0
        
    def connect(self) -> bool:
        """
        连接（加载图片列表）
        
        Returns:
            bool: 成功返回True
        """
        import os
        import glob
        
        if not os.path.exists(self.test_img_folder):
            logger.error(f'Test image folder {self.test_img_folder} not found')
            return False
        
        # 加载所有图片文件
        patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        for pattern in patterns:
            self.image_files.extend(
                glob.glob(os.path.join(self.test_img_folder, pattern))
            )
        
        if len(self.image_files) == 0:
            logger.error(f'No images found in {self.test_img_folder}')
            return False
        
        self.image_files.sort()
        self.connected = True
        logger.info(f'ImageFolderCamera {self.camera_ip}: Loaded {len(self.image_files)} images')
        return True
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info(f'ImageFolderCamera {self.camera_ip} disconnected')
    
    def capture(self) -> Optional[np.ndarray]:
        """随机读取一张图片"""
        if not self.connected:
            logger.error(f'ImageFolderCamera {self.camera_ip} not connected')
            return None
        
        if len(self.image_files) == 0:
            return None
        
        # 随机选择图片
        image_path = random.choice(self.image_files)
        
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f'Failed to read image: {image_path}')
            return None
        
        logger.info(f'ImageFolderCamera {self.camera_ip}: Read {image_path}')
        return image
