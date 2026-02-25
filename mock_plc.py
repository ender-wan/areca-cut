"""
Mock PLC 模拟类
用于在无实际PLC硬件的情况下测试系统
"""

import threading
import time
from typing import Dict


class MockPlc:
    """
    模拟PLC - 用于测试
    
    替换位置: plc_manager.py 中当 pymodbus 不可用时使用
    """
    
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.registers: Dict[int, int] = {}  # 模拟寄存器表
        self.lock = threading.RLock()
        
        # 初始化所有寄存器为0
        for addr in range(100, 200):
            self.registers[addr] = 0
        
        # 启动自动触发线程（模拟PLC发送触发信号）
        self.auto_trigger_enabled = True
        self.trigger_thread = threading.Thread(target=self._auto_trigger_worker, daemon=True)
        self.trigger_thread.start()
    
    def connect(self) -> bool:
        """模拟连接"""
        print(f"MockPlc: 连接到 {self.ip}:{self.port} (模拟)")
        return True
    
    def close(self):
        """模拟关闭连接"""
        self.auto_trigger_enabled = False
        print("MockPlc: 断开连接 (模拟)")
    
    def read_holding_register(self, address: int) -> int:
        """读取寄存器"""
        with self.lock:
            value = self.registers.get(address, 0)
            # print(f"MockPlc: 读取 D{address} = {value}")
            return value
    
    def write_holding_register(self, address: int, value: int) -> bool:
        """写入寄存器"""
        with self.lock:
            self.registers[address] = value
            print(f"MockPlc: 写入 D{address} = {value}")
            return True
    
    def write_multiple_registers(self, address: int, values: list) -> bool:
        """写入多个寄存器"""
        with self.lock:
            for i, value in enumerate(values):
                self.registers[address + i] = value
            print(f"MockPlc: 批量写入 D{address}~D{address + len(values) - 1} = {values}")
            return True
    
    def _auto_trigger_worker(self):
        """
        自动触发工作线程
        每隔5-10秒随机向一个相机的触发寄存器写入10
        模拟真实PLC的行为：检测到128（图片就绪）后自动重置为0
        """
        import random
        
        trigger_addresses = [100, 110, 120, 130, 140, 150, 160, 170]  # 8个相机的触发寄存器
        
        while self.auto_trigger_enabled:
            # 首先检查所有触发寄存器，如果是128则重置为0（模拟PLC收到完成信号）
            with self.lock:
                for addr in trigger_addresses:
                    if self.registers.get(addr, 0) == 128:
                        self.registers[addr] = 0
                        # print(f"MockPlc: 自动重置 D{addr} = 0 (收到完成信号)")
            
            time.sleep(random.uniform(2, 5))  # 随机间隔
            
            # 随机选择一个相机触发
            addr = random.choice(trigger_addresses)
            
            with self.lock:
                # 只在寄存器为0时触发（避免重复触发）
                if self.registers.get(addr, 0) == 0:
                    self.registers[addr] = 10  # 写入触发信号
                    print(f"\n>>> MockPlc: 自动触发 D{addr} = 10 <<<\n")
