from win32com import client
import pdfplumber
import xlrd
import xlwt
from pdf2txt.pdf2string import pdf_recongnition

def doc2pdf(doc_name, pdf_name):
    # docx转pdf：时灵时不灵
    # wordname = r'D:\User\Documents\PycharmProjects\test\data\roamedit_record\Neo4j权威指南.20200821221200.docx'
    # pdfname = r'D:\User\Documents\PycharmProjects\test\data\roamedit_record\Neo4j权威指南.20200821221200.pdf'
    # doc2pdf(wordname, pdfname)
    try:
        word = client.DispatchEx("Word.Application")
        if os.path.exists(pdf_name):
            os.remove(pdf_name)
        worddoc = word.Documents.Open(doc_name,ReadOnly=1)
        worddoc.SaveAs(pdf_name, FileFormat = 17)
        worddoc.Close()
        return pdf_name
    except Exception as e:
        print(e)
        return 1

def templateDoc2pdf(doc_absolute_name, pdf_absolute_name):
    """
    :word文件转pdf
    有个要注意的点，输入的两个参数都要是绝对地址，如果用相对地址，方法会报错
    :param doc_name word文件名称
    :param pdf_name 转换后pdf文件名称
    """
    word = client.DispatchEx("Word.Application")
    if os.path.exists(pdf_absolute_name):
        os.remove(pdf_absolute_name)
    worddoc = word.Documents.Open(doc_absolute_name, ReadOnly=1)
    worddoc.SaveAs(pdf_absolute_name, FileFormat=17)
    worddoc.Close()
    return 0

def templateExcel2pdf(excel_absolute_name, pdf_absolute_name):
    """
    :excel文件转pdf
    有个要注意的点，输入的两个参数都要是绝对地址，如果用相对地址，方法会报错
    :param excel_absolute_name excel
    :param pdf_absolute_name 转换后pdf文件名称
    """
    xlApp = client.Dispatch("Excel.Application")
    if os.path.exists(pdf_absolute_name):
        os.remove(pdf_absolute_name)
    # books = xlApp.Workbooks.Open(input)
    # ws = books.Worksheets[0]
    # ws.Visible = 1
    # ws.ExportAsFixedFormat(0, output)

    xlApp.Visible = False
    xlApp.DisplayAlerts = 0
    books = xlApp.Workbooks.Open(excel_absolute_name, False)
    books.ExportAsFixedFormat(0, pdf_absolute_name)
    books.Close(False)
    xlApp.Quit()
    return 0

def search_in_word_and_process(word_path, compiled_pattern):
    '''
    在word中搜索指定模式
    compiled_pattern为已编译的模式，例如re.compile('\\[\\[(.*?)\\]\\]')
    '''
    quelified_result = set([])
    document = Document(word_path)
    for p in document.paragraphs:
        match_pattern = compiled_pattern.findall(p.text)
        if '完全垄断市场' in match_pattern:
            a=1
        if len(match_pattern) != 0:
            quelified_result = quelified_result.union(set(match_pattern))
    return quelified_result

def get_word_from_tree(tree_data, word_object, heading_level):
    '''
    把tree写入word，当前tree的根节点标题层级为heading_level
    1.一个block，如果有children，就是一级标题
    2.block如果没有children，就是段落

    example:
    # SCIPT1:把path中的内容打印到word中。
    # path = 'data/roamedit_record/Neo4j权威指南.20200821221200.json'
    # save_file = 'data/roamedit_record/Neo4j权威指南.20200821221200.docx'
    # document = Document()
    # with open(path, 'r', encoding='utf-8') as jsonfile:
    #     data = json.load(jsonfile)
    #     tree = get_tree_from_json_RoamEdit(data)
    #     get_word_from_tree(tree, document, heading_level=0)
    #     document.save(save_file)
    '''
    text=""
    tree_data.show()
    root = tree_data.root
    root_node = tree_data.get_node(root)
    root_content = root_node.data
    text_temp = root_content.get('STRING')
    if text_temp is not None:
        text += text_temp
    if root_node.is_leaf():
        # 找到所有普通文字run
        ordinarychar_run_list = re.split(r'\[\[.*?\]\]',text_temp)
        # 找到所有topic的run[[]]
        topic_run_list = re.findall(r'\[\[(.*?)\]\]',text_temp)
        assert len(ordinarychar_run_list) == len(topic_run_list)+1
        # 依次添加run
        for i in range(len(topic_run_list)):
            # 先添加普通文字run
            paragraph = word_object.add_paragraph()
            paragraph.text = ordinarychar_run_list.pop(0)
            # 后添加topic run
            paragraph = word_object.add_paragraph()
            filename = topic_run_list.pop(0)
            url = "file:///D:/User/Documents/PycharmProjects/test/data/roamedit_record/topic_pdf/{filename}.docx".format(filename=filename)
            add_hyperlink(paragraph, url, filename, color=None, underline=True)
            # run = paragraph.add_run()
            # run.text = topic_run_list.pop(0)
            # run.font.underline = True
            # run.font.bold = True
        # 添加最后一段文字
        if len(ordinarychar_run_list) != 0:
            paragraph = word_object.add_paragraph()
            paragraph.text = ordinarychar_run_list.pop(0)

    else:
        word_object.add_heading(text_temp, level=heading_level)
        if root_content.get('CHILDREN') is not None:
            for child_uid in root_content.get('CHILDREN'):
                #child_uid = child.get('UID')
                try:
                    child_tree = tree_data.subtree(child_uid)
                    child_level = heading_level+1
                    text_child = get_word_from_tree(child_tree, word_object, child_level)
                    text += text_child
                except Exception as e:
                    a=1
    return text

def analyze_table_in_pdf(pdf_path):
    '''
    把一张pdf中的表，解析为一个字典
    能处理跨页情况
    :param pdf_path
    :return:
    '''
    result = {}
    table_detect = None
    previous_key = ""
    previous_value = ""
    key = ""
    value = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            #上一页的最后一对key-value
            previous_key = key
            previous_value = value
            first_meaningful_line = True
            # table = page.extract_table(table_settings={'vertical_strategy':"lines",'horizontal_strategy':"lines"})    # 找到最大的表格
            table = page.extract_table()  # 找到最大的表格
            if table is None:
                table_detected = False
            else:
                table_detected = True
                for line_content in table:
                    tmp_key, tmp_value, msg = get_table_key_value_in_list(line_content)  # 发现有的pdf的key出现叠字，如'被被处处罚罚当当事事人人姓姓名名'
                    if len(tmp_key) == 0 and len(tmp_value) == 0:
                        continue    # 空行
                    else:
                        key = tmp_key   # 防止上一页最后两行是空行
                        value = tmp_value
                        if first_meaningful_line == True:
                            # 新的一页第一个有效行，要考虑key或value跨页的情况
                            if len(key) == 0 or len(value) == 0:
                                # 删除部分key或value的项
                                if previous_key in result:
                                    del result[previous_key]
                                # 跨页都需要先拼接
                                previous_key += key
                                previous_value += value
                                logger.debug("当前行是跨页行，key={}，value={}".format(key, value))
                                # 更新合并后的键值对
                                result.update({previous_key: previous_value})
                                first_meaningful_line = False
                            else:
                                # key和value都不跨页（其实还可能是key和value都跨页了，这种现在不能区别）
                                logger.debug("在当前行找到key：{}，value：{}，reason：{}".format(key, value, msg))
                                result.update({key: value})
                                first_meaningful_line = False
                        else:
                            # key和value都不跨页（其实还可能是key和value都跨页了，这种现在不能区别）
                            logger.debug("在当前行找到key：{}，value：{}，reason：{}".format(key, value, msg))
                            result.update({key: value})
                            first_meaningful_line = False

    return result, table_detected

class lu_pdf_handler():
    # pdf处理的类，基于pdfplumber
    def __init__(self, pdf_path=None):
        self.pdf_path = pdf_path
        self.pdf_name = None
        # 打开文件对象
        if self.pdf_path is not None:
            self.pdf_obj = pdfplumber.open(self.pdf_path)
            # 获取文件名
            [_,filename]=os.path.split(self.pdf_path)
            self.pdf_name, _ = os.path.splitext(filename)
        else:
            self.pdf_obj = None

    def __del__(self):
        # 对象不再使用时，自动运行析构函数
        print("对象{}销毁".format(self.__class__.__name__))
        del self.pdf_obj

    def find_page_border(self, pdf_page, show=True):
        '''
        根据pdf中划线边界，返回区域坐标
        默认边界为页面的四条边
        测试OK
        '''
        # 默认边界
        if pdf_page.bbox is not None:
            default_x0 = float(pdf_page.bbox[0])
            default_y0 = float(pdf_page.bbox[1])
            default_x1 = float(pdf_page.bbox[2])
            default_y1 = float(pdf_page.bbox[3])
        else:
            print("本页的bbox为None")
        # 检测4条边界:类型为Line & 颜色为黑色
        page_border_list = [x for x in pdf_page.annots if x['data']['Subtype'].name == 'Line' and x['data']['C'] == [0,0,0]]
        # 区分上下左右边界
        top_border = None
        bottom_border = None
        left_border = None
        right_border = None
        vertical_lines = []
        horizontal_lines = []
        result = {}
        #1. 根据斜率分为水平线 & 垂直线两组
        for line in page_border_list:
            slope = get_slope(line['x0'],line['y0'],line['x1'],line['y1'])
            mid_point = get_mid_point(line['x0'],line['y0'],line['x1'],line['y1'])
            line['mid_point'] = mid_point
            if abs(slope)>30:
                # 垂直线
                vertical_lines.append(line)
            elif abs(slope)<0.1:
                # 水平线
                horizontal_lines.append(line)
            else:
                print("既非垂直，又非水平")
        #2. 垂直线组内，中点在左的是左边界，终点在右的为右边界
        if len(vertical_lines) == 2:
            temp = sorted(vertical_lines, key=lambda x:x['mid_point']['mid_x'], reverse=False)
            result['left_border'] = temp[0]['mid_point']['mid_x']
            result['right_border'] = temp[-1]['mid_point']['mid_x']
        else:
            result['left_border'] = default_x0
            result['right_border'] = default_x1
        #3. 水平线组内，中点在上的是上边界，终点在下的为下边界
        if len(horizontal_lines) == 2:
            temp = sorted(horizontal_lines, key=lambda x:x['mid_point']['mid_y'], reverse=False)
            result['lower_border'] = temp[0]['mid_point']['mid_y']
            result['upper_border'] = temp[-1]['mid_point']['mid_y']
        else:
            result['lower_border'] = default_y0
            result['upper_border'] = default_y1
        return result
        

        pass

    def find_page_drawing(self, pdf_page):
        '''
        根据pdf中方框，返回图片区域坐标（不需OCR）
        '''
        # 检测4条边界:类型为Line & 颜色为黑色
        # 测试OK
        drawing_border_list = [x for x in pdf_page.annots if x['data']['Subtype'].name == 'Square' and x['data']['C'] == [0,0,0]]
        return drawing_border_list

    def cut_page_text_Region(self, pdf_page, border_region=None, drawing_region=None):
        '''
        在pdf边框内部，去除不需OCR的图片区域，剩下的连通域即为需要进行OCR提取文字的区域，截图出来
        最终截图还是一个矩形，但是不用OCR的区域（例如图片区域）填充为黑色。
        测试OK
        '''
        img = pdf_page.to_image(resolution=400)
        # 根据用户画出的边界，截取区域
        result = self.find_page_border(pdf_page)
        bounding_box = (result['left_border'],\
                        float(pdf_page.height)-result['upper_border'],\
                        result['right_border'],\
                        float(pdf_page.height)-result['lower_border'])
        # 上边界与page顶线间的区域涂黑
        upper_filter_region = (type(pdf_page.height).from_float(result['left_border']),\
                            type(pdf_page.height).from_float(0),\
                            type(pdf_page.height).from_float(result['right_border']),\
                            pdf_page.height-type(pdf_page.height).from_float(result['upper_border']))
        img = img.draw_rect(upper_filter_region, fill=(0,0,0))
        img.save("page_cut.png", format="PNG")
        # 下边界与page底线间的区域涂黑
        lower_filter_region = (type(pdf_page.height).from_float(result['left_border']),\
                            pdf_page.height-type(pdf_page.height).from_float(result['lower_border']),\
                            type(pdf_page.height).from_float(result['right_border']),\
                            pdf_page.height)
        img = img.draw_rect(lower_filter_region, fill=(0,0,0))
        img.save("page_cut.png", format="PNG")
        # 左边界与page左边线间的区域涂黑
        left_filter_region = (type(pdf_page.height).from_float(0),\
                            type(pdf_page.height).from_float(0),\
                            type(pdf_page.height).from_float(result['left_border']),\
                            pdf_page.height)
        img = img.draw_rect(left_filter_region, fill=(0,0,0))
        img.save("page_cut.png", format="PNG")
        # 右边界与page右边线间的区域涂黑
        right_filter_region = (type(pdf_page.height).from_float(result['right_border']),\
                            type(pdf_page.height).from_float(0),\
                            pdf_page.width,\
                            pdf_page.height)
        img = img.draw_rect(right_filter_region, fill=(0,0,0))
        # page_cut = pdf_page.within_bbox(bounding_box)
        # img = page_cut.to_image(resolution=400)
        # img.save("page_cut.png", format="PNG")
        img.save("page_cut.png", format="PNG")
        # 可能有多个drawing区域
        result = self.find_page_drawing(pdf_page)
        for index, region in enumerate(result):
            bounding_box = (region['x0'],region['top'],\
                            region['x1'],region['bottom'])
            # 根据用户划出的框，截取不需OCR的图片区域并保存
            page_cut = pdf_page.crop(bounding_box)
            img_cut = page_cut.to_image(resolution=400)
            img_cut.save("drawing_P{page}_drawing_No{index}.png".format(page=pdf_page.page_number,index=index), format="PNG")
            # 根据用户划出的框，将框内区域涂黑
            img = img.draw_rect(bounding_box, fill=(0,0,0))    #COLORS.BLUE
        # 保存最终版
        save_path = "data/pdf_pages/page{pageNo}_filtered.png".format(pageNo=pdf_page.page_number)
        img.save(save_path, format="PNG")
        return save_path

    def get_user_comment(self, pdf_page):
        '''
        提取用户的批注，并和页码联系在一起
        '''
        result = []
        for annotation in pdf_page.annots:
            if annotation['data']['Type'].name == 'Annot' and \
                annotation['data']['Subtype'].name == 'FreeText':
                    result.append(annotation['contents'])
        return result

    def build_full_notes(self):
        '''
        建立全量笔记：页码——文字的映射关系。存放在ES，或者mysql中
        测试OK
        '''
        all_content= ''
        all_comments = ''
        for page in self.pdf_obj.pages:
            # 获取pdf的有效区域
            path = self.cut_page_text_Region(page)
            # 完成OCR
            OCR_result, md5 = get_OCR_result_from_baidu(baidu_access_token, path, source='local')
            content = '\r\n'.join([x['words'] for x in OCR_result['words_result']])
            nonempty_char = re.sub('\s','',content)
            all_content += nonempty_char
            nonempty_char_num = len(nonempty_char)
            print(content)
            # 获取用户批注
            user_comment = '\r\n'.join(self.get_user_comment(page))
            nonempty_comment = re.sub('\s','',user_comment)
            all_comments += nonempty_comment
            # 建立页码——文字、用户批注的映射关系
            connector = engine
            table_name = 'pdf_record'
            timestamp = datetime.datetime.now()
            time = datetime.datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S')
            col = ['pdf_name', 'page_number', 'content','nonempty_char_num','drawing', 'user_comment', 'user_comment_nonempty', 'insert_timestamp','insert_time']
            df = pd.DataFrame([[self.pdf_name, page.page_number, content, nonempty_char_num, '', user_comment, nonempty_comment, timestamp, time]],
                            columns=col)
            pd.io.sql.to_sql(df, table_name, con=connector, index=False, if_exists='append')

        # 建立书名——内容、用户批注的对应关系
        table_name = 'pdf_book_content'
        col = ['pdf_name', 'content', 'user_comment']
        df = pd.DataFrame([[self.pdf_name, all_content, all_comments]], columns=col)
        pd.io.sql.to_sql(df, table_name, con=connector, index=False, if_exists='append')

        return 0

    def get_page_no(self, char_index, char_page_distribution):
        '''
        功能：根据某个字在全文中的序号返回所在页码，以及在该页中的大概位置，例如80%
        char_index:某个字在全文中的序号
        char_page_distribution：各页的文字数量分布，
            例如[10,13,5]代表第一页10个字，第二页13个字，第三页5个字
        返回：
        char_index在char_page_distribution的第几行
        测试OK
        '''
        accumulated_count = 0
        result_index = -1
        for index_, num in enumerate(char_page_distribution):
            start_ = accumulated_count + 1
            accumulated_count = start_+num-1
            end_ = accumulated_count
            if char_index >= start_ and char_index <= end_:
                # 所在页的序号
                page_index = index_
                # 在该页中的大概位置
                position = (char_index-start_+1)/(end_-start_+1)
                break
        return page_index, position

    def find_sequence_pageNo(self, content):
        '''
        在全量笔记中搜索某段文字content。思路是：
        1.在建立全量笔记的时候，就统计出每一个page中含有的非空字符；
          这样，我就能计算出每一页的字符范围：page1——字符1~100，page2——字符101到150,...
        2.在搜索时，每一定页数（例如10页）的所有内容拼接起来，
          用str.index搜索到这个字符串的起始位置
          起始位置+字符串长度=终止位置
        3.根据起始位置和终止位置，可以计算出字符串在哪一页，或者跨页了
        4.最好还能返回字符串的上下文，或者大致位置（例如该页80%处），帮助用户快速找到对应位置。
        测试OK
        '''
        result = []
        table = 'pdf_book_content'
        sql = 'select pdf_name, locate(\'{content}\', content) as start_point from {table}'.format(content=content, table=table)
        tempDF = pd.read_sql_query(sql, engine)
        # 2.找到字符串的index
        for index, row in tempDF.iterrows():
            pdf_name = row['pdf_name']
            start_ = row['start_point']
            end = start_ + len(re.sub('\s','',content)) - 1
            if start_ >0:
                # 本书存在content匹配
                table_in = 'pdf_record'
                sql_in = 'select pdf_name, page_number, nonempty_char_num from {table} where pdf_name = \'{pdf_name}\''.format(content=content, table=table_in, pdf_name=pdf_name)
                tempDF_in = pd.read_sql_query(sql_in, engine)
                if len(tempDF_in) == 0:
                    print("不存在这本pdf")
                else:
                    char_distribution = [int(x) for x in tempDF_in['nonempty_char_num']]
                    # 起点页码，起点在该页中的位置
                    start_index, position_in_start_page = self.get_page_no(start_, char_distribution)
                    start_page = tempDF_in['page_number'][start_index]

                    # 终点页码，终点在该页中的位置
                    end_index, position_in_end_page = self.get_page_no(end, char_distribution)
                    end_page = tempDF_in['page_number'][end_index]
                # 3.计算出搜索字符串的起始和终止位置（哪本书，第几页，约%多少处）
                found_occurence = {'pdf_name':pdf_name,\
                    'start_page_no':start_page,\
                    'position_in_start_page':position_in_start_page,\
                    'end_page_no':end_page,\
                    'position_in_end_page':position_in_end_page}
                result.append(found_occurence)
        return result

    def find_content_in_user_comment_pageNo(self, content):
        '''
        在用户批注中搜索，并返回该批注的页码
        测试OK
        '''
        result = []
        table_in = 'pdf_record'
        sql_in = 'select pdf_name, page_number from {table} where user_comment_nonempty like \'%%{content}%%\''\
            .format(table=table_in, content=content)
        tempDF_in = pd.read_sql_query(sql_in, engine)
        if len(tempDF_in) == 0:
            print("在用户注释中没找到指定内容")
            pdf_name = ''
            start_page = -1
        else:
            for index, row in tempDF_in.iterrows():
                pdf_name = row['pdf_name']
                start_page = row['page_number']
                # 3.计算出搜索字符串的起始和终止位置（哪本书，第几页，约%多少处）
                found_occurence = {'pdf_name':pdf_name,'start_page_no':start_page}
                result.append(found_occurence)

        return result

def analyzePDF_step1_lineInfo(pdfPath):
    '''
    对pdf进行初步解析，将解析结果存入字典
    :param pdfPath:
    :return:
    pdfDic = {int pageIndex: # pageIndex
              {
                  'lineDic': {},  # {y0:{'element':list,'content':str}}
                  'DiseaseRegion': {}  # {x0:float,y0:float,x1:float,y1:float,bboxList[(4-tuple),...]}
              }
              }
    '''
    pdfDic = {}
    with pdfplumber.open(pdfPath) as pdf:
        for i, page in enumerate(pdf.pages):
            pageNo = i+1
            pdfDic[pageNo] = {}
            pdfDic[pageNo]['pdfplumberPage'] = page
            chars = page.chars
            # 1.字符组合成行：所有纵坐标一样的char形成line
            lineDic = {}
            for char in chars:
                # 把每个char归到各个行中
                y0 = float(char['y0'])
                hit = 0
                for key in lineDic.keys():
                    if abs(y0 - key) < float(char['height']) * 0.3:
                        hit += 1
                        lineDic[key]['element'].append(char)
                if hit == 0:
                    lineDic[y0] = {'element': []}
                    lineDic[y0]['element'].append(char)
            resultLineDic = {}
            for key, line in lineDic.items():
                text = ''
                temp = sorted(line['element'], key=lambda x:x['x0'], reverse=False)
                leftBound = temp[0]['x0']  # 最左字符x0
                rightBound = temp[-1]['x1']  # 最右字符x1
                lowerBound = None
                upperBound = None
                for char in line['element']:
                    text += char['text']
                    lowerBound = char['y0'] if lowerBound == None or char['y0'] < lowerBound else lowerBound
                    upperBound = char['y1'] if upperBound == None or char['y1'] > upperBound else upperBound
                text = re.sub(r'[\s]+', '', text)
                if len(text) != 0:
                    lineDic[key]['content'] = text
                    lineDic[key]['x0'] = leftBound
                    lineDic[key]['x1'] = rightBound
                    lineDic[key]['y0'] = lowerBound
                    lineDic[key]['y1'] = upperBound
                    resultLineDic[key] = lineDic[key]
            pdfDic[pageNo]['lineDic'] = resultLineDic

    return pdfDic

def remove_heading_index(heading):
    '''
    把（一）或一、或一  或第一部分 第一节 第一章这种格式都去掉
    '''
    result = re.sub(r'第[零一二三四五六七八九十](部分|章|节)','',heading)
    result = re.sub(r'[\（\(]+[零一二三四五六七八九十0-9]+[\）\)]+', '', result)
    result = re.sub(r'[零一二三四五六七八九十0-9]*[，,、\s\t]+', '', result)
    result = result.strip()
    return result

def get_word_headings(word_path):
    '''
    获取word各级标题
    update 2020-10-09:把（一）或一、或一  这种格式都去掉
    :param word_path:
    :return:
    '''
    document = Document(word_path)
    heading_dic = {}
    # 遍历word
    for paragraph in document.paragraphs:
        style = paragraph.style.name
        text = paragraph.text.strip()
        text = remove_heading_index(text) # 取出格式字符
        if len(text) == 0:
            continue
        if 'Heading' not in style:
            # 排除没有Heading关键字的其他格式
            continue
        if style != 'Normal':
            if style not in heading_dic:
                heading_dic[style] = []
            else:
                heading_dic[style].append(text)
    return heading_dic

def get_excel_row_number(excel_path, sheet_index=0):
    '''
    获取excel中有多少行
    :param excel_path:
    :return:
    '''
    try:
        xls = xlrd.open_workbook(excel_path)
        sheet = xls.sheets()[sheet_index]
        row_number = sheet.nrows
    except Exception as e:
        print(traceback.format_exc())
        row_number = -1
    return row_number

def create_excel(excel_path, header=None):
    '''
    新建一个excel文件
    '''
    result = -1
    if os.path.exists(excel_path) == False:
        workbook = xlwt.Workbook(encoding='utf-8')       #新建工作簿
        sheet1 = workbook.add_sheet("Sheet1")          #新建sheet
        if header is not None:
            for i in range(len(header)):
                sheet1.write(0,i, label = header[i])
        workbook.save(excel_path)   #保存
        result = 0
    else:
        result = 1
    return result

def extract_text_from_pdf(pdf_path, image_dir):
    '''
    【测试OK】
    从pdf中提取文字内容（先尝试直接提取，如果失败，则用OCR提取）
    :param pdf_path:
    :param image_dir:
    :return:
    '''
    pure_text = []
    need_OCR = False    # 是否需要OCR提取内容
    try:
        # 1.尝试按照文字版pdf提取内容
        try:
            begin_time = datetime.datetime.now()
            pdfDic = analyzePDF_step1_lineInfo(pdf_path)
            end_time = datetime.datetime.now()
            time_span = (end_time - begin_time).total_seconds()
            logger.info("从pdf中直接提取文字成功，共{}页，耗时{}秒".format(len(pdfDic), time_span))
        except Exception as e:
            msg = "pdf{path}解析失败：\r\n{err}".format(path=pdf_path, err=e)
            logger.error(msg)
            raise Exception(msg)
        total_char = 0
        for pageNo, page in pdfDic.items():
            text = page['pdfplumberPage'].extract_text()
            if text is not None:
                pure_text.append(text)
                total_char += len(text)
                logger.debug("第{}页提取文字共{}字".format(pageNo, len(text)))
            else:
                logger.info("此文件（{file_name}）第{pageNo}页直接提取文字失败"\
                             .format(file_name=pdf_path, pageNo=pageNo))
                need_OCR = True
                break
        logger.debug("直接提取文字共{}字".format(total_char))

        # 2.如果无法提取出文字，调用OCR识别
        if need_OCR == True:
            logger.info("尝试用OCR提取文件内容...")
            if not os.path.exists(image_dir):
                os.mkdir(image_dir)

            begin_time = datetime.datetime.now()
            result_dict = pdf_recongnition(pdf_path, image_dir, first_page=pageNo)
            end_time = datetime.datetime.now()
            time_span = (end_time-begin_time).total_seconds()
            logger.info("OCR成功，共耗时{}秒".format(time_span))

            # 转换为统一格式
            for _, value in result_dict.items():
                pure_text.append(''.join(value))
    except Exception as e:
        msg = "从此文件{file_name}中提取文字失败".format(file_name=pdf_path)
        logger.error(msg)
        raise Exception(msg)

    return pure_text