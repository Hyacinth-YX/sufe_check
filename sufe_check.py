# -*- coding:utf-8 -*-
# Author: Hyacinth
import requests
from bs4 import BeautifulSoup
import hashlib
import os
import json
import time
import argparse

from PIL import Image, ImageEnhance
import pytesseract

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class checker ():
    def __init__(self, uid, passwd, stdName, mobile, form_dir="./form_dir", code_dir="./code_dir", os_type="mac",
                 decoder="baidu",
                 app_id="", api_key="", secret_key="", maxretry=10):
        self.os_type = os_type  # mac or linux, not support windows
        self.decoder = decoder  # "baidu" or "pytesseract"
        self.headless = True

        """ 你的 APPID AK SK """
        self.APP_ID = app_id
        self.API_KEY = api_key
        self.SECRET_KEY = secret_key

        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Connection': 'keep-alive',
            'accept': '*/*'
        }

        self.queryUrl = 'http://stu.sufe.edu.cn/stu/ncp/cn.edu.sufe.ncp.stuReport.queryStdInfo.biz.ext'
        self.formUrl = 'http://stu.sufe.edu.cn/stu/ncp/ncpIndex1.jsp'
        self.finishedUrl = "http://stu.sufe.edu.cn/stu/ncp/finished.html"
        self.submitUrl = 'http://stu.sufe.edu.cn/stu/ncp/cn.edu.sufe.ncp.stuReport.submit.biz.ext'

        self.session = requests.session ()
        self.form_dir = form_dir
        self.code_dir = code_dir
        self.uid = uid
        self.stdName = stdName
        self.mobile = mobile
        self.passwd = passwd
        self.maxretry = maxretry

        if self.headless:
            from selenium.webdriver.chrome.options import Options  # no gui
            self.chrome_options = Options ()
            self.chrome_options.add_argument ('--headless')
            self.chrome_options.add_argument ('--disable-gpu')
            self.chrome_options.add_argument ('--no-sandbox')
            self.chrome_options.add_argument ("window-size=1980,1080")
        else:
            self.chrome_options = None

        if self.os_type == "mac":
            self.DRIVER_PATH = "./chromeDriver/chromedriver_mac"
        elif self.os_type == "linux":
            self.DRIVER_PATH = "./chromeDriver/chromedriver_linux"
        elif self.os_type == "windows":
            self.DRIVER_PATH = "./chromeDriver/chromedriver_win.exe"
        else:
            print ('os_type error, please select from ["windows","mac","linux"]')
            exit (1)

        if self.decoder == "baidu":
            self.initial_baidu_aip ()

    def initial_baidu_aip(self):
        from aip import AipOcr
        try:
            self.client = AipOcr (self.APP_ID, self.API_KEY, self.SECRET_KEY)
            if not self.client:
                print ("百度api没有配置成功，请检查一下")
        except Exception as e:
            print (e)
            exit (1)

    def get_valid_code(self, browser):
        code_file_name = self.get_code_image (browser)
        if self.decoder == "baidu":
            code = self.decode_by_baidu (code_file_name)
            return code
        else:
            code = self.decode_by_pytesseract (code_file_name)
            return code

    def get_login_cookie(self):
        retry = 0
        while True:
            try:
                browser = webdriver.Chrome (self.DRIVER_PATH,options=self.chrome_options)

                browser.get (self.queryUrl)

                WebDriverWait (browser, 10).until (
                    EC.presence_of_element_located ((By.ID, "userId"))
                )
                browser.set_window_position (0, 0)
                element = browser.find_element_by_class_name ("user-login")
                element.click ()
            except Exception as e:
                print (e)
                exit (1)

            valid_code = self.get_valid_code (browser)
            if (len (valid_code) < 5):
                print("识别到的验证码不符合要求正在重试")
                browser.refresh ()
                continue

            try:
                browser.find_element_by_id ("username").send_keys (self.uid)
                browser.find_element_by_id ("password").send_keys (self.passwd)
                browser.find_element_by_id ("imageCodeName").send_keys (valid_code)
                browser.find_element_by_class_name ("login").click ()
                result = browser.find_element_by_tag_name("pre")

                # result = WebDriverWait (browser, 5).until (EC.alert_is_present (), "没有消息框，是不是已经填好辽？")
                if result:
                    result = json.loads(result.text)['result'][0]
                    if result['ISFINISHED'] == 1:
                        print("报告完成")
                        exit(0)
                    else:
                        break
                else:
                    browser.refresh ()
                    retry += 1
                    if retry >= self.maxretry:
                        print("尝试次数达到最大次数，请检查验证码是否解码正确，或用户名密码是否输入正确")
                        exit(555)
            except Exception as e:
                    browser.refresh ()
                    retry += 1
                    if retry >= self.maxretry:
                        print ("尝试次数达到最大次数，请检查验证码是否解码正确，或用户名密码是否输入正确")
                        exit (555)
        # 获取cookie
        sufeCookies = browser.get_cookies ()
        browser.quit ()
        cookies = {}
        for item in sufeCookies:
            cookies[item['name']] = item['value']

        cookiesJar = requests.utils.cookiejar_from_dict (cookies, cookiejar=None, overwrite=True)
        self.session.cookies = cookiesJar

    def get_code_image(self, browser):
        try:
            _file_name = str (int (time.time ()))
            _file_name_wz = str (_file_name) + '.png'
            _file_url = self.code_dir + '/' + _file_name_wz
            browser.get_screenshot_as_file (_file_url)  # get_screenshot_as_file截屏
            if not os.path.exists(_file_url):
                print("全屏截图失败")
                exit(3)

            captchaElem = browser.find_element_by_id ("codeImg").find_element_by_tag_name ("img")  # # 获取指定元素（验证码）

            captchaX = int (captchaElem.location['x'])
            captchaY = int (captchaElem.location['y'])  # 不知道为什么截屏的验证码需要下移60p
            # 获取验证码宽高
            captchaWidth = captchaElem.size['width']
            captchaHeight = captchaElem.size['height']

            captchaRight = captchaX + captchaWidth
            captchaBottom = captchaY + captchaHeight

            browserWidth = browser.get_window_size ()['width']
            browserHeight = browser.get_window_size ()['height']

            tx_p = float (captchaX / browserWidth)
            ty_p = float (captchaY / browserHeight)
            bx_p = float (captchaRight / browserWidth)
            by_p = float (captchaBottom / browserHeight)

            imgObject = Image.open (_file_url)  # 获得截屏的图片
            w, h = imgObject.size
            tx = w * tx_p
            ty = h * ty_p
            bx = w * bx_p
            by = h * by_p
            imgCaptcha = imgObject.crop ((tx, ty, bx, by))  # 裁剪
            validcode_file_name = str (_file_name) + 'valid.png'
            imgCaptcha.save (self.code_dir + '/' + validcode_file_name)
            os.remove (_file_url)
            return validcode_file_name
        except Exception as e:
            print ('错误 ：', e)

    def checkIfSubmited(self):
        try:
            flag = self.session.get (self.queryUrl, headers=self.header).json ()['result'][0]['ISFINISHED'] == 1
            return True if flag else False
        except Exception as e:
            print ("检查是否提交时出错", e)
            exit (1)

    def queryForm(self) -> str:
        isFinished = self.checkIfSubmited ()
        if isFinished:
            print ("表格填写完成")
            exit (0)
        else:
            time.sleep (1)
            response = self.session.get (self.formUrl, headers=self.header).text
            soup = BeautifulSoup (response, 'lxml')
            if soup.text.find ("是否被发现疑似") > -1:
                content = "".join(list(map(str,soup.find_all("div",attrs={"class":"weui-cells__title"}))))
                digest = hashlib.md5 (content.encode (encoding="gb2312")).hexdigest ()
                formname = digest + ".json"
                return formname
            else:
                print ("登陆错误，请检查cookie!")
                exit (1)

    def submitForm(self, formName) -> bool:
        filePath = self.form_dir + "/" + formName
        if os.path.exists (filePath):
            with open (filePath, "r") as f:
                form = json.loads (f.read ())
            form["reportDate"] = time.strftime ("%Y-%m-%d", time.localtime ())
            form.update ({"stdCode": self.uid, "stdName": self.stdName, "mobile": self.mobile})
            url = self.submitUrl
            response = self.session.post (url, headers=self.header, data=form)
            if response.status_code == 200:
                print ("submit 成功")
            else:
                response.raise_for_status ()
        else:
            print (f"表单信息不存在或可能已经修改，请在{filePath}中手动填写信息")
            with open (filePath, 'w') as f:
                f.write ("请根据stdForm填写该文件")

    def _get_file_content(self, filePath):
        with open (filePath, 'rb') as fp:
            return fp.read ()

    """百度aip识别验证码"""
    def decode_by_baidu(self, image_name):
        """ 读取图片 """
        image = self._get_file_content (self.code_dir + "/" + image_name)
        """ 调用通用文字识别, 图片参数为本地图片 """
        self.client.basicGeneral (image);
        """ 带参数调用通用文字识别, 图片参数为本地图片 """
        re = self.client.basicGeneral (image)
        return re['words_result'][0]['words'].replace (" ", "") if len (re['words_result']) > 0 else ""

    def decode_by_pytesseract(self, code_file_name):
        imageCode = Image.open ("./code_dir" + "/" + code_file_name)  # 图像增强，二值化
        imageCode.load ()
        sharp_img = ImageEnhance.Contrast (imageCode).enhance (2.0)
        sharp_img.load ()
        code = pytesseract.image_to_string (sharp_img).strip ().replace (" ", "")
        return code


def init_parser():
    # 可以在运行时指定用户名密码，也可以在这里手动添加，为保证安全性，建议在运行时用secrets指定
    parser = argparse.ArgumentParser ()
    parser.add_argument ("-uid", help="用户名")
    parser.add_argument ("-passwd", help="密码")
    parser.add_argument ("-stdName", help="学生姓名")
    parser.add_argument ("-mobile", help="登记的手机号码（注意与学号对应）")
    parser.add_argument ("-os_type", help='操作系统("mac","windows","linux")')
    parser.add_argument ("-decoder", help="解码器('baidu','pytesseract')")
    parser.add_argument ("-app_id", help="百度aip接口")
    parser.add_argument ("-api_key", help="百度aip接口")
    parser.add_argument ("-secret_key", help="百度aip接口")
    parser.add_argument ("-form_dir", help="指定当前文件夹下存放表单的文件夹相对路径，路径请使用\"\"包裹")
    parser.add_argument ("-code_dir", help="验证码所在文件夹")
    parser.add_argument ("-maxretry", help="最大尝试次数")
    args = parser.parse_args ()
    return args

"""            
准备工作：请在form_dir中用md5码摘要得到文件名的json文件中，修改自己的信息

必选参数 uid:校园卡账号 passwd:密码 os_type:操作系统("mac","windows","linux") stdName:学生姓名 mobile:手机号码

可选参数  decoder:用于解码验证码的api ("baidu","pytesseract")
        (app_id api_key secret_key):均为百度decoder的账户信息  maxretry:最大尝试次数，默认10
        
        备注：（1）"pytesseract"不需要申请账户，不限流，但是准确度低，如果使用该decoder建议调高maxretry
                innux上要安装tesseract-ocr库，sudo add-apt-repository ppa:alex-p/tesseract-ocr
                  "pytesseract"没有在windows测试，可以自行百度
             （2）"baidu"decoder如果使用，必须填上 app_id api_key secret_key三个参数，该三个参数为申请百度aip创
             建项目后获得。
        
不建议修改的参数 form_dir:存放需要填报表单的json文件夹路径  code_dir:存放验证码的文件夹路径
"""
if __name__ == '__main__':
    args = init_parser()

    uid = None
    passwd = None
    stdName = ""
    mobile = ""
    os_type = None
    decoder = "baidu"
    app_id = ""
    api_key = ""
    secret_key = ""

    form_dir = "./form_dir"
    code_dir = "./code_dir"

    maxretry = 10

    if args.uid:
        uid = args.uid.strip ('"')
    if args.passwd:
        passwd = args.passwd.strip ('"')
    if args.stdName:
        stdName = args.stdName.strip ('"')
    if args.mobile:
        mobile = args.mobile.strip ('"')
    if args.os_type:
        os_type = args.os_type.strip ('"').lower ()
    if args.decoder:
        decoder = args.decoder.strip ('"').lower ()
    if args.app_id:
        app_id = args.app_id.strip ('"')
    if args.api_key:
        api_key = args.api_key.strip ('"')
    if args.secret_key:
        secret_key = args.secret_key.strip ('"')
    if args.form_dir:
        form_dir = args.form_dir.strip ('"')
    if args.code_dir:
        code_dir = args.code_dir.strip ('"')
    if args.maxretry:
        maxretry = int (args.maxretry.strip ('"'))

    print("正在初始化")
    checker_ob = checker (uid=uid, passwd=passwd, os_type=os_type, stdName=stdName, mobile=mobile,
                          form_dir=form_dir, code_dir=code_dir, decoder=decoder,
                          app_id=app_id, api_key=api_key, secret_key=secret_key, maxretry=maxretry)
    print ("正在登陆获取cookie")
    try:
        checker_ob.get_login_cookie ()
    except Exception as e:
        print(e)
        exit(1)
    print("查询待填写form名称")
    filename = checker_ob.queryForm ()
    print("正在尝试填写表单")
    checker_ob.submitForm (filename)
    if checker_ob.checkIfSubmited ():
        print ("检查完毕，确定提交成功啦")
    else:
        print ("!!不知道哪里出错了，没有提交成功QWQ")
