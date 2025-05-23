from concurrent.futures import ThreadPoolExecutor, as_completed
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

logging.info('程序启动')

# 初始化日志系统
logger = lib.LogSystem(file_level=logging.DEBUG, console_level=logging.INFO)

class Tabs(tk.Frame):
    def __init__(self,master=None,**kwargs):
        super().__init__(master,kwargs)
        



class GUI:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title('动漫下载器')

        self.init_webdriver_thread=threading.Thread(target=self._init_webdriver)
        self.init_webdriver_thread.start()

        self.root.resizable(False, False)  # 禁止缩放窗口

        try:# 调用Windows API设置DPI感知
            ctypes.windll.shcore.SetProcessDpiAwareness(1)

            # 获取缩放因子
            ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)

            # 设置Tkinter缩放
            self.root.tk.call('tk', 'scaling', ScaleFactor/75)
        except:
            pass

        sv_ttk.set_theme("dark")

    def _init_webdriver(self):
        self.comic_downloader=getData.ComicDownloader(headless=True)

    def main(self):
        #初始化
        self._build_tabs
        self.tab_Frame.to_tab(0)
        
        self._build_tabs()
        self._init_main_page()
        
        self.root.mainloop()
    
    def _build_tabs(self):
        empty=tk.Canvas(self.root,width=348,height=300,bg='red')
        empty.grid(row=0,column=0)
        self.tab_Frame=GUILibs.Tabs(self.root,show_tab_bar=False)
        self.tab_Frame.add_tab('mainPage')
        self.tab_Frame.add_tab('chapters')
        self.tab_Frame.add_tab('downloadLists')
        self.tab_Frame.add_tab('settings')
        self.tab_Frame.add_tab('init')
        self.tab_Frame.grid(row=0,column=0,sticky='nwse')

    def _init_main_page(self):
        root = self.tab_Frame.get_tabs()[0]

        def to_tab4(arg=''):
            self.tab_Frame.to_tab(3)

        def to_tab3(arg=''):
            self.tab_Frame.to_tab(2)

        def main_page_entry_on_focus_in(event):
            if self.main_page_entry.get() == "输入搜索关键词":
                self.main_page_entry.delete(0, tk.END)
                self.main_page_entry.config(foreground='white')
        
        def _exit():
            self.root.destroy()
            exit()

        def main_page_entry_on_focus_out(event):
            if not self.main_page_entry.get():
                self.main_page_entry.insert(0, "输入搜索关键词")
                self.main_page_entry.config(foreground='grey')


        #标题
        self.main_page_label_title = ttk.Label(root, text='动漫下载器', anchor='center', width=30)
        self.main_page_label_title.grid(row=1, column=1, sticky='wnse',columnspan=3)

        #检索输入
        self.main_page_entry = ttk.Entry(root)
        self.main_page_entry.grid(row=2, column=1, sticky='wnes',columnspan=3)

        #搜索按钮
        self.main_page_search=ttk.Button(root,text='搜索',command=self.search)
        self.main_page_search.grid(row=3,column=1,sticky='nwse',columnspan=3)

        #跳转设置按钮
        self.main_page_to_settings=ttk.Button(root,text='设置',command=to_tab4)#4->seetings
        self.main_page_to_settings.grid(row=4,column=1,sticky='nwse')

        #跳转下载界面按钮
        self.main_page_to_download=ttk.Button(root,text='下载',command=to_tab3)#4->seetings
        self.main_page_to_download.grid(row=4,column=2,sticky='nwse')

        #退出按钮
        self.main_page_quit=ttk.Button(root,text='推出',command=_exit)#4->seetings
        self.main_page_quit.grid(row=4,column=3,sticky='nwse')

        # 设置 placeholder
        self.main_page_entry.insert(0, "输入搜索关键词")
        self.main_page_entry.config(foreground='grey')

        self.root.bind("<Return>", self.search)
        self.main_page_entry.bind("<FocusIn>", main_page_entry_on_focus_in)
        self.main_page_entry.bind("<FocusOut>", main_page_entry_on_focus_out)

        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=1)
        
        #设置基本布局间距
        for child in root.winfo_children():
            info = child.grid_info()  # 获取该控件的 grid 信息
            if info['row'] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                child.grid_configure(pady=10)

        #设置基本布局间距
        for child in root.winfo_children():
            info = child.grid_info()  # 获取该控件的 grid 信息
            if info['column'] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                child.grid_configure(padx=10)

    def _init_init_page(self):
        root=self.tab_Frame.get_tabs()[5]

        info=ttk.Label(root,text='浏览器初始化中',anchor='center')
        info.grid(row=0,column=0)
        
        progress=ttk.Progressbar(root, orient="horizontal", length=30, mode="determinate")
        progress.grid(row=0,column=0)


        #设置基本布局间距
        for child in root.winfo_children():
            info = child.grid_info()  # 获取该控件的 grid 信息
            if info['row'] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                child.grid_configure(pady=10)

        #设置基本布局间距
        for child in root.winfo_children():
            info = child.grid_info()  # 获取该控件的 grid 信息
            if info['column'] % 2 == 1:  # 奇数行（注意：行从 0 开始）
                child.grid_configure(padx=10)




    def search(self,args=''):
        self.search_thread=threading.Thread(target=self.__search)
        
        self.search_thread.start()

    def __search(self):
        text=self.main_page_entry.get()
        self.current_comic_data=self.comic_downloader.search_comic(text)
        if self.current_comic_data:
            self.comic_downloader.get_chapters(self.current_comic_data)
        else:
            logging.error('未找到')


mg=GUI()

mg.main()