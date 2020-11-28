

def get_slope(x0,y0,x1,y1):
    # 计算两个点连线的斜率
    if float(x1)-float(x0) == 0:
        slope = float('inf')    # 正无穷
    else:
        slope = 1.0*(float(y1)-float(y0))/(float(x1)-float(x0))
    return slope

def get_mid_point(x0,y0,x1,y1):
    mid_point = {}
    # 获取两个点连线的中点
    mid_point['mid_x'] = (float(x0)+float(x1))/2.0
    mid_point['mid_y'] = (float(y0)+float(y1))/2.0
    return mid_point