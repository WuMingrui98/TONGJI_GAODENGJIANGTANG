import tkinter
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from lxml import etree
import traceback
import base64
import re
import os
from selenium import webdriver
from msedge.selenium_tools import Edge
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from PIL import Image
from chaojiying import Chaojiying_Client
import time
import sys


# # 实现无可视化界面
# edge_options = Options()
# edge_options.use_chromium = True
# edge_options.add_argument('--headless')
# edge_options.add_argument('--disable-gpu')
# edge_options.add_experimental_option('excludeSwitches', ['enable-automation'])


def get_code(code_file, code_type, chaojiying_ID, chaojiying_password, chaojiying_softID):
    chaojiying = Chaojiying_Client(chaojiying_ID, chaojiying_password, chaojiying_softID)
    im = open(code_file, 'rb').read()  # 本地图片文件路径 来替换 a.jpg 有时WIN系统须要//
    result = chaojiying.PostPic(im, code_type)  # 1902 验证码类型  官方网站>>价格体系 3.4+版 print 后要加()
    return result


def Registration_operation(driver, forum, information, date_list, name_list):
    time.sleep(2)
    # 显示等待讲堂详情页面可以点击
    WebDriverWait(driver, 20, 0.5).until(lambda driver: forum)
    # 进入报名页面
    forum.click()

    # 显示等待讲堂信息加载信息
    xpath = '//*[@id="app"]/div/div[2]/div[1]/div/div[1]/div/button'
    Wait_ajax_presence(xpath=xpath, driver=driver)
    Wait_ajax_click(xpath=xpath, driver=driver)
    driver.find_element_by_xpath(xpath).click()

    # 判断是否已经报名成功
    # 建立循环，判断是否已经报名成功，如果没有成功则反复等待
    try:
        xpath = '/html/body/div[2]/div/div[1]/div/span'
        locator = (By.XPATH, xpath)
        WebDriverWait(driver, 60, 0.5).until(EC.presence_of_element_located(locator=locator))
        status = driver.find_element_by_xpath(xpath).text
        if status != '报名成功':
            raise Exception
        # 记录报名的课程名称和时间，防止重复报名以及时间不合适
        # 拆分信息
        section = information.split('\n')
        name = section[1]
        date = section[3].split()[0]
        date_list.append(date)
        name_list.append(name)
        # 在文本中记录报名状态
        with open('./报名情况.txt', 'a', encoding='utf-8') as f:
            f.write('\n' + information)
            f.write('\n' + status + '\n')
    except:
        status = '目前报名显示持续等待中或以及报名,请过一段时间登录网站查询报名情况'
        # 记录报名的课程名称和时间，防止重复报名以及时间不合适
        # 拆分信息
        section = information.split('\n')
        name = section[1]
        date = section[3].split()[0]
        date_list.append(date)
        name_list.append(name)
        # 在文本中记录报名状态
        with open('./报名情况.txt', 'a', encoding='utf-8') as f:
            f.write('\n' + information)
            f.write('\n' + status + '\n')
    # 按下确定按钮，取消小窗口
    xpath = '/html/body/div[2]/div/div[3]/button/span'
    Wait_ajax_presence(xpath=xpath, driver=driver)
    Wait_ajax_click(xpath=xpath, driver=driver)
    driver.find_element_by_xpath(xpath).click()
    # 回到首页
    xpath = '//*[@id="app"]/div/div[1]/div/div[2]/a[1]/button/span'
    Wait_ajax_presence(xpath=xpath, driver=driver)
    Wait_ajax_click(xpath=xpath, driver=driver)
    driver.find_element_by_xpath(xpath).click()



# 定义等待动态加载数据可点击的方法
def Wait_ajax_click(xpath=None, class_name=None, name=None,driver=None):
    if xpath is not None:
        locator = (By.XPATH, xpath)
        WebDriverWait(driver, 20, 0.5).until(EC.element_to_be_clickable(locator=locator))
    if class_name is not None:
        locator = (By.CLASS_NAME, class_name)
        WebDriverWait(driver, 20, 0.5).until(EC.element_to_be_clickable(locator=locator))
    if name is not None:
        locator = (By.NAME, name)
        WebDriverWait(driver, 20, 0.5).until(EC.element_to_be_clickable(locator=locator))


# 定义等待动态加载数据加载的方法
def Wait_ajax_presence(xpath=None, class_name=None, name=None, driver=None):
    if xpath is not None:
        locator = (By.XPATH, xpath)
        WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator=locator))
    if class_name is not None:
        locator = (By.CLASS_NAME, class_name)
        WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator=locator))
    if name is not None:
        locator = (By.NAME, name)
        WebDriverWait(driver, 20, 0.5).until(EC.element_to_be_clickable(locator=locator))



def main(tongji_ID, tongji_password, chaojiying_ID, chaojiying_password, chaojiying_softID):
    # 获取已经抢的课的时间，避免时间冲突不能继续抢课
    date_list = []
    # 获取已经抢的课的名称，避免系统出错，显示出已经抢了的课
    name_list = []
    if os.path.exists('./报名情况.txt'):
        os.remove('./报名情况.txt')

    Continuous_operation = True
    Operation_timeout = False
    start = time.time()
    Operation_num = 0
    #  在一段时间内，若因为网络问题或程序出错，则持续抢课
    while (not Operation_timeout) and Continuous_operation:
        try:
            if time.time()-start > 1800:
                Operation_timeout = True
                with open('./报名情况.txt', 'a', encoding='utf-8') as f:
                    f.write('\n操作已超时，建议下次再抢\n')
            # 统计操作次数
            Operation_num += 1
            # 首次运行判断依据
            First_Run = True
            # 循环报名判断依据
            Registration = True
            # -----------登陆操作-------------
            # 按照浏览器类型创建webdriver
            if os.path.exists('./msedgedriver.exe'):
                driver = webdriver.Edge(executable_path=r'msedgedriver.exe')
            elif os.path.exists('./chromedriver.exe'):
                driver = webdriver.Chrome(executable_path=r'chromedriver.exe')
            # # 隐性等待时间
            # driver.implicitly_wait(30)
            driver.get('http://gdjt.tongji.edu.cn/PC/#/login')
            # 显示等待登录按钮可以点击
            class_name = 'el-button'
            Wait_ajax_presence(class_name=class_name, driver=driver)
            Wait_ajax_click(class_name=class_name, driver=driver)
            driver.find_element_by_class_name('el-button').click()
            # 登录成功判断
            Login_OK = False
            while not Login_OK:
                # 获得登陆页面源码
                page_text = driver.page_source
                # 实例化etree对象
                tree = etree.HTML(page_text)

                # 获得验证码
                code = tree.xpath('//*[@id="codeImg"]/@src')[0]

                b64code = re.findall(',(.*?)$', code)[0]
                code_image = base64.b64decode(b64code)
                with open('./code.jpg', 'wb') as f:
                    f.write(code_image)

                # 自动输入验证码
                result = get_code('./code.jpg', 1902, chaojiying_ID, chaojiying_password, chaojiying_softID)['pic_str']
                print(result)

                # # 手动输入验证码
                # image = Image.open('./code.jpg')
                # image.show()
                # result = input('输入验证码：')
                # print(result)

                # 登录操作
                driver.find_element_by_id('username').send_keys(tongji_ID)
                driver.find_element_by_id('password').send_keys(tongji_password)
                driver.find_element_by_id('Txtidcode').send_keys(result)
                # 显示等待Login按钮可以点击
                name = 'btsubmit'
                Wait_ajax_presence(name=name, driver=driver)
                Wait_ajax_click(name=name, driver=driver)
                driver.find_element_by_name(name).click()

                try:
                    driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div[1]/div[1]/div[2]/div[1]/div/input')
                    Login_OK = True
                except:
                    print(traceback.print_exc())
                    pass

            # 建立循环，持续抢课
            while Registration:
                time.sleep(1)
                # 显性等待状态切换按钮
                xpath = '//*[@id="app"]/div/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/input'
                Wait_ajax_presence(xpath=xpath, driver=driver)
                Wait_ajax_click(xpath=xpath, driver=driver)
                # 切换高等讲堂状态
                # 点击状态
                driver.find_element_by_xpath(xpath).click()
                time.sleep(1)
                # 显性等待有余位按钮,第二运行位置会变
                if First_Run:
                    xpath = '/html/body/div[2]/div[1]/div[1]/ul/li[2]'
                else:
                    xpath = '/html/body/div[3]/div[1]/div[1]/ul/li[2]'
                Wait_ajax_presence(xpath=xpath, driver=driver)
                Wait_ajax_click(xpath=xpath, driver=driver)
                # 点击有余位
                driver.find_element_by_xpath(xpath).click()
                time.sleep(2)
                # 显示等待讲堂信息加载信息
                xpath = '//*[@id="app"]//div[@class="Lecturelist"]/li'
                locator = (By.XPATH, xpath)
                WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator=locator))
                # 获取讲堂信息
                forum_list_temp = driver.find_elements_by_xpath(xpath)
                # 为了避免获取的讲堂时间重合，需要筛选掉相同日期的高等讲堂
                forum_list = []
                for forum in forum_list_temp:
                    # 判断这个信息能否添加到forum_list中
                    Forum_OK = True
                    for each in date_list:
                        if each in forum.text:
                            Forum_OK = False
                    if Forum_OK:
                        for each in name_list:
                            if each in forum.text:
                                Forum_OK = False
                    if Forum_OK:
                        forum_list.append(forum)

                # 定义一个请求状态
                Get_forum = False
                # 定义一个请求状态
                Click_forum = False
                # 先获取线上的讲堂
                for forum in forum_list:
                    information = forum.text
                    if "zoom" in information:
                        # 调用报名的功能函数
                        Registration_operation(driver, forum, information, date_list, name_list)
                        # 显示已经发起过报名了
                        Click_forum = True
                        # 将报名状态转变已经报名过了
                        Get_forum = True
                        break

                # 再获取四平的线下讲堂
                if not Click_forum:
                    for forum in forum_list:
                        information = forum.text
                        if "四平" in information:
                            # 调用报名的功能函数
                            Registration_operation(driver, forum, information, date_list, name_list)
                            # 将报名状态转变已经报名过了
                            Get_forum = True
                            break

                if not Get_forum:
                    with open('./报名情况.txt', 'a', encoding='utf-8') as f:
                        f.write('\n已经没有合适的高等讲堂了，等下次吧\n')
                    Registration = False
                    Continuous_operation = False
                    driver.quit()
                    break
                First_Run = False
                time.sleep(180)
        except:
            print(traceback.print_exc())
            traceback.print_exc()
            if Operation_num > 5:
                time.sleep(5)
            elif Operation_num > 10:
                time.sleep(10)
            elif Operation_num > 30:
                Continuous_operation = False
            driver.quit()
            with open('./报名情况.txt', 'a', encoding='utf-8') as f:
                f.write('\n出错一次\n')
    os._exit(0)


def scheduler_operation():
    tongji_ID = entry1[0].get()
    tongji_password = entry1[1].get()
    chaojiying_ID = entry2[0].get()
    chaojiying_password = entry2[1].get()
    chaojiying_softID = entry2[2].get()
    year = int(entry3[0].get())
    month = int(entry3[1].get())
    day = int(entry3[2].get())
    hour = int(entry3[3].get())
    minute = int(entry3[4].get())
    second = int(entry3[5].get())
    # 定时执行
    scheduler = BlockingScheduler()
    # scheduler.add_job(main, 'date', run_date=datetime(2021, 4, 13, 12, 20, 0))
    scheduler.add_job(main, 'date', run_date=datetime(year, month, day, hour, minute, second), kwargs={"tongji_ID": tongji_ID, "tongji_password": tongji_password,\
                                                                                                       "chaojiying_ID": chaojiying_ID, "chaojiying_password": chaojiying_password, \
                                                                                                       "chaojiying_softID": chaojiying_softID})
    scheduler.start()


# 编写交互界面
myWindow = tkinter.Tk()
# 设置标题
myWindow.title('高等讲堂自动报名')
# 设置窗口大小
myWindow.geometry('380x300')
# 创建frame
frame1 = tkinter.Frame(myWindow)
frame2 = tkinter.Frame(myWindow)
frame3 = tkinter.Frame(myWindow)
frame1.grid(row=0, column=0, columnspan=2)
frame2.grid(row=1, column=0, columnspan=2)
frame3.grid(row=2, column=0, columnspan=2)
#标签控件布局
tkinter.Label(frame1, text='同济大学统一身份认证').grid(row=0, column=0, columnspan=2)
tkinter.Label(frame1, text="用户名").grid(row=1, column=0)
tkinter.Label(frame1, text="密码").grid(row=2, column=0)
tkinter.Label(frame2, text='超级鹰账户').grid(row=0, column=0, columnspan=2)
tkinter.Label(frame2, text="用户名").grid(row=1, column=0)
tkinter.Label(frame2, text="密码").grid(row=2, column=0)
tkinter.Label(frame2, text="软件ID").grid(row=3, column=0)
tkinter.Label(frame3, text='运行时间').grid(row=0, column=0, columnspan=12)
tkinter.Label(frame3, text="年").grid(row=1, column=1)
tkinter.Label(frame3, text="月").grid(row=1, column=3)
tkinter.Label(frame3, text="日").grid(row=1, column=5)
tkinter.Label(frame3, text="时").grid(row=1, column=7)
tkinter.Label(frame3, text="分").grid(row=1, column=9)
tkinter.Label(frame3, text="秒").grid(row=1, column=11)

# Entry控件布局
entry1 = []
entry2 = []
entry3 = []
for i in range(2):
    entry1.append(tkinter.Entry(frame1))
for i in range(3):
    entry2.append(tkinter.Entry(frame2))
for i in range(6):
    entry = tkinter.Entry(frame3, width=5)
    entry3.append(entry)
entry1[0].grid(row=1, column=1)
entry1[1].grid(row=2, column=1)
entry2[0].grid(row=1, column=1)
entry2[1].grid(row=2, column=1)
entry2[2].grid(row=3, column=1)
entry3[0].grid(row=1, column=0)
entry3[1].grid(row=1, column=2)
entry3[2].grid(row=1, column=4)
entry3[3].grid(row=1, column=6)
entry3[4].grid(row=1, column=8)
entry3[5].grid(row=1, column=10)

# 确定按钮运行程序，退出按钮退出程序
tkinter.Button(myWindow, text='确定', command=scheduler_operation).grid(row=3, column=0, padx=5, pady=5)
tkinter.Button(myWindow, text='退出', command=myWindow.quit).grid(row=3, column=1, padx=5, pady=5)
myWindow.mainloop()

# # 切换页码的操作
# driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div[2]/div/div/span/div/input').clear()
# driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div[2]/div/div/span/div/input').send_keys('2')
# driver.find_element_by_class_name('topMenu').click()
