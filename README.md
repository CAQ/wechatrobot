微信对话机器人

登录过程参考自 https://github.com/0x5e/wechat-deleted-friends

心跳参考自 http://reverland.org/javascript/2016/01/15/webchat-user-bot/

使用方法：

1、修改myself.config（提供了.example，请重命名），加入区分自己账号的信息

2、实现answer.py（提供了.example，请重命名）中的GetAnswer方法。注意：如果返回None或空串则不作答。

3、运行wechatrobot.py，按步骤，扫描二维码、手机确认即可。

备注：

在wechatrobot.py中修改 DEBUG = True 则可控制是否将收到的响应写入本地json文件。
