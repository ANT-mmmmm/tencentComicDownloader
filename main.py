from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import lib
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import requests
import threading
import os
import sv_ttk
import GUILibs
import ctypes
import tkinter as tk
import tkinter.ttk as ttk
import getData

logging.info("程序启动")

# 初始化日志系统
logger = lib.LogSystem(file_level=logging.DEBUG, console_level=logging.INFO)


class Tabs(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, kwargs)


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动漫下载器")

        self.init_webdriver_thread = threading.Thread(target=self._init_webdriver)
        self.init_webdriver_thread.start()

        self.root.resizable(False, False)  # 禁止缩放窗口

        try:  # 调用Windows API设置DPI感知
            ctypes.windll.shcore.SetProcessDpiAwareness(1)

            # 获取缩放因子
            ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)

            # 设置Tkinter缩放
            self.root.tk.call("tk", "scaling", ScaleFactor / 75)
        except:
            pass

        sv_ttk.set_theme("dark")

    def _init_webdriver(self):
        self.comic_downloader = getData.ComicDownloader(headless=True)

    def main(self):
        # 初始化
        self._build_tabs()
        self.tab_Frame.switch_to_tab(0)
        self._init_main_page()
        self._init_settings_tab()
        self._init_loading_tab()

        self.root.mainloop()

    def _build_tabs(self):
        empty = tk.Canvas(self.root, width=348, height=300, bg="red")
        empty.grid(row=0, column=0)
        self.tab_Frame = GUILibs.Tabs(self.root, show_tab_bar=False)
        self.tab_Frame.add_tab("mainPage")
        self.tab_Frame.add_tab("chapters")
        self.tab_Frame.add_tab("downloadLists")
        self.tab_Frame.add_tab("settings")
        self.tab_Frame.add_tab("loading")

        self.tab_Frame.grid(row=0, column=0, sticky="nwse")

    def _init_main_page(self):
        """
        初始化主页面布局和功能。

        此函数定义了主页面上的各个控件，以及它们的布局和事件处理函数。
        包括标题、搜索输入框、搜索按钮、设置和下载跳转按钮，以及退出按钮。
        """
        # 获取主标签页
        root = self.tab_Frame.get_tabs()[0]

        # 跳转到第4个标签页的函数
        def to_tab4(arg=""):
            self.tab_Frame.switch_to_tab(3)

        # 跳转到第3个标签页的函数
        def to_tab2(arg=""):
            self.tab_Frame.switch_to_tab(2)

        # 退出程序的函数
        def _exit():
            self.root.destroy()
            exit()

        # 标题
        self.main_page_label_title = ttk.Label(
            root, text="动漫下载器", anchor="center", width=30
        )
        self.main_page_label_title.grid(row=1, column=1, sticky="wnse", columnspan=3)

        # 检索输入
        self.main_page_entry = ttk.Entry(root)
        self.main_page_entry.grid(row=2, column=1, sticky="wnes", columnspan=3)
        self.main_page_entry.focus_set()

        # 搜索按钮
        self.main_page_search = ttk.Button(root, text="搜索", command=self.search)
        self.main_page_search.grid(row=3, column=1, sticky="nwse", columnspan=3)

        # 跳转设置按钮
        self.main_page_to_settings = ttk.Button(
            root, text="设置", command=to_tab4
        )  # 4->seetings
        self.main_page_to_settings.grid(row=4, column=1, sticky="nwse")

        # 跳转下载界面按钮
        self.main_page_to_download = ttk.Button(
            root, text="下载", command=to_tab2
        )  # 2->download
        self.main_page_to_download.grid(row=4, column=2, sticky="nwse")

        # 退出按钮
        self.main_page_quit = ttk.Button(
            root, text="退出", command=_exit
        )  # 4->seetings
        self.main_page_quit.grid(row=4, column=3, sticky="nwse")

        # 绑定事件
        self.root.bind("<Return>", self.search)

        GUILibs.set_hover(self.main_page_entry, "输入搜索关键词")

        # 设置网格布局权重
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=1)

        self.basic_layout(root)

    def basic_layout(self, root: ttk.Frame):
        # 设置基本布局间距
        for child in root.winfo_children():
            try:
                info = child.grid_info()  # 获取该控件的 grid 信息
                if info["row"] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                    child.grid_configure(pady=10)
            except:
                pass

        # 设置基本布局间距
        for child in root.winfo_children():
            try:
                info = child.grid_info()  # 获取该控件的 grid 信息
                if info["column"] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                    child.grid_configure(padx=10)
            except:
                pass

    def search(self, args=""):
        text = self.main_page_entry.get()
        if text == "输入搜索关键词" or text == "":
            return None
        self.search_thread = threading.Thread(target=self.__search, args=(text,))
        self.search_thread.start()

    def __search(self, text):
        try:
            self.current_comic_data = self.comic_downloader.search_comic(text)
        except AttributeError as e:
            # 搜索失败
            logging.error(e)
            logging.error("未初始化")
            self.current_comic_data = None
            self.tab_Frame.switch_to_tab(4)
        if self.current_comic_data:
            self.comic_downloader.get_chapters(self.current_comic_data)
        else:
            logging.error("未找到")

    def _init_loading_tab(self):
        root = self.tab_Frame.get_tabs()[4]
        root.configure(border=10)

        info = ttk.Label(root, text="浏览器初始化中", anchor="center")
        info.grid(row=0, column=1, sticky="we")

        def refresh(arg: ttk.Progressbar):
            while True:
                arg["value"] += 3
                arg.update()
                time.sleep(0.01)
                if arg["value"] >= 200:
                    arg["value"] = 0

        progressbar = ttk.Progressbar(
            root, orient="horizontal", length=100, mode="indeterminate"
        )
        progressbar.grid(row=1, column=1, sticky="we")
        refresh_thread = threading.Thread(target=refresh, args=(progressbar,))
        refresh_thread.start()
        root.grid_columnconfigure(1, weight=1)

    def _init_settings_tab(self):
        root = self.tab_Frame.get_tabs()[3]
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=1)

        empty = tk.Canvas(root, width=0, height=0)

        main_frame = GUILibs.Settings(root, text="通用设置")
        main_frame.grid(row=2, column=1, columnspan=3, sticky="we")

        main_frame.add_setting("下载路径", "str")
        main_frame.add_setting("下载线程数", "int", limit=4)
        # main_frame.add_setting("下载质量","str")

        download_path_entry = main_frame.get_data()["下载路径"]
        download_path_entry: ttk.Entry

        GUILibs.set_hover(download_path_entry, "./download")

        def back():
            self.tab_Frame.switch_to_tab(0)

        def save():
            back()

        back_button = ttk.Button(root, text="取消", command=back)
        back_button.grid(row=3, column=3, sticky="sw")

        save_button = ttk.Button(root, text="保存", command=save)
        save_button.grid(row=3, column=1, sticky="se")

        self.basic_layout(root)
        empty.grid(row=1, column=1, columnspan=3, sticky="we", pady=5)


mg = GUI()

mg.main()
