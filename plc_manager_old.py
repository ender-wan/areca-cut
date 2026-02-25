"""
PLC Modbus TCP 通讯管理器
PlcManager: 处理Modbus连接和读写，线程安全
"""

import threading
import time
from typing import Optional, List
try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False
    print("Warning: pymodbus not installed. Using MockPlc for testing.")

from config import PLC_CONFIG


class PlcManager:
    """
    PLC管理器 - 线程安全的Modbus TCP客户端
    """
    
    def __init__(self, ip: str = None, port: int = None):
        """
        初始化PLC管理器
        
        Args:
            ip: PLC IP地址，默认使用配置文件中的值
            port: PLC端口，默认使用配置文件中的值
        """
        self.ip = ip or PLC_CONFIG['ip']
        self.port = port or PLC_CONFIG['port']
        self.timeout = PLC_CONFIG['timeout']
        self.unit_id = PLC_CONFIG['unit_id']
        
        self.client: Optional[ModbusTcpClient] = None
        self.connected = False
        self.lock = threading.RLock()  # 递归锁，保证线程安全
        
    def connect(self) -> bool:
        """
        连接到PLC
        
        Returns:
            bool: 连接成功返回True，否则返回False
        """
        with self.lock:
            try:
                if not PYMODBUS_AVAILABLE:
                    print("错误: pymodbus未安装，请运行: pip install pymodbus")
                    return False
                
                print(f"正在连接PLC: {self.ip}:{self.port}, 超时={self.timeout}秒")
                
                self.client = ModbusTcpClient(
                    host=self.ip,
                    port=self.port,
                    timeout=self.timeout
                )
                
                # 尝试连接
                self.connected = self.client.connect()
                
                if not self.connected:
                    print(f"PLC连接失败: 无法建立TCP连接到 {self.ip}:{self.port}")
                    return False
                
                print("TCP连接成功，测试Modbus通信...")
                
                # 测试Modbus通信（读取一个寄存器）
                # pymodbus版本兼容性：不同版本参数名不同
                test_result = None
                try:
                    # 尝试pymodbus 2.x/早期3.x版本的API
                    test_result = self.client.read_holding_registers(
                        address=0,
                        count=1,
                        unit=self.unit_id
                    )
                except TypeError as e:
                    if 'slave' in str(e) or 'unit' in str(e):
                        # 参数名错误，尝试其他API
                        try:
                            # 尝试不带unit/slave参数
                            test_result = self.client.read_holding_registers(0, 1)
                        except Exception as e2:
                            print(f"Modbus API不兼容: {e2}")
                            self.client.close()
                            self.connected = False
                            return False
                    else:
                        raise
                
                # 检查结果
                if test_result and hasattr(test_result, 'isError') and test_result.isError():
                    print(f"Modbus通信测试失败: {test_result}")
                    self.client.close()
                    self.connected = False
                    return False
                
                print("Modbus通信测试成功")
                return True
                    
            except Exception as e:
                print(f"PLC连接异常: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                self.connected = False
                return False
    
    def disconnect(self):
        """断开PLC连接"""
        with self.lock:
            if self.client and self.connected:
                try:
                    if PYMODBUS_AVAILABLE:
                        self.client.close()
                    self.connected = False
                except Exception as e:
                    print(f"PLC断开连接失败: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        with self.lock:
            return self.connected
    
    def read_holding_register(self, address: int) -> Optional[int]:
        """
        读取保持寄存器 (对应三菱PLC的D寄存器)
        
        Args:
            address: 寄存器地址 (例如: 100表示D100)
            
        Returns:
            int: 寄存器值，失败返回None
        """
        with self.lock:
            if not self.connected:
                print(f"PLC未连接，无法读取寄存器 D{address}")
                return None
            
            try:
                if self.using_mock:
                    # 使用Mock实现
                    return self.client.read_holding_register(address)
                elif PYMODBUS_AVAILABLE:
                    response = self.client.read_holding_registers(
                        address=address,
                        count=1,
                        unit=self.unit_id
                    )
                    if not response.isError():
                        return response.registers[0]
                    else:
                        print(f"读取寄存器 D{address} 失败: {response}")
                        return None
                else:
                    # Mock实现
                    return self.client.read_holding_register(address)
                    
            except Exception as e:
                print(f"读取寄存器 D{address} 异常: {e}")
                return None
    
    def write_holding_register(self, address: int, value: int) -> bool:
        """
        写入保持寄存器 (对应三菱PLC的D寄存器)
        
        Args:
            address: 寄存器地址
            value: 要写入的值
            
        Returns:
            bool: 写入成功返回True
        """
        with self.lock:
            if not self.connected:
                print(f"PLC未连接，无法写入寄存器 D{address}")
                return False
            
            try:
                if self.using_mock:
                    # 使用Mock实现
                    return self.client.write_holding_register(address, value)
                elif PYMODBUS_AVAILABLE:
                    response = self.client.write_register(
                        address=address,
                        value=value,
                        unit=self.unit_id
                    )
                    if not response.isError():
                        return True
                    else:
                        print(f"写入寄存器 D{address} 失败: {response}")
                        return False
                else:
                    # Mock实现
                    return self.client.write_holding_register(address, value)
                    
            except Exception as e:
                print(f"写入寄存器 D{address} 异常: {e}")
                return False
    
    def write_multiple_registers(self, address: int, values: List[int]) -> bool:
        """
        写入多个连续的保持寄存器
        
        Args:
            address: 起始寄存器地址
            values: 要写入的值列表
            
        Returns:
            bool: 写入成功返回True
        """
        with self.lock:
            if not self.connected:
                print(f"PLC未连接，无法写入多个寄存器")
                return False
            
            try:
                if self.using_mock:
                    # 使用Mock实现
                    return self.client.write_multiple_registers(address, values)
                elif PYMODBUS_AVAILABLE:
                    response = self.client.write_registers(
                        address=address,
                        values=values,
                        unit=self.unit_id
                    )
                    if not response.isError():
                        return True
                    else:
                        print(f"写入多个寄存器失败: {response}")
                        return False
                else:
                    # Mock实现
                    return self.client.write_multiple_registers(address, values)
                    
            except Exception as e:
                print(f"写入多个寄存器异常: {e}")
                return False
