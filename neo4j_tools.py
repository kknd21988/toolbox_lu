##############################################
############   neo4j的函数      ###############
##############################################
def load_nodes_neo4j(nodes_csv, graph_object):
    '''把节点信息导入neo4j
    参考：https://www.jianshu.com/p/a24cf6893949'''
    if isinstance(graph_object, py2neo.database.Graph) is False:
        print("type of input graph_object should be py2neo.database.Graph, instead of {current_type}".format(current_type=type(graph_object)))
        return -1

    node_matcher = NodeMatcher(graph_object)
    with open(nodes_csv, newline = '', encoding='utf-8') as rdFile:
        csv_reader = csv.reader(rdFile)
        for row in tqdm(csv_reader):
            uid = row[0]
            string = row[1]
            children = row[2]
            create_time = row[3]
            edit_time = row[4]
            # create node of block
            block = node_matcher.match('Block', UID=uid).first()
            if not block:
                block = Node("Block",
                          UID=uid, STRING=string,
                          CHILDREN=children,
                          CREATE_TIME=create_time,
                          EDIT_TIME=edit_time)
            graph_object.create(block)
    return 0

def load_relations_neo4j(relations_csv, graph_object):
    '''把关系信息导入neo4j
    参考：https://www.jianshu.com/p/a24cf6893949'''
    if isinstance(graph_object, py2neo.database.Graph) is False:
        print("type of input graph_object should be py2neo.database.Graph, instead of {current_type}".format(current_type=type(graph_object)))
        return -1

    # create relationship of personal_call
    relationship_matcher = RelationshipMatcher(graph_object)
    with open(relations_csv, newline = '', encoding='utf-8') as rdFile:
        csv_reader = csv.reader(rdFile)
        for row in tqdm(csv_reader):
            start_uid = row[0]
            relation_type = row[1]
            end_uid = row[2]
            
            node_matcher = NodeMatcher(graph_object)
            # 图中起点
            start_node = node_matcher.match('Block', UID=start_uid).first()
            if start_node is None:
                print("Start node {} does not exist in graph".format(start_uid))
            # 图中终点
            end_node = node_matcher.match('Block', UID=end_uid).first()
            if end_node is None:
                print("End node {} does not exist in graph".format(end_uid))
            # 添加关系
            if start_node is not None and end_node is not None:
                relation = relationship_matcher.match(nodes=(start_node, end_node), r_type=relation_type).first()
                if relation is None:
                    try:
                        relation = Relationship(start_node, relation_type, end_node)
                        graph_object.create(relation)
                    except Exception as e:
                        a=1
    return 0