import json
import requests
import os
import sys
import time
from requests_toolbelt import MultipartEncoder


class Feishu(object):

    def __init__(self) -> None:
        self.url_pyger_token = 'https://www.pgyer.com/apiv2/app/getCOSToken'
        self.api_key_pyger = 'fc5921d4b3850ec9b0c8004f76d2c824'
        self.url_pyger_build_info = 'https://www.pgyer.com/apiv2/app/buildInfo'

        self.app_id = 'cli_a3fb53663cf9900d'
        self.app_secret = 'KvRIvxX9dCRlUE7pydGUUgmGYqeCldW1'

        self.url_get_token = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        self.url_get_qr = "https://api.pwmqr.com/qrcode/create"
        self.url_web_hook = 'https://open.feishu.cn/open-apis/bot/v2/hook/86e83fc2-6b37-4060-98ef-8cc9dfc41dca'  #测试免打扰群
        #self.url_web_hook = 'https://open.feishu.cn/open-apis/bot/v2/hook/97697d78-098a-44ba-83c5-ae5232e38aa2'  #android客户端交流群
        self.url_upload_image = "https://open.feishu.cn/open-apis/im/v1/images"

    def get_token(self):  #获取飞书应用token
        headers = {'content-type': 'application/json; charset=utf-8'}
        json = {'app_id': self.app_id, 'app_secret': self.app_secret}
        json_data = requests.post(url=self.url_get_token,
                                  headers=headers,
                                  json=json).json()
        print("获取飞书token:", json_data)
        return json_data['tenant_access_token']

    def get_qr(self, downUrl):  #获取二维码
        params = {'url': downUrl}
        bs = requests.get(url=self.url_get_qr, params=params).content
        return bs

    def get_Img(self, url):
        bs = requests.get(url=url).content
        return bs

    def upload_image(self, token, bs):  #上传图片到飞书
        url = self.url_upload_image
        form = {'image_type': 'message', 'image': (bs)}
        multi_form = MultipartEncoder(form)
        headers = {
            'Authorization': 'Bearer %s' % (token),
        }
        headers['Content-Type'] = multi_form.content_type
        json_data = requests.request("POST",
                                     url,
                                     headers=headers,
                                     data=multi_form).json()
        print('上传图片到飞书:', json_data)
        return json_data['data']['image_key']

    def exec_command(self, command):  #执行os命令
        os.system(command)

    def upload_pgyer(self, file_path, updata_note):
        print('上传apk:', file_path)

        #1.获取token 预上传
        def get_token():
            url = self.url_pyger_token
            header = {'content-type': 'application/x-www-form-urlencoded'}
            body = {
                '_api_key': self.api_key_pyger,
                'buildType': 'android',
                'buildUpdateDescription': updata_note
            }
            json_data = requests.post(url=url, headers=header,
                                      data=body).json()
            print('获取蒲公英token:', json_data)
            return json_data['data']

        #2.上传
        def upload(obj):
            print('蒲公英上传中，请耐心等待...')
            url = obj['endpoint']
            headers = {'enctype': 'multipart/form-data'}
            params = obj['params']
            files = {'file': open(file_path, 'rb')}
            response = requests.post(url=url,
                                     headers=headers,
                                     files=files,
                                     data=params)
            print('蒲公英上传结果:', response.status_code)

        #3.获取发布信息
        def get_app_info(obj):
            print('查询蒲公英上传结果中，等待3s')
            time.sleep(3)  # 先等个几秒，上传完直接获取肯定app是还在处理中~
            url = self.url_pyger_build_info
            params = {
                '_api_key': self.api_key_pyger,
                'buildKey': obj['params']['key']
            }
            response = requests.get(url=url, params=params)
            if (response.status_code == requests.codes.ok):
                pass
            json_data = response.json()
            code = json_data['code']
            if code == 1247 or code == 1246:  # 1246	应用正在解析、1247 应用正在发布中
                return get_app_info(obj)
            else:
                print('蒲公英上传成功:', json_data)
                return json_data['data']

        tokenData = get_token()
        upload(tokenData)
        return get_app_info(tokenData)

    def get_file_list(self, dir, Filelist):  #查找指定文件
        newDir = dir
        if os.path.isfile(dir) and os.path.splitext(dir)[1] == '.apk':
            Filelist.append(os.path.abspath(dir))
        elif os.path.isdir(dir):
            for s in os.listdir(dir):
                newDir = os.path.join(dir, s)
                self.get_file_list(newDir, Filelist)

    def read_json(self, img_key, obj, file_name):  #读取json配置
        des = obj['buildUpdateDescription'].replace('\n', '\\n')
        with open('./card_pyger.json', 'r', encoding='utf-8') as f:
            jsonStr = json.dumps(json.load(f)) % (
                obj['buildName'], img_key, file_name,
                'https://www.pgyer.com/%s' % (obj['buildShortcutUrl']),
                obj['buildVersion'], obj['buildVersionNo'], des)
        print('读取飞书Markdown：', json.loads(jsonStr))
        return jsonStr

    def send_robot_msg(self, card_info):  #发送飞书机器人消息
        webhook = self.url_web_hook
        header = {'Content-Type': 'application/json'}
        body = {'msg_type': 'interactive', 'card': card_info}
        response = requests.post(url=webhook, headers=header, json=body)
        print('发送飞书机器人消息：', response.json())

    def start_pyger(self, server_type, update_note):  #上传蒲公英
        des = '%s\n%s' % (server_type, update_note)
        #寻找apk
        apkList = []
        self.get_file_list('./outputs', apkList)
        apk_file = apkList[0]
        #上传蒲公英得到下载地址
        obj_pyger = self.upload_pgyer(apk_file, des)
        #生成二维码
        bs = self.get_Img(obj_pyger['buildQRCodeURL'])
        #得到飞书token
        token = self.get_token()
        #上传二维码到飞书得到img_key
        img_key = self.upload_image(token, bs)
        #读取飞书markdown配置信息
        card_info = self.read_json(img_key, obj_pyger,
                                   os.path.split(apk_file)[1])
        #发送飞书机器人消息(大功告成)
        self.send_robot_msg(card_info)


Feishu().start_pyger(sys.argv[1], sys.argv[2])
