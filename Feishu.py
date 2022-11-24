import json
import requests
import os
import sys
import time
from requests_toolbelt import MultipartEncoder


class Feishu(object):

    def __init__(self) -> None:
        self.app_id = 'cli_a3fb53663cf9900d'
        self.app_secret = 'KvRIvxX9dCRlUE7pydGUUgmGYqeCldW1'

        self.url_get_token = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        self.url_get_qr = "https://api.pwmqr.com/qrcode/create"
        self.url_web_hook = 'https://open.feishu.cn/open-apis/bot/v2/hook/86e83fc2-6b37-4060-98ef-8cc9dfc41dca'
        self.url_upload_image = "https://open.feishu.cn/open-apis/im/v1/images"

        oss_bucket = 'guapy-file'
        self.oss_path = '/testfile/'
        self.url_oss_path = 'oss://%s%s' % (oss_bucket, self.oss_path)
        self.url_oss_bucket_domain = 'https://dl.whyax.cn'
        pass

    def get_token(self):  #获取飞书应用token
        headers = {'content-type': 'application/json; charset=utf-8'}
        json = {'app_id': self.app_id, 'app_secret': self.app_secret}
        token = requests.post(url=self.url_get_token,
                              headers=headers,
                              json=json).json()['tenant_access_token']
        print("token=", token)
        return token

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
        response = requests.request("POST",
                                    url,
                                    headers=headers,
                                    data=multi_form)
        print(response.headers['X-Tt-Logid'])  # for debug or oncall
        print(response.content)  # Print Response
        img_key = response.json()['data']['image_key']
        print('image_key = ', img_key)
        return img_key

    def exec_command(self, command):  #执行os命令
        os.system(command)

    def upload_oss(self, file_path):  #上传app到oss
        self.exec_command('ossutil64.exe cp %s %s' %
                          (file_path, self.url_oss_path))
        print('finish os command')
        file_name = os.path.split(file_path)[1]
        downloadUrl = '%s%s%s' % (self.url_oss_bucket_domain, self.oss_path,
                                  file_name)
        return downloadUrl

    def upload_pgyer(self, file_path):

        #1.获取token 预上传
        def get_token():
            url = 'https://www.pgyer.com/apiv2/app/getCOSToken'
            header = {'content-type': 'application/x-www-form-urlencoded'}
            body = {
                '_api_key': 'b26f6a1f32a0379132bab27c30210c1b',
                'buildType': 'android',
                'buildUpdateDescription': "测试脚本发布"
            }
            response = requests.post(url=url, headers=header, data=body)
            print('get_token==>>', response.content)
            return response.json()['data']

        #2.发布
        def upload(obj):
            url = obj['endpoint']
            headers = {'enctype': 'multipart/form-data'}
            params = obj['params']

            files = {'file': open(file_path, 'rb')}
            print(url)
            print('upload==>>', params)
            response = requests.post(url=url,
                                     headers=headers,
                                     files=files,
                                     data=params)
            print('upload==>>', response.status_code)

        #3.获取发布信息
        def get_app_info(obj):
            print('sleep 3s')
            time.sleep(3)  # 先等个几秒，上传完直接获取肯定app是还在处理中~
            url = 'https://www.pgyer.com/apiv2/app/buildInfo'
            params = {
                '_api_key': 'b26f6a1f32a0379132bab27c30210c1b',
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
                print(json_data)
                return json_data['data']['buildQRCodeURL']

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

    def read_json(self, img_key, down_url, update_note):  #读取json配置
        print('downloadUrl = ', down_url)
        with open('./card.json', 'r', encoding='utf-8') as f:
            jsonStr = json.dumps(
                json.load(f)) % (img_key, down_url, update_note)
        print(jsonStr)
        return jsonStr

    def send_robot_msg(self, card_info):  #发送飞书机器人消息
        webhook = self.url_web_hook
        header = {'Content-Type': 'application/json'}
        body = {'msg_type': 'interactive', 'card': card_info}
        response = requests.post(url=webhook, headers=header, json=body)
        print(response.content)

    def start_oss(self):  #上传oss
        #寻找apk
        apkList = []
        self.get_file_list('./outputs', apkList)
        #上传oss得到下载地址
        down_url = self.upload_oss(apkList[0])
        #生成二维码
        bs = self.get_qr(down_url)
        #得到飞书token
        token = self.get_token()
        #上传二维码到飞书得到img_key
        img_key = self.upload_image(token, bs)
        #读取飞书markdown配置信息
        card_info = self.read_json(img_key, down_url, sys.argv[1])
        #发送飞书机器人消息(大功告成)
        self.send_robot_msg(card_info)
        pass

   


Feishu().start_oss()