# NEW
2020.7.9 
    
* 修复了超过maxretry后仍然执行程序的bug，如果一直无法登陆成功可以尝试调高maxretry，
如果retry很多次一直没有作用很可能有两种情况：api接口有问题，请检查是否是文本识别接口；系统
有差别，这种情况如果你是actions里运行应该比较少见，因为他们应该都是同样的环境。但如果真的
出现了，可以自己运行一下code看看code_dir中是否有正确的验证码图片，如果是空白的说明截图位置
不对。
* 另外修改了auto_check_SF中的时间问题，将时区设置成上海时区，如果要指定时间只需指定正常
的时间即可。这是因为程序中有获取日期这一需求，每天填报的日期是按照系统时间来的，原本的定时
任务中，如果时间设定在早上8点以前也就是系统时间24点以前，是前一天的时间。报表上报是错误的
所以会出现`"!!不知道哪里出错了，没有提交成功QWQ"`

2020.8.3
修复安装chrome失败的问题

2020.8.26
为了匹配最新稳定版本chrome，更换chromedrive以匹配85版本。部分老版本chrome可能本机运行
时不匹配，请替换为old version或升级chrome，变换为符合版本。

2020.12.26
用户如果需要部署项目可以直接fork本项目，在secrets中设置相应参数，然后在form_dir中修改相应学院即可。

此外发现windows用户直接克隆项目修改后，会加入特殊编码的问题，建议直接fork到自己仓库后，使用github编辑他。


# Start up
这是一个每天自动为SUFE健康申报的程序，由python写成，包含了actions，可以将项目挂载github上自动运行。
当然你也可以挂在自己的服务器上设置一个定时任务。

# actions
github提供的actions服务可以让你在没有服务器的情况下运行一些小程序。

首先在你自己的github上建立一个仓库，将本仓库的所有文件都放到你自己的仓库里，注意自己给自己的仓库一个star。
然后在Settings的Secrets中添加自己的私密信息，主要包括

    UID: ${{ secrets.UID }} 你的学号
    PASSWD: ${{ secrets.PASSWD }} 你的密码
    APP_ID: ${{ secrets.APP_ID }} 你的百度aip相关信息
    API_KEY: ${{ secrets.API_KEY }} 你的百度aip相关信息
    SECRET_KEY: ${{ secrets.SECRET_KEY }} 你的百度aip相关信息
    STDNAME: ${{secrets.STDNAME}} 你的姓名
    MOBILE: ${{secrets.MOBILE}} 你的手机号码
    
UID是你的学号，PASSWD是登录密码，APP_ID、API_KEY、SECRET_KEY是可选如果你选了baidu api作为验证码解码器
那么需要去[百度ai开放平台](https://ai.baidu.com)申请一个账户，在文字识别服务中新建一个应用，他会提供你相关
信息。百度aip在一定额度中是免费的，相信只是登录的验证码识别你是无法用完一天50000次的额度的。

如果你更希望修改decoder的方法，不想使用百度的decoder，那么你需要修改actions的脚本。

actions的运行脚本在`./github/workflows/auto_check_SF.yml`如果有能力里自己修改的话可以修改脚本。
python的运行参数在sufe_check中都有描述，可以按照他来使用

actions脚本中其中有一个参数需要注意

    on:
      push:
        branches:
          - master
      watch:
        types: started
      schedule:
        - cron: 0 23 * * *
        
~~在代码第10行（文件中）设置了一个定时任务，这里的时间是美洲时间，与中国相差8小时，所以23代表早上7点。你也可以
指定其他时间。~~ (hints:这里已经被修改，因为有时间查询需求，actions中已将时区换成上海
时区，只需要指定常规时间即可)

在修改好代码后请修改form_dir中的表格内容，其中一串由md5编码得到的文件名是表单信息，如果表单内容没有修改的话，那么这串md5数字
摘要得到的字符串应该是不变的，所以你只需要将你的信息填写在这个json文件里面就行了(不过其实基本只要修改学院和地址，隐私信息我都放到secrets里了)
。如果程序运行中创建了一个新的json文件，那么说明需求的表单可能发生了变化。我暂时没有将其自动化（因为懒），
如果出现了这种情况需要按照新的表单填写到新的json文件中。

当你的所有准备工作都完成后，你可以将你的项目push到云端了，在你push后会自动运行第一次，你可以在github的actions中查看日志
，日志中会包括运行信息，如果看上去没问题，那可以暂时放着他不管，然后每天会按照设定的时间自动运行。

如果你绑定了邮箱，程序运行出错的时候会发邮件给你。

# sufe_check.py
这是程序运行的主文件，如果你想要了解详细的使用方式请阅读代码，其中包含了一些注释。如果仅仅是想了解参数，我贴在了这下面

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
# 声明
本项目是零碎时间写的，主要为了自己偷懒使用，不保证一直运行正常。（测试时间不够久可能有一定风险）

允许用户自己使用或二次开发，但不允许私自用于商业用途。引用请标明出处。

如果你发现有什么bug可以在issues中提出来，也可以邮件联系我clearbamboo at outlook.com (at为@)