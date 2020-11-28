#coding=utf-8
import os

def get_root():
    [dirname, filename] = os.path.split(__file__)
    return dirname
