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
        new_button = ttk.Button(
            self.tab_bar,
            text=title,
            command=lambda idx=len(self.tabs): self.switch_to_tab(idx),
        )

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


class Settings(ttk.LabelFrame):
    def __init__(self, master=None, **kwargs):
        """
        初始化 Settings 容器框架。

        :param master: 父级控件
        """
        super().__init__(master, **kwargs)
        # 创建一个内部容器框架，用于承载所有设置项
        self.root_frame = self
        self.bg='red'
        
        self.data={}

    def add_setting(self, label_text, data_type: str, limit=0) -> None:
        """
        添加一个设置项，支持 bool、str、int 三种类型。

        :param label_text: 设置项的标签文本
        :param data_type: 数据类型 ('bool', 'str', 'int')
        :param limit: 可选参数，暂未使用
        """
        # 获取当前行号，用于放置新设置项
        self.start_row = self.root_frame.grid_size()[1] + 1
        
        self.limit = limit

        # 创建标签控件，靠左对齐
        label = ttk.Label(self.root_frame, text=label_text, anchor="w")
        label.grid(row=self.start_row, column=0, sticky="w",pady=5, padx=5)

        # 创建提示值标签，用于显示 int 类型的当前值
        num_label = ttk.Label(self.root_frame, text="0", anchor="e")

        # 根据数据类型创建不同的控件
        if data_type == "bool":
            widget = ttk.Checkbutton(self.root_frame)
        elif data_type == "str":
            widget = ttk.Entry(self.root_frame, width=10)
        elif data_type == "int":
            # 创建滑动条，并绑定数值变化事件更新提示值
            widget = ttk.Scale(
                self.root_frame,
                from_=0,
                to=self.limit,
                command=lambda val: num_label.config(text=f"{int(float(val))}"),
            )
            num_label.config(text="0")  # 初始化提示值为 0
            num_label.grid(
                row=self.start_row, column=2, sticky="e"
            )  # 提示值放在第2列，靠右对齐

        # 控件放置在第3列，靠右对齐
        widget.grid(row=self.start_row, column=3, sticky="we",padx=5,pady=5)
        
        self.data.update({label_text:widget})

    def get_data(self):
        return self.data

    def grid(self,**kwargs):
        """
        将设置项容器放置到主框架中，启用自适应布局。
        """
        #self.root_frame.grid(row=0, column=0, sticky="nsew")
        
        
        # 配置各列权重，使布局适应窗口大小变化
        self.root_frame.grid_columnconfigure(0, weight=1)  # 标签列：可扩展
        self.root_frame.grid_columnconfigure(1, weight=1)  # 中间空列（可选）
        self.root_frame.grid_columnconfigure(2, weight=0)  # 提示值列：固定宽度
        self.root_frame.grid_columnconfigure(3, weight=1)  # 控件列：可扩展
        
        super().grid(**kwargs)

def set_hover(entry: ttk.Entry, placeholder_text: str):
    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(foreground="white")

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.config(foreground="grey")

    entry.insert(0, placeholder_text)
    entry.config(foreground="grey")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)