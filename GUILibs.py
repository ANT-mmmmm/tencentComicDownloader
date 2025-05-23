
import tkinter as tk
import tkinter.ttk as ttk

class Tabs(ttk.Frame):
    def __init__(self, master=None, show_tab_bar=True, **kwargs):
        super().__init__(master, **kwargs)
        
        # 存储所有的标签页
        self.tabs = []
        # 存储所有的标签按钮
        self.tab_buttons = []
        # 当前选中的标签页索引
        self.current_tab = None
        # 是否显示标签栏
        self.show_tab_bar = show_tab_bar
        
        # 标签栏容器
        self.tab_bar = ttk.Frame(self)
        # 标签页内容容器
        self.tab_container = ttk.Frame(self)
        
        # 将标签栏和标签页内容容器添加到主框架中
        if self.show_tab_bar:
            self.tab_bar.pack(side=tk.TOP, fill=tk.X)
        self.tab_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def add_tab(self, title="New Tab"):
        """
        添加一个新的标签页。
        
        :param title: 标签页的标题
        """
        new_tab = ttk.Frame(self.tab_container)
        new_button = ttk.Button(self.tab_bar, text=title, command=lambda idx=len(self.tabs): self.switch_to_tab(idx))
        
        self.tabs.append(new_tab)
        self.tab_buttons.append(new_button)
        
        # 如果这是第一个标签页，则自动选中它
        if len(self.tabs) == 1:
            self.switch_to_tab(0)
        
        new_button.pack(side=tk.LEFT)
    
    def get_tabs(self) -> list[tk.Frame]:
        """
        获取所有的标签页。
        
        :return: 包含所有标签页的列表
        """
        return self.tabs
    
    def switch_to_tab(self, index: int):
        """
        切换到指定的标签页。
        
        :param index: 要切换到的标签页的索引
        """
        if 0 <= index < len(self.tabs):
            # 隐藏当前标签页
            if self.current_tab is not None:
                self.tabs[self.current_tab].pack_forget()
                self.tab_buttons[self.current_tab].config(style="TButton")
            
            # 显示目标标签页
            self.tabs[index].pack(fill=tk.BOTH, expand=True)
            self.tab_buttons[index].config(style="Selected.TButton")
            
            # 更新当前标签页索引
            self.current_tab = index