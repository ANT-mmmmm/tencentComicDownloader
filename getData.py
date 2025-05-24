from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import random
import time
import json
import lib
import os,io
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ComicData:
    """漫画基本信息数据类"""

    title: str  # 漫画标题
    comic_id: str  # 漫画ID
    cover_url: Optional[str] = None  # 封面URL
    author: Optional[str] = None  # 作者
    tags: Optional[List[str]] = None  # 标签
    description: Optional[str] = None  # 描述
    update_time: Optional[str] = None  # 更新时间

@dataclass
class ChapterInfo:
    """章节信息数据类"""
    comic: ComicData

    title: str  # 章节标题
    cid: str  # 章节cid
    app: bool = False  # 是否为VIP章节
    page_count: Optional[int] = None  # 页数


# ---主类---
class ComicDownloader:
    """漫画下载器主类，支持多线程下载"""

    def __init__(
        self,
        debug: bool = False,
        max_webdrivers: int = 2,
        max_download_threads: int = 4,
        timeout: int = 60,
        headless: bool = True,
        download_path=str
    ):
        """
        初始化下载器

        Args:
            debug (bool): 是否开启调试模式
            maxWebdrivers (int): 浏览器最大数量
            maxDownloadThreads (int): 图片下载最大线程数量
            timeout (int): (单位: s) 浏览器超时时限
        """
        logging.info('主类已启动')
        self.debug = debug
        self.max_webdrivers = max_webdrivers
        self.max_download_threads = max_download_threads
        self.timeout = timeout
        self.current_drivers=0
        self.headless = headless
        self.download_path=download_path
        
        self.initialized=False

        self._init_webdrivers()
        logging.info('浏览器已启动')

        # 状态跟踪
        self.is_running = False
        self.current_task = None
        self.progress_callbacks = []

        # 基础URL配置
        self.mobile_url = "https://m.ac.qq.com"
        self.pc_url = "https://ac.qq.com"

    # 建立浏览器队列
    def _init_webdrivers(self) -> None:
        """
        初始化浏览器队列
        """
        self.web_drivers_queue = queue.Queue()
    
        # 创建一个Edge浏览器实例
        def create_driver():
            return webdriver.Edge(options=self._get_random_driver_options())
        
        # 使用线程池执行器并行创建浏览器实例
        with ThreadPoolExecutor() as executor:
            # 提交任务到线程池，创建多个浏览器实例
            futures = [executor.submit(create_driver) for _ in range(self.max_webdrivers)]
            # 等待所有浏览器实例创建完成，并将它们放入队列中
            for future in as_completed(futures):
                self._put_webdriver(future.result())
        self.initialized = True
    def _get_webdriver(self) -> webdriver.Edge:
        return self.web_drivers_queue.get()

    def _put_webdriver(self,webdriver_:webdriver.Edge):
        self.web_drivers_queue.put(webdriver_)

    # 初始化浏览器设置
    def _get_random_driver_options(self) -> webdriver.EdgeOptions:
        """
        获取浏览器设置
        """
        driver_options = webdriver.EdgeOptions()
        
        driver_options.add_argument("--log-level=3")  # 设置日志级别为 3（ERROR）
        driver_options.add_argument("--disable-logging")  # 禁用日志
        driver_options.add_argument("--disable-dev-shm-usage")  # 禁用共享内存
        driver_options.add_argument("--no-sandbox")  # 禁用沙盒模式

        driver_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )  # 禁止图片加载
        driver_options.add_argument(
            "--blink-settings=imagesEnabled=false"
        )  # 禁止图片加载
        driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver_options.add_experimental_option("useAutomationExtension", False)
        driver_options.add_argument("--inprivate")  # 无痕模式
        if self.headless:  # 无头模式
            driver_options.add_argument("--headless")
        else:
            pass
        driver_options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )  # 禁止自动化控制
        driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver_options.add_experimental_option("useAutomationExtension", False)
        #driver_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # 2. 用户代理随机化
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]
        driver_options.add_argument(f"user-agent={random.choice(user_agents)}")

        # 3. 禁用自动化特征
        driver_options.add_argument("--disable-infobars")
        driver_options.add_argument("--disable-extensions")
        #driver_options.add_argument("--disable-gpu")
        driver_options.add_argument("--disable-dev-shm-usage")
        driver_options.add_argument("--no-sandbox")

        # 4. 语言和时区设置
        driver_options.add_argument("--lang=en-US")
        driver_options.add_argument("--timezone=America/New_York")

        # 5. 窗口大小随机化
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        driver_options.add_argument(f"--window-size={width},{height}")

        # 6. 禁用自动化标志 (重要)
        driver_options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.images": 1,
            },
        )

        # 7. 禁用WebDriver标志
        driver_options.add_argument("--disable-blink-features")
        driver_options.add_argument("--disable-blink-features=AutomationControlled")

        return driver_options

    # 通过腾讯搜索
    def search_comic_by_tencent(self, title) -> list[ComicData]:
        """通过腾讯搜索漫画
        
        参数:
        title -- 漫画标题用于搜索
        
        返回:
        一个包含ComicData对象的列表，每个对象包含有关搜索结果的详细信息
        """
    
        # 获取webdriver实例
        driver = self._get_webdriver()
        driver: webdriver.Edge
    
        # 设置页面加载超时时间
        driver.set_page_load_timeout(self.timeout)
    
        # 构造搜索URL并请求页面
        driver.get(self.mobile_url + r"/search/result?word=" + title)
    
        # 等待页面加载完成，动态加载更多内容
        while 1:
            if self.debug:
                logging.info("下滑")
            try:
                tmp=driver.find_element(By.CLASS_NAME, "mlm-status-loading")
                break
            except:
                pass
            if 'text-not-found' in driver.page_source:
                break
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.02)
    
        # 根据类名爬取目录
        text = driver.page_source
    
        # 使用文本处理更快
        html = lib.HTMLParser(text)
    
        # 获取信息的列表
        comic_title = html.find_elements_by_class_name("comic-title")
        comic_link = html.find_elements_by_class_name("comic-link")
        cover_image = html.find_elements_by_class_name("cover-image")
        comic_tag = html.find_elements_by_class_name("comic-tag")
        comic_update = html.find_elements_by_class_name("comic-update")
        comic_description = html.find_elements_by_class_name("comic-update")
    
        # 总索引
        search_index = []
    
        # 遍历获取的信息并创建ComicData对象
        for i in range(len(comic_tag)):
            # 拆解列表
            title = comic_title[i].get_attribute("innerText")
            link = comic_link[i].get_attribute("href")
            image = cover_image[i].get_attribute("src")
            tags_ = comic_tag[i].get_attribute("innerText")
            update = comic_update[i].get_attribute("innerText").replace(' 更新','')
            disc = comic_description[i].get_attribute("innerHTML")
    
            # 创建ComicData对象并添加到结果列表
            tmp = ComicData(
                title=title,
                comic_id=link[link.rfind('/')+1:],
                cover_url=image,
                tags=tags_,
                description=disc,
                update_time=update,
            )
            search_index.append(tmp)
        
        # 归还webdriver实例
        self._put_webdriver(driver)
        return search_index
    #  通过bing搜索
    def search_comic_by_bing(self, title) -> list[ComicData]:
        '''
        使用 Bing 搜索引擎查找漫画。
        
        通过提供漫画标题，构造搜索 URL 并使用 WebDriver 加载页面，然后解析页面源代码以查找漫画信息。
        
        参数:
        - title: 要搜索的漫画标题。
        
        返回:
        - list[ComicData]: 包含漫画数据的列表，每个元素都是一个 ComicData 对象。
        '''
        # 初始化 WebDriver
        driver = self._get_webdriver()
        
        # 构造并请求搜索 URL
        driver.get('https://cn.bing.com/search?q=' + title + '%20%E8%85%BE%E8%AE%AF%E6%BC%AB%E7%94%BB')
        logging.info('搜索: ' + 'https://cn.bing.com/search?q=' + title + '%20%E8%85%BE%E8%AE%AF%E6%BC%AB%E7%94%BB')
        
        # 等待页面加载完成
        time.sleep(1)
        
        # 获取页面源代码
        source = driver.page_source
        
        # 解析页面源代码以查找漫画链接
        lists = lib.findString(source, 'href="https://ac.qq.com/Comic/comicInfo/id/', '" h="', 43, -5)
        
        for i in range(len(lists)):
            # 获取链接
            try:
                url = lib.findString(source, 'href="https://ac.qq.com/Comic/comicInfo/id/', '" h="', 43, -5)[i]
                href = lib.findString(source, 'href="https://ac.qq.com/Comic/comicInfo/id/', '" h="', 6, -5)[i]
                url = url[:url.find('?')]
            except IndexError as e:
                logging.info('未找到:\t' + str(e))
                self._put_webdriver(driver)
                return None
            except Exception as e:
                logging.info('未知错误:\t' + str(e))
                self._put_webdriver(driver)
                return None
            
            # 获取标题
            comic_title = driver.get(href)
            time.sleep(0.5)
            comic_title = lib.clean_text(driver.find_element(By.TAG_NAME, 'h2').get_attribute('innerText'))
            
            # 判断标题
            if title not in comic_title:
                continue
            
            tmp = int(url)
            
            self._put_webdriver(driver)
            return ComicData(title=comic_title, comic_id=url)
    #  搜索
    def search_comic(self, title) -> Optional[ComicData]:
        """
        搜索判断逻辑
        """
        logging.info('搜索:\t'+str(title))
        self.current_task='search_comic'
        self.is_running = True
        result = self.search_comic_by_tencent(title)
        
        #查找结果
        comic=None
        for i in result:
            if title in i.title:
                comic=i
                logging.info('在\t腾讯动漫\t找到了')
                break

        
        if not comic:
            logging.info('在\t腾讯动漫\t未找到')

            comic=self.search_comic_by_bing(title)
            if comic:
                logging.info('在\tbing\t找到了')
            else:
                logging.info('在\tbing\t未找到')

        
        if not comic:
            logging.info('未找到')
            self.is_running  = False
            self.current_task=None
            return None
        else:
            logging.info('找到了:\t'+comic.title+'\n\t'+comic.comic_id+'\n\t'+self._get_comic_link(comic.comic_id))
            self.is_running=False
            self.current_task=comic
            return comic
    # 获取链接
    def _get_comic_link(self, comic_id):
        return self.pc_url + r"/Comic/ComicInfo/id/" + comic_id
    def _get_mobile_comic_link(self, comic_id):
        return self.mobile_url + r"/comic/index/id/" + comic_id
    
    def get_chapters(self,comic:ComicData) -> list[ChapterInfo]:
        self.is_running=True
        self.current_task='get_chapters'
        driver=self._get_webdriver()
        driver.get(self._get_mobile_comic_link(comic.comic_id))
        logging.info('尝试获取章节列表')

        
        time.sleep(1)
        source=driver.page_source
        index_frame=lib.HTMLParser(source).find_element_by_class_name('chapter-wrap-list')
        pr=lib.HTMLParser(source)

        chapter_title_list=index_frame.get_attribute('innerText').split('\n')
        try:
            tag=chapter_title_list.index('APP')-1
        except:
            tag=-1

        chapter_title_list = [x for x in chapter_title_list if x not in ('', 'APP')]

        chapter_link_list=[]

        for i in pr.find_elements_by_class_name('chapter-link'):
            chapter_link_list.append(i.get_attribute('href'))
        logging.info('获取章节列表成功 整理中')


        # 获取章节标题和链接
        chapter_list=[]
        for i in range(len(chapter_title_list)):
            tmp=chapter_link_list[i]
            tmp:str
            if i<tag:

                chapter_list.append(ChapterInfo(
                    comic=comic,
                    title=chapter_title_list[i],
                    cid=tmp[tmp.rfind('/')+1:],
                    app=False
                ))
            else:
                chapter_list.append(ChapterInfo(
                    comic=comic,
                    title=chapter_title_list[i],
                    cid=tmp[tmp.rfind('/')+1:],
                    app=True
                ))
        logging.info('整理完毕')
        
        self._put_webdriver(driver)

        self.is_running=False
        self.current_task=None
        
        return chapter_list
    
    def _from_cid_to_mobile(self,chapter:ChapterInfo):
        output=self.mobile_url+'/chapter/index/id/'+chapter.comic.comic_id+'/cid/'+chapter.cid
        return output




    def get_comic_urls(self,chapter:ChapterInfo) -> list[str]:
        
        self.current_task='get_comic_urls'
        self.is_running=True
        
        #pool = ThreadPoolExecutor(max_workers=self.max_download_threads, thread_name_prefix='Thread')
        tmp=self._get_jpg_files(chapter)
        #with open('./debug/test.json','w+',encoding='utf-8') as f:
        #    f.write(json.dumps(tmp,ensure_ascii=False,indent=4))
        
        self.current_task=None
        self.is_running=False
        return tmp

    
    def _get_jpg_files(self,chapter:ChapterInfo) ->list[str]:
        
        driver=self._get_webdriver()

        driver.get(self._from_cid_to_mobile(chapter))

        time.sleep(3)

        source=driver.page_source

        imgList=lib.findString(source,'data-src="https://manhua.acimg.cn/manhua_detail/0/','.jpg/800',10,-3)

        logging.info(chapter.comic.title+'\t'+chapter.title+' 获取了'+str(len(imgList))+'张图片')

        return imgList

    def download(self,chapter:ChapterInfo,file_name:str,url:str):
        with open(self.download_path+'/'+chapter.comic.title+'/'+chapter.title+'/'+str(file_name)+'.jpg','wb+') as f:
            f.write(requests.get(url).content)