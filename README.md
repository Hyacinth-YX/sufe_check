# Start up
这是一个每天自动为SUFE健康申报的程序，由python写成，包含了actions，可以将项目挂载github上自动运行。
当然你也可以挂在自己的服务器上设置一个定时任务

# actions
github提供的actions服务可以让你在没有服务器的情况下运行一些小程序。

首先在你自己的github上建立一个仓库，将本仓库的所有文件都放到你自己的仓库里，注意自己给自己的仓库一个star。
然后在Settings的Secrets中添加自己的私密信息，主要包括

    UID: ${{ secrets.UID }}
    PASSWD: ${{ secrets.PASSWD }}
    APP_ID: ${{ secrets.APP_ID }}
    API_KEY: ${{ secrets.API_KEY }}
    SECRET_KEY: ${{ secrets.SECRET_KEY }}
    
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
        
在代码第10行（文件中）设置了一个定时任务，这里的时间是美洲时间，与中国相差8小时，所以23代表早上7点。你也可以
指定其他时间。

在修改好代码后请修改form_dir中的表格内容，其中一串由md5编码得到的文件名是表单信息，如果表单内容没有修改的话，那么这串md5数字
摘要得到的字符串应该是不变的，所以你只需要将你的信息填写在这个json文件里面就行了。如果程序运行中创建了一个新的json文件，那么说明
需求的表单可能发生了变化。我暂时没有将其自动化（因为懒），如果出现了这种情况需要按照新的表单填写到新的json文件中。

当你的所有准备工作都完成后，你可以将你的项目push到云端了，在你push后会自动运行第一次，你可以在github的actions中查看日志
，日志中会包括运行信息，如果看上去没问题，那可以暂时放着他不管，然后每天会按照设定的时间自动运行。

如果你绑定了邮箱，程序运行出错的时候会发邮件给你。

# sufe_check.py
这是程序运行的主文件，如果你想要了解详细的使用方式请阅读代码，其中包含了一些注释。如果仅仅是想了解参数，我贴在了这下面

    准备工作：请在form_dir中用md5码摘要得到文件名的json文件中，修改自己的信息

    必选参数 uid:校园卡账号 passwd:密码 os_type:操作系统("mac","windows","linux")
    
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