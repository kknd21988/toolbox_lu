# 用户的flash的相关字段
create table flash_pool(
ID VARCHAR(32),
detail VARCHAR(2048),
context_text VARCHAR(1024),
context_pic VARCHAR(256),
source VARCHAR(512),
author VARCHAR(64),
first_insert_time VARCHAR(64),
last_edit_time VARCHAR(64),
other VARCHAR(1024)
)

# 用户上传的题目图片相关字段
create table excercise_pool(
hash VARCHAR(64),   #图片内容对应的hash码
insert_timestamp VARCHAR(64),	#上传时间戳
insert_time VARCHAR(64),	#上传时间
content VARCHAR(2048),   #图片OCR后的内容
pic_name VARCHAR(128),	#图片名称
user_analysis VARCHAR(2048) # 用户对题目的解析
)