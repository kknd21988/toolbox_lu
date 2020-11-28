#from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
# from win32com import client
from collections import Iterable
import base64
import hashlib
from fuzzywuzzy import fuzz
import json
import requests
from PIL import ImageGrab
import re
import codecs
import os


def get_files(dir_path, suffixes = ""):
    ret_list = []
    for root, dirs, files in os.walk(dir_path):
        for fpath in files:
            if fpath.endswith(suffixes):
                ret_list.append(os.path.join(root, fpath))
    return ret_list

def get_file_md5(file_path):
    file = open(file_path, 'rb').read()
    md5_hash = hashlib.md5(file).hexdigest()
    return md5_hash

def get_MD5(content):
    '''
    计算内容对应的MD5
    '''
    hash_encoder = hashlib.md5()
    hash_encoder.update(content.encode("utf-8"))
    return hash_encoder.hexdigest()

def get_char_correlation(text_1, text_2):
    '''
    计算字面相似度
    主要为了检测出和原文几乎一样的题目
    '''
    #correlation = fuzz.token_sort_ratio(text_1, text_2)/100.0
    correlation = fuzz.partial_ratio(text_1, text_2)/100.0
    return correlation

def get_all_filenames_under_folder(folder):
    '''
    从请求中，获取文件名
    :return:
    '''
    files_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isdir(file_path):
            tmp_result = get_all_filenames_under_folder(file_path)
            files_list.extend(tmp_result)
        else:
            files_list.append(file_path)

    return files_list

def dump(file_content, file_path):
    '''
    内容写入指定文件
    '''
    _dir = os.path.dirname(file_path)
    if _dir and not os.path.exists(_dir):
        os.makedirs(_dir)
    with open(file_path, 'w') as fout:
        fout.write(file_content)

def flatten_list(in_list):
    out_list = list()
    for item in in_list:
        if(isinstance(item,(list,tuple))):
            out_list.extend(flatten_list(item))
        else:
            out_list.append(item)
    return out_list

def flatten(items):
    """把多层list展平"""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

def dicts_merge(*dicts):
    ret_dict = {}
    for _dict in dicts:
        for key in _dict:
            if key not in ret_dict:
                ret_dict[key] = _dict[key]
            else:
                if type(ret_dict[key]) == dict and type(_dict[key]) == dict:
                    ret_dict[key] = dicts_merge(ret_dict[key], _dict[key])
                else:
                    if not isinstance(ret_dict[key], list):
                        ret_dict[key] = [ret_dict[key]]
                    if not isinstance(_dict[key], list):
                        _dict[key] = [_dict[key]]
                    ret_dict[key].extend(_dict[key])
    return ret_dict

# 状态：已测试
# 功能：合并2个字典。向mainDic中添加已有域的不同值
def merge2Dic(mainDic, minorDic):
    for key, value in minorDic.items():
        if key not in mainDic:
            mainDic[key] = value
        elif isinstance(mainDic[key], type(value)) == False:
            raise Exception("Error: corresponding value is not the same type")
        elif isinstance(mainDic[key], dict):
            merge2Dic(mainDic[key], value)
        elif isinstance(mainDic[key], list):
            mainDic[key] = list(set(mainDic[key]).union(set(value)))
    return mainDic

def get_OCR_result_from_baidu(access_token, excercise_path, source='clipboard'):
    '''
    调用百度OCR API识别剪贴板中图片中的文字
    source:['clipboard', 'local']
    保存图片到excercise_path
    计算md5 hash值
    返回json
    '''
    if source == 'clipboard':
        # 剪贴板中的图片保存到本地
        result = None
        image = ImageGrab.grabclipboard() # 获取剪贴板文件
        image.save(excercise_path)
    elif source == 'local':
        if os.path.isfile(excercise_path) is False:
            return None, None
    # 调用百度 API识别图片
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    # 二进制方式打开图片文件
    f = open(excercise_path, 'rb')
    img = base64.b64encode(f.read())

    params = {"image":img}
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        result = response.json()
    # 计算hash值
    md5 = get_pic_md5(excercise_path)
    # 结果返回
    return result, md5

def remove_files_in_folder(folder_path):
    '''
    清空某个文件夹
    '''
    shutil.rmtree(folder_path) # 能删除该文件夹和文件夹下所有文件
    os.mkdir(folder_path)
    return 0

def json_formatter(json_file):
    '''
    将RE的导出json文件格式化
    '''
    with codecs.open(json_file, 'r', encoding='utf-8') as rdFile:
        content = json.load(rdFile)
    
    json_str = json.dumps(content, indent=4, ensure_ascii=False)
    with codecs.open(json_file, 'w', encoding='utf-8') as wtFile:
        wtFile.write(json_str)
    return content

def get_by_url(folder_path, url):
    '''从url下载文件'''
    if not os.path.exists(folder_path):
        logger.info("Selected folder not exist, try to create it.")
        os.makedirs(folder_path)
    # 下载文件
    logger.info("Try downloading file: {}".format(url))
    filename = url.split('/')[-1]
    filepath = folder_path + '/' + filename
    if os.path.exists(filepath):
        logger.info("File have already exist. skip")
    else:
        try:
            urllib.request.urlretrieve(url, filename=filepath)
        except Exception as e:
            logger.error("Error occurred when downloading file, error message:\n{}".format(traceback.format_exc()))
    return filepath, filename
    
def get_year_month_day(date_str):
    '''
    从日期中获取年、月、日信息
    :return:
    '''
    result = None
    if date_str is not None:
        pattern = re.compile("(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})")
        result = pattern.match(date_str)
        if result is not None:
            result = result.groupdict()
    return result

def trans_English_symbol_to_Chinese_symbol(name_str):
    '''
    把name_str中的英文符号替换为中文符号
    :param name:
    :return:
    '''
    ChineseChar = ['，', '！', '。', '：', '；', '？', '（', '）', '【', '】']
    EnglishChar = [',', '!', '.', ':', ';', '?', '(', ')', '[', ']']  # 与上面的中文列表一一对应
    str_name = str(name_str)
    # 英文换成中文
    for i in range(len(EnglishChar)):
         str_name = str_name.replace(EnglishChar[i], ChineseChar[i])
    return str_name

def trans_Chinese_number_to_English_number(time_str):
    '''
    将字符串中的中文数字转为阿拉伯
    :param time_str:
    :return:
    '''
    result = ""
    numerals_dict = {'零': 0, '〇':0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
                                '十': 10, '百': 100, '千': 1000, '万': 10000, '亿': 100000000}

    for x in time_str:
        if x in numerals_dict:
            result += str(numerals_dict[x])
        else:
            result += x
    return result

def str_contains_keyword_that_exists_in_keywordlist(content_str, keyword_checklist):
    '''

    :param content_str:
    :param keyword_checklist:
    :return:
    '''
    keyword_exist = []
    for keyword in keyword_checklist:
        if keyword in content_str:
            keyword_exist.append(keyword)

    if len(keyword_exist) == 0:
        result = False
    else:
        result = True
    return result, keyword_exist

def remove_continuous_repeat_char(content_str):
    '''
    去除连续的叠字，例如'被被处处罚罚当当事事人人姓姓名名'
    这种情况在识别pdf时经常出现
    但是数字的叠字不能去，例如2020年11月4日 去除叠字就变成2020年1月4日
    :param content_str:
    :return:
    '''
    result = ""
    if len(content_str)!=0:
        content_str_from_1st_remove_last = copy.copy(content_str)[:-1]
        content_str_from_2st = content_str[1:]
        last_char = content_str[-1]
        for forward_char, backward_char in zip(content_str_from_1st_remove_last, content_str_from_2st):
            if forward_char in ['1','2','3','4','5','6','7','8','9','0'] or forward_char != backward_char:
                result += forward_char
            else:
                continue
        result+=last_char
    return result

def get_star_line(star_num):
    '''
    获取指定长度的星号字符串，用于打印log
    :param star_num:
    :return:
    '''
    result = ""
    if isinstance(star_num, int):
        result = '*'*star_num+'\n'
    return result

def longestCommonSequence(str_one, str_two, case_sensitive=True):
    """
    str_one 和 str_two 的最长公共子序列
    :param str_one: 字符串1
    :param str_two: 字符串2（正确结果）
    :param case_sensitive: 比较时是否区分大小写，默认区分大小写
    :return: 最长公共子序列的长度
    """
    len_str1 = len(str_one)
    len_str2 = len(str_two)
    # 定义一个列表来保存最长公共子序列的长度，并初始化
    record = [[0 for i in range(len_str2 + 1)] for j in range(len_str1 + 1)]
    for i in range(len_str1):
        for j in range(len_str2):
            if str_one[i] == str_two[j]:
                record[i + 1][j + 1] = record[i][j] + 1
            elif record[i + 1][j] > record[i][j + 1]:
                record[i + 1][j + 1] = record[i + 1][j]
            else:
                record[i + 1][j + 1] = record[i][j + 1]

    return record[-1][-1]

'''
给视频加字幕
src_mp4 = "test_cases/video/test.mp4"
dst_mp4 = "test_cases/video/test_with_script.mp4"
video = VideoFileClip(src_mp4)
sentences = [("这是个测试",2,5)]
words = [("下面",2.5, 7),
        ("ceshi",5.5, 9),
        ("哈哈",9, 3)]
txts = []

for sentence, start, span in sentences:
    txt = (TextClip(sentence, fontsize=40,
                    font='SimHei', size=(1900,40),
                    align='center', color='black')
                    .set_position((10,900))
                    .set_duration(span).set_start(start))
    txts.append(txt)

left = 800
for index, (word, start, span) in enumerate(words):
    width = 40*len(word)
    txt = (TextClip(word, fontsize=40,
                    font='SimHei', size=(width,40),
                    align='center', color='black')
                    .set_position((left,900))
                    .set_duration(span).set_start(start))
    txts.append(txt)
    left += width
# 合成视频，写入文件
video = CompositeVideoClip([video, *txts])
video.write_videofile(dst_mp4)
'''