# -*- coding: utf-8 -*-
# flake8: noqa
from qiniu import Auth, put_file, etag, put_data, BucketManager
import os
import qiniu.config
# 需要填写你的 Access Key 和 Secret Key
from settings import Config
import random

def upload_qiniu(fileStorage):

    access_key = 'l9uurBEtx0HG59BDx9Xk51Ez5It1j8dBSDMH1tSw'
    secret_key = '5SScrjrooc6ytuPCHAyZQKwXmy9ffzVbPLbtSjZB'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'myblogtest124'
    # 上传后保存的文件名
    file_name = fileStorage.filename
    key = str(random.randint(1,1000)) + file_name
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    # 要上传文件的本地路径
    ret , info = put_data(token,key,fileStorage.read())
    return ret,info

def delete_qiniu(file_name):
    access_key = 'l9uurBEtx0HG59BDx9Xk51Ez5It1j8dBSDMH1tSw'
    secret_key = '5SScrjrooc6ytuPCHAyZQKwXmy9ffzVbPLbtSjZB'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    # 初始化BucketManager
    bucket = BucketManager(q)
    # 你要测试的空间， 并且这个key在你空间中存在
    bucket_name = "myblogtest124"
    key = file_name
    # 删除bucket_name 中的文件 key
    ret, info = bucket.delete(bucket_name, key)
    return info
