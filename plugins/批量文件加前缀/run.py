#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/27 11:09
# @Author  : 我的名字
# @File    : run.py
# @Description : 这个函数是用来balabalabala自己写
# 简单示例：接收两个参数 folder prefix
import sys
import os
import time

if len(sys.argv) < 3:
    print("Usage: run.py <folder> <prefix>")
    sys.exit(1)

folder = sys.argv[1]
prefix = sys.argv[2]

print("开始批量改名", folder, prefix)
for i, f in enumerate(os.listdir(folder)):
    src = os.path.join(folder, f)
    if os.path.isfile(src):
        dst = os.path.join(folder, prefix + f)
        os.rename(src, dst)
        print(">>>", f, "->", prefix + f)
        time.sleep(0.05)
print("完成")

