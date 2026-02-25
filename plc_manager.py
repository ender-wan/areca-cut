"""
PLC管理器 - 使用Modbus TCP协议与PLC通信
参照back-end工程的实现（使用modbus_tk库）
"""

import threading
import logging
from typing import Optional
from config import PLC_CONFIG

logger = logging.getLogger(__name__)

# 使用modbus_tk库（与back-end保持一致）
try:
    import modbus_tk.defines as cst
    from modbus_tk import modbus_tcp
    MODBUS_TK_AVAILABLE = True
except ImportError:
    MODBUS_TK_AVAILABLE = False
    print("错误: modbus_tk未安装，请运行: pip install modbus-tk")


class PlcManager:
    """
    PLC管理器 - 使用modbus_tk库（与back-end保持一致）
    """
    
    def __init__(self, ip: Optional[str] = None, port: Optional[int] = None):
        """
        初始化PLC管理器
        
        Args:
            ip: PLC IP地址，默认使用配置文件中的值
            port: PLC端口，默认使用配置文件中的值
        """
        self.ip = ip or PLC_CONFIG['ip']
        self.port = port or PLC_CONFIG['port']
        self.unit_id = PLC_CONFIG['unit_id']
        
        self.master: Optional[modbus_tcp.TcpMaster] = None
        self.connected = False
        self.lock = threading.RLock()  # 递归锁，保证线程安全
        
    def connect(self) -> bool:
        """
        连接到PLC（参照back-end/areca/business/camera_trigger.py的实现）
        
        Returns:
            bool: 连接成功返回True，否则返回False
        """
        with self.lock:
            try:
                if not MODBUS_TK_AVAILABLE:
                    logger.error("modbus_tk未安装，请运行: pip install modbus-tk")
                    print("错误: modbus_tk未安装")
                    return False
                
                logger.info(f"正在连接PLC: {self.ip}:{self.port}")
                logger.debug(f"PLC配置: unit_id={self.unit_id}, timeout={PLC_CONFIG['timeout']}")
                
                # 使用modbus_tk连接（与back-end一致）
                self.master = modbus_tcp.TcpMaster(host=self.ip, port=self.port)
                self.master.set_timeout(PLC_CONFIG['timeout'])
                logger.debug("TcpMaster创建成功")
                
                # 测试连接 - 尝试读取一个寄存器
                try:
                    logger.debug("测试Modbus通信...")
                    test_result = self.master.execute(
                        self.unit_id,
                        cst.READ_HOLDING_REGISTERS,
                        0,  # 起始地址
                        1   # 读取数量
                    )
                    logger.info(f"✓ PLC连接成功！测试读取D0={test_result[0]}")
                    self.connected = True
                    return True
                except Exception as e:
                    logger.error(f"❌ Modbus通信测试失败: {type(e).__name__}: {e}")
                    logger.error("请检查：1.PLC IP是否正确 2.Modbus服务是否启用 3.网络是否连通")
                    self.connected = False
                    return False
                    
            except Exception as e:
                logger.error(f"❌ PLC连接异常: {type(e).__name__}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                self.connected = False
                return False
    
    def disconnect(self):
        """断开PLC连接"""
        with self.lock:
            if self.master and self.connected:
                try:
                    self.master.close()
                    self.connected = False
                    print("PLC连接已断开")
                except Exception as e:
                    print(f"PLC断开连接失败: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        with self.lock:
            return self.connected
    
    def read_holding_register(self, address: int) -> Optional[int]:
        """
        读取保持寄存器（参照back-end实现）
        
        Args:
            address: 寄存器地址
            
        Returns:
            int: 寄存器值，失败返回None
        """
        with self.lock:
            if not self.connected:
                logger.error("PLC未连接，无法读取寄存器")
                return None
            
            try:
                # 使用modbus_tk的execute方法
                result = self.master.execute(
                    self.unit_id,
                    cst.READ_HOLDING_REGISTERS,
                    address,
                    1
                )
                value = result[0] if result else None
                logger.debug(f"读取D{address}={value}")
                return value
            except Exception as e:
                logger.error(f"❌ 读取寄存器D{address}失败: {type(e).__name__}: {e}")
                return None
    
    def write_single_register(self, address: int, value: int) -> bool:
        """
        写入单个寄存器（参照back-end实现）
        
        Args:
            address: 寄存器地址
            value: 要写入的值
            
        Returns:
            bool: 成功返回True
        """
        with self.lock:
            if not self.connected:
                logger.error("PLC未连接，无法写入寄存器")
                return False
            
            try:
                # 使用modbus_tk的execute方法（参照back-end/classifiers/classifier.py）
                logger.debug(f"写入D{address}={value}")
                self.master.execute(
                    self.unit_id,
                    cst.WRITE_SINGLE_REGISTER,
                    address,
                    output_value=value
                )
                logger.debug(f"✓ 写入D{address}成功")
                return True
            except Exception as e:
                logger.error(f"❌ 写入寄存器D{address}={value}失败: {type(e).__name__}: {e}")
                return False
    
    def write_holding_register(self, address: int, value: int) -> bool:
        """
        写入保持寄存器（write_single_register的别名，兼容camera_worker调用）
        
        Args:
            address: 寄存器地址
            value: 要写入的值
            
        Returns:
            bool: 成功返回True
        """
        return self.write_single_register(address, value)
    
    def write_multiple_registers(self, address: int, values: list) -> bool:
        """
        写入多个寄存器
        
        Args:
            address: 起始寄存器地址
            values: 要写入的值列表
            
        Returns:
            bool: 成功返回True
        """
        with self.lock:
            if not self.connected:
                logger.error("PLC未连接，无法批量写入")
                return False
            
            try:
                logger.debug(f"批量写入D{address}~D{address+len(values)-1}={values}")
                # 检查值的范围
                for i, val in enumerate(values):
                    if not isinstance(val, int) or val < -32768 or val > 32767:
                        logger.error(f"❌ 寄存器D{address+i}的值{val}超出范围(-32768~32767)")
                        return False
                
                self.master.execute(
                    self.unit_id,
                    cst.WRITE_MULTIPLE_REGISTERS,
                    address,
                    output_value=values
                )
                logger.debug(f"✓ 批量写入D{address}成功")
                return True
            except Exception as e:
                logger.error(f"❌ 批量写入寄存器D{address}失败: {type(e).__name__}: {e}")
                logger.error(f"   尝试写入的值: {values}")
                logger.error(f"   Modbus寄存器限制: -32768 ~ 32767 (有符号16位整数)")
                return False
