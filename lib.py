import time
import logging
import os
import zipfile
from datetime import datetime, timedelta
from typing import Optional
import glob
import re
def dateToTimestamp(date_str):
    return int(time.mktime(time.strptime(date_str, "%Y-%m-%d")))

# log_system.py
class LogSystem:
    """
    增强版日志系统（带自动归档功能）
    
    新增功能：
    1. 自动将前一天的日志文件压缩归档
    2. 可设置保留最近N天的日志文件
    3. 自动清理过期的归档文件
    
    使用方法保持不变：
    from log_system import LogSystem
    
    logger = LogSystem(
        debug_mode=True,
        log_dir='log',
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        keep_days=7  # 新增参数：保留最近7天的日志
    )
    """

    def __init__(
        self,
        debug_mode: bool = True,
        log_dir: str = 'log',
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        keep_days: int = 7
    ):
        """
        初始化日志系统
        
        :param debug_mode: 是否调试模式
        :param log_dir: 日志存放目录
        :param console_level: 控制台日志级别
        :param file_level: 文件日志级别
        :param keep_days: 保留最近几天的日志（默认7天）
        """
        self.DEBUG = debug_mode
        self.LOG_DIR = log_dir
        self.LOG_CONSOLE_LEVEL = console_level
        self.LOG_FILE_LEVEL = file_level
        self.KEEP_DAYS = keep_days
        
        # 初始化时自动清理和归档旧日志
        self._archive_old_logs()
        self._setup_logging()

    def _archive_old_logs(self):
        """归档所有今天之前的日志文件（增强版）"""
        try:
            if not os.path.exists(self.LOG_DIR):
                if self.DEBUG:
                    logging.debug(f"日志目录不存在: {self.LOG_DIR}")
                return

            today = datetime.now().strftime('%Y-%m-%d')
            if self.DEBUG:
                logging.debug(f"开始归档日志，今天日期: {today}")

            # 获取所有.log文件
            all_logs = glob.glob(os.path.join(self.LOG_DIR, '*.log'))
            if self.DEBUG:
                logging.debug(f"找到{len(all_logs)}个日志文件")

            # 筛选今天之前的日志
            old_logs = [
                f for f in all_logs 
                if not os.path.basename(f).startswith(today)
            ]
            
            if not old_logs:
                if self.DEBUG:
                    logging.debug("没有需要归档的旧日志")
                return

            if self.DEBUG:
                logging.debug(f"找到{len(old_logs)}个需要归档的旧日志")

            # 创建归档目录
            archive_dir = os.path.join(self.LOG_DIR, 'archives')
            try:
                os.makedirs(archive_dir, exist_ok=True)
                if self.DEBUG:
                    logging.debug(f"创建归档目录: {archive_dir}")
            except Exception as e:
                logging.error(f"创建归档目录失败: {str(e)}")
                return

            # 按日期分组
            date_groups = {}
            for log_file in old_logs:
                try:
                    filename = os.path.basename(log_file)
                    date_part = filename.split('_')[0]
                    if date_part not in date_groups:
                        date_groups[date_part] = []
                    date_groups[date_part].append(log_file)
                except Exception as e:
                    logging.error(f"处理日志文件{log_file}出错: {str(e)}")
                    continue

            # 打包每个日期的日志
            for date, logs in date_groups.items():
                zip_path = os.path.join(archive_dir, f'logs_{date}.zip')
                if self.DEBUG:
                    logging.debug(f"正在创建归档: {zip_path}")
                
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for log_file in logs:
                            zipf.write(log_file, os.path.basename(log_file))
                            if self.DEBUG:
                                logging.debug(f"添加文件到归档: {log_file}")
                    
                    # 验证ZIP文件是否创建成功
                    if not os.path.exists(zip_path):
                        logging.error(f"归档文件创建失败: {zip_path}")
                        continue
                    
                    # 删除原日志文件
                    for log_file in logs:
                        try:
                            os.remove(log_file)
                            if self.DEBUG:
                                logging.debug(f"已删除原文件: {log_file}")
                        except Exception as e:
                            logging.error(f"删除文件{log_file}失败: {str(e)}")
                            
                except Exception as e:
                    logging.error(f"创建归档{zip_path}失败: {str(e)}")
                    continue

            # 清理旧归档
            #self._clean_expired_archives()

        except Exception as e:
            logging.error(f"日志归档过程中发生未捕获的异常: {str(e)}")

    def _setup_logging(self):
        """配置日志系统 (与原代码逻辑一致)"""
        # 创建日志目录
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)
        
        # 生成日志文件名(按日期和序号)
        today = datetime.now().strftime('%Y-%m-%d')
        existing_logs = [f for f in os.listdir(self.LOG_DIR) 
                        if f.startswith(today) and f.endswith('.log')]
        log_file = os.path.join(self.LOG_DIR, f'{today}_{len(existing_logs)+1}.log')
        
        # 清除现有日志处理器
        logger = logging.getLogger()
        logger.handlers.clear()
        
        # 设置日志格式
        formatter = logging.Formatter(
            '[%(asctime)s][%(threadName)s][%(funcName)s][%(levelname)s] %(message)s',
            datefmt=r'%Y-%m-%d %H:%M:%S'
        )
        
        # 自定义时间格式化函数以支持毫秒
        def custom_time_format(record, datefmt):
            created = datetime.fromtimestamp(record.created)
            # 将毫秒部分拼接到格式化后的时间字符串中
            base_time_str = created.strftime(datefmt)
            millisecond = created.microsecond // 1000  # 微秒转毫秒
            return f"{base_time_str}.{millisecond:03d}"
        
        formatter.formatTime = custom_time_format
        
        # 配置文件处理器(UTF-8编码)
        file_handler = logging.FileHandler(log_file, mode='w+', encoding='utf-8')
        file_handler.setLevel(self.LOG_FILE_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 配置控制台处理器
        if self.LOG_CONSOLE_LEVEL:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.LOG_CONSOLE_LEVEL)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 设置根记录器级别
        logger.setLevel(logging.DEBUG)

        # 调试模式额外输出
        if self.DEBUG:
            logging.debug(f"日志系统初始化完成")
            logging.debug(f"日志文件: {log_file}")
            logging.debug(f"控制台级别: {self.LOG_CONSOLE_LEVEL}")
            logging.debug(f"文件记录级别: {self.LOG_FILE_LEVEL}")
            logging.debug(f"日志保留天数: {self.KEEP_DAYS}天")

def clean_text(text):
    """
    删除文本中符合以下模式的字符组合：
    多个空格+换行+(空格+换行)*n(n>=0)+空格
    
    参数:
        text (str): 需要清理的原始文本
        
    返回:
        str: 清理后的文本
    """
    # 匹配模式：多个空格+换行+(空格+换行)*n+空格
    pattern = r'[ ]+\n(?:[ ]*\n)*[ ]*'
    # 替换为单个换行
    cleaned = re.sub(pattern, '\n', text)
    # 确保最后没有多余空格
    return cleaned.strip()

import re

#
def minimize_html_whitespace(html):
    # 合并连续空白为一个空格，并去除首尾空白
    html = re.sub(r'[\s\t\n\r]+', ' ', html)
    return html.strip()
import re
from typing import Optional


class HTMLParser:
    def __init__(self, outerHTML: str):
        self.outerHTML = outerHTML  # 假设minimize_html_whitespace已处理

    def find_elements_by_class_name(self, class_name: str) -> list['HTMLParser']:
        """
        通过class名查找所有匹配元素并返回由HTMLParser对象构成的列表
        """
        results = []

        # 改进后的正则表达式，支持自闭合和普通标签，捕获整个标签
        pattern = r'<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*?class="[^"]*\b' + re.escape(class_name) + r'\b[^"]*"[^>]*)\s*(/?)>'

        for match in re.finditer(pattern, self.outerHTML):
            tag_name = match.group(1)
            attr_text = match.group(2)
            is_self_closing = match.group(3) == '/'

            start_pos = match.start()

            if is_self_closing:
                # 自闭合标签
                full_html = self.outerHTML[start_pos:match.end()]
                results.append(HTMLParser(full_html))
            else:
                # 普通标签，匹配整个块（支持嵌套）
                depth = 1
                pos = match.end()
                while depth > 0 and pos < len(self.outerHTML):
                    next_open = re.search(rf'<{tag_name}\b[^>]*?(?<!/)>', self.outerHTML[pos:])
                    next_close = re.search(rf'</{tag_name}>', self.outerHTML[pos:])

                    if next_open and (not next_close or next_open.start() < next_close.start()):
                        depth += 1
                        pos += next_open.end()
                    elif next_close:
                        depth -= 1
                        pos += next_close.end()
                    else:
                        break

                full_html = self.outerHTML[start_pos:pos]
                results.append(HTMLParser(full_html))

        return results

    def find_element_by_class_name(self, class_name: str):
        """
        通过class名查找第一个匹配元素
        """
        pattern = r'<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*?class="[^"]*\b' + re.escape(class_name) + r'\b[^"]*"[^>]*)\s*(/?)>'

        match = re.search(pattern, self.outerHTML)
        if not match:
            return None

        tag_name = match.group(1)
        is_self_closing = match.group(3) == '/'
        start_pos = match.start()

        if is_self_closing:
            return HTMLParser(match.group(0))

        # 普通标签处理（嵌套结构）
        depth = 1
        pos = match.end()
        while depth > 0 and pos < len(self.outerHTML):
            next_open = re.search(rf'<{tag_name}\b[^>]*?(?<!/)>', self.outerHTML[pos:])
            next_close = re.search(rf'</{tag_name}>', self.outerHTML[pos:])

            if next_open and (not next_close or next_open.start() < next_close.start()):
                depth += 1
                pos += next_open.end()
            elif next_close:
                depth -= 1
                pos += next_close.end()
            else:
                break

        return HTMLParser(self.outerHTML[start_pos:pos])

    def get_attribute(self, attr_name: str) -> Optional[str]:
        """
        获取指定属性的值
        """
        if attr_name == 'outerHTML':
            return self.outerHTML

        if attr_name == 'innerHTML':
            start_tag_end = self.outerHTML.find('>') + 1
            end_tag_start = self.outerHTML.rfind('<')
            if start_tag_end == -1 or end_tag_start == -1 or start_tag_end >= end_tag_start:
                return ""
            return self.outerHTML[start_tag_end:end_tag_start]

        if attr_name == 'innerText':
            inner_html = self.get_attribute('innerHTML')
            text = re.sub(r'<[^>]*>', '', inner_html)
            text = clean_text(text)
            return text

        pattern = rf'{attr_name}="([^"]*?)"'
        match = re.search(pattern, self.outerHTML)
        if match:
            return match.group(1)
        return None
    
def findString(main_string: str, start_string: str, end_string: str,start_move=0,end_move=0) -> list[str]:
    output = {}
    current_pos = 0  # 记录当前搜索位置，避免修改原字符串
    
    while True:
        try:
            # 查找起始字符串的位置（从 current_pos 开始）
            start_place = main_string.index(start_string, current_pos)
            
            # 查找结束字符串的位置（从 start_place 开始）
            end_place = main_string.index(end_string, start_place + len(start_string))
            
            # 提取匹配的子串（包含 start_string 和 end_string）
            matched_str = main_string[start_place+start_move : end_place + len(end_string)+end_move]
            output.update({matched_str:(start_place , end_place + len(end_string))})
            
            # 更新 current_pos 到当前匹配的结束位置，继续搜索
            current_pos = end_place + len(end_string)
            
        except ValueError:  # 如果找不到 start_string 或 end_string，退出循环
            break
    
    return list(output.keys())

def split_list_with_index(lst: list, n: int) -> list[list[dict]]:
    
    """
    将一个列表平均分割成 n 个子列表，并返回一个包含这些子列表的列表。

    参数：
    - lst: 要分割的列表。
    - n: 要分割的子列表数量。

    返回：
    - 一个包含 n 个子列表的列表。每个子列表是一个字典，键是列表中的元素，值是元素在原始列表中的索引。
    """

    if n <= 0:
        raise ValueError("n must be positive")
    
    length = len(lst)
    chunk_size, remainder = divmod(length, n)
    
    result = []
    start = 0
    
    for i in range(n):
        end = start + chunk_size + (1 if i < remainder else 0)
        if start >= length:
            result.append([{}])  # 空字典（如果没有元素）
        else:
            # 将当前分片的元素转为 {value: index} 字典
            chunk = lst[start:end]
            chunk_dict = {val: idx for idx, val in enumerate(lst) if val in chunk}
            result.append([chunk_dict])  # 用列表包裹字典（符合你的需求）
        start = end
    
    return result


import threading
import threading
import time
import queue
from typing import Optional, Callable

class DynamicThread:
    def __init__(self, refresh_time=10,auto_back=False,source_queue: queue.Queue=None):
        '''创建一个动态线程'''
        self.refresh_time: int = refresh_time  # 修复类型声明
        self.current_running: bool = False
        self.current_func: Optional[Callable] = None  # 使用类型注解
        self.stop_: bool = False
        self.queue=queue.Queue()
        self.auto_back=auto_back
        self.source_queue=source_queue

        # 创建线程
        self.thread = threading.Thread(target=self.main)
        self.thread.start()  # 启动线程

    def main(self):
        while True:
            self.current_running = False
            time.sleep(self.refresh_time / 1000)  # 等待指定时间
            if self.queue.qsize() > 0:
                self.current_func = self.queue.get()
                self.current_running = True
                self.current_func()
                self.current_func=None
            if self.stop_:
                break  # 如果设置了停止标志，退出循环
            
        if self.auto_back:
            self.source_queue.put(self)

    def add(self, func: Callable):
        '''设置要运行的函数'''
        self.queue.put(func)

    def stop(self):
        '''停止线程'''
        self.stop_ = True

    def get_thread(self) -> threading.Thread:
        '''获取线程对象'''
        return self.thread

