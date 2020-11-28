import pandas as pd
import random,string
import datetime
from sqlalchemy import create_engine

# 数据库配置
db_config = {'mysql_user':'root',\
             'mysql_password':'tongxin2007',\
             'mysql_hostname':'localhost',\
             'mysql_port':'3306',\
             'mysql_schema':'thought_flow',\
             'mysql_charset':'utf8'}

# 连接数据库
engine = create_engine("mysql+pymysql://{user}:{password}@{hostname}:{port}/{schema}?charset={charset}".format \
                           (user=db_config['mysql_user'], password=db_config['mysql_password'],
                            hostname=db_config['mysql_hostname'],
                            port=db_config['mysql_port'], schema=db_config['mysql_schema'],
                            charset=db_config['mysql_charset']))

def genRandomString(slen=10):
    return ''.join(random.sample(string.ascii_letters + string.digits, slen))

def check_if_ID_in_table(ID, table_name, engine, field='ID'):
    '''
    查询数据库中table_name中是否存在某ID
    默认匹配ID字段
    '''
    existed = False
    sql = 'select * from {} where {}=\'{}\''.format(table_name, field, ID)
    df = pd.read_sql_query(sql, engine)
    if len(df) == 0:
        existed = False
    else:
        existed = True
    return existed


def generateKnowledgeID(slen=10):
    '''
    产生一个在id_to_table中不存在的ID
    :param slen: ID的长度
    :return:
    '''
    existed = True
    while existed == True:
        # 产生一个新的ID
        ID = genRandomString(slen)
        # 在数据库中查询该ID是否存在。根据存在情况修改existed
        existed = check_if_ID_in_table(ID, 'flash_pool', engine)
    return ID

def to_sql_wrapper(self, frame, tableName, con, index, if_exists, style):
    '''

    :param frame:
    :param tableName:
    :param con:
    :param index:
    :param if_exists:
    :return:
    '''
    # 0.记录数据来源、和时间
    #now = datetime.datetime.now()
    #now = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
    # 1.产生ID、infoSource、time列
    dataNum = len(frame)
    ID = set()
    if style == 'oneRow_oneID':  # dataframe中一行对应一个ID
        while len(ID) < dataNum:
            ID.add(self.generateKnowledgeID())
        ID = list(ID)
        ID_table = [[x, tableName] for x in ID]
    elif style == 'wholeDataFrame_oneID':  # dataframe中所有行对应一个ID
        ID = self.generateKnowledgeID()
        ID_table = [[ID, tableName]]
    else:
        a = 1
    # 2.在原frame中插入ID列
    frame.insert(0, 'ID', ID)
    # 3.在全局的索引表中维护新增知识的索引（全局唯一）
    # ID_tableFrame = pd.DataFrame(ID_table, columns=['ID', '所在表名', 'insertTime', 'infoSource'])
    # pd.io.sql.to_sql(ID_tableFrame, 'id_to_table', con=con, index=index, if_exists=if_exists)
    # 4.在指定表中新增知识
    pd.io.sql.to_sql(frame, tableName, con=con, index=index, if_exists=if_exists)
    return ID, frame

def deleteKnowledge(self, ID):
    '''
    根据ID删除对应的知识
    :param ID:
    :return:
    '''
    status = 0
    # 1.查数据库中是否有该ID：有就删除，没有要反馈给用户
    sql = 'select * from id_to_table where ID = \'{}\''.format(ID)
    df = pd.read_sql_query(sql, self.engine)
    if len(df) == 0:
        status = -1
    else:
        # 删除知识点
        tableName = df['所在表名'][0]
        sql_deleteTable = 'delete from {} where ID=\'{}\''.format(tableName, ID)
        pd.io.sql.execute('SET SQL_SAFE_UPDATES = 0;', self.engine)
        pd.io.sql.execute(sql_deleteTable, self.engine)

        # 删除索引
        sql_delete = 'delete from id_to_table where ID=\'{}\''.format(ID)
        pd.io.sql.execute(sql_delete, self.engine)
        pd.io.sql.execute('SET SQL_SAFE_UPDATES = 1;', self.engine)
        # 反馈
        status = 0
    return status