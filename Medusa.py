# -*- coding: utf-8 -*-
__author__ = 'ice'

###### config #####
mode_symmetry = [
    ["idea", "eclipse"],
    ["dev", "release"]
]

ignore_dir = [
    "node_modules",
    "sea-modules",
    "spm_modules",
    "sofax-dump",
    "target"
]

excl_type = [
    'iml',
    'MF',
    'class',
    'bat',
    'sh',
    'txt',
    'jar',
    'fragment',
    'handlers',
    'schemas',
    'pid',
    '1',
    'acf',
    'pyc',
    'log',
    'MD',
    'css',
    'com',
    'gif',
    'png',
    'psd',
    'eot',
    'svg',
    'ttf',
    'woff'
]

anna_map = {
    "java": "//## ${} ##//",
    "js": "//## ${} ##//",
    "xml": "<!--## ${} ##-->",
    "properties": "#### ${} ####",
    "vm": "#### ${} ####"
}

anna_key = {
    "java": "//# ${}",
    "js": "//# ${}",
    "xml": "<!--# ${} #-->",
    "properties": "#! ${}",
    "vm": "##! ${}"
}

anna_standard = {
    "java": "//${}",
    "js": "//${}",
    "xml": "<!--${}-->",
    "properties": "#${}",
    "vm": "##${}"
}

########### end #############


import os
import sys
import re
import platform

_RELEASE_ = "release"
_END_ = "end"
_ANNA_ = 1
_DEANNA_ = 2
_NORMAL_ = 0
_SLASH_ = ("/" if platform.system() != "Windows" else "\\")

_GRAMMAR_ = 0
_NOBLOCK_ = 1

file_types = []
hit_mode = []
anna_mode = []


def scan_types(file_path):
    if os.path.isfile(file_path):
        ftype = file_path.split(_SLASH_)[-1]
        if "." not in ftype:
            return
        ftype = file_path.split(".")[-1]
        if ftype not in file_types:
            file_types.append(ftype)
        return
    # 目录的话进行目录扫描递归
    file_list = os.listdir(file_path)
    for f in file_list:
        # 默认隐藏文件夹忽略
        if f.startswith("."):
            continue
        scan_types(os.path.join(file_path, f))


def process_args():
    """
    处理执行参数
    没有参数默认为正式版
    :return:
    """
    global mode_symmetry, hit_mode, anna_mode

    hit_mode = [_RELEASE_] if sys.argv.__len__() <= 1 else [x.strip() for x in sys.argv[1:]]

    if "scan" in hit_mode:
        scan_types(".")
        print file_types
        exit(0)

    for mode in hit_mode:
        for sym in mode_symmetry:
            for x in sym:
                if mode in x:
                    anna_mode += [xx for xx in sym if xx != mode]
    pass


def is_ignore(name):
    """
    文件是否在排除类型之外
    :param name:
    :return:
    """
    if name.startswith(".") and not name.startswith("." + _SLASH_):
        return True
    if "." not in name.split(_SLASH_)[-1]:
        return True
    name_type = name.split(".")[-1].lower()
    # print name_type
    if name_type in excl_type:
        # print name + " is in ignore list"
        return True
    if name_type not in anna_map:
        return True
    return False


def is_ignore_dir(dir_name):
    # 默认隐藏文件夹忽略和target文件夹忽略

    if dir_name.startswith('.') and dir_name != "." and dir_name != "." + _SLASH_:
        return True
    if dir_name in ignore_dir:
        return True

    return False


def anna_code(code, code_type):
    """
    代码块注释
    只注释每行注释符是从行首开始的，和用户自定义注释区分开
    如果已经满足注释条件不会重复注释
    :param code:
    :param code_type:
    :return:
    """
    global code_pattern, sample_pattern
    return code if code_pattern.search(code) or sample_pattern.search(code) else anna_key[code_type].replace(
        "${}", code.strip("\n")) + "\n"


def deanna_code(code, code_type):
    """
    反注释代码块
    只反注释每行注释符是从行首开始的，和用户自定义注释区分开
    如果不满足条件的不做处理
    :param code:
    :param code_type:
    :return:
    """
    global code_pattern
    match = code_pattern.search(code)
    return match.group(1) + "\n" if match else code


def verify_file(name):
    """
    检查代码块是否存在不闭合的情况
    :param name:
    :return:
    """
    global mark_pattern
    f = open(os.path.realpath(name))

    switch = False
    not_found_block = True

    for line in f:
        match = mark_pattern.search(line)
        if match:
            not_found_block = False
            if match.group(1).strip() != _END_:
                switch = True
            else:
                switch = False
    return [switch, not_found_block]


def process_file(name):
    """
    解析自定义代码块
    :param name:
    :return:
    """
    if is_ignore(name):
        return
    # print name
    file_type = name.split(".")[-1]
    # print file_type

    # 定义注释正则匹配
    global code_pattern, mark_pattern, sample_pattern, hit_mode, anna_mode
    code_pattern = re.compile("^" + anna_key[file_type].replace("${}", "(.*)"))
    mark_pattern = re.compile(anna_map[file_type].replace("${}", "(\w+)"))
    sample_pattern = re.compile("^( *)" + anna_standard[file_type].replace("${}", "(.*)"))

    # 如果文件语法不正确，则不处理
    verify_file_res = verify_file(name)
    if verify_file_res[_GRAMMAR_]:
        print "文件: " + name + " 语法校验失败，存在非闭合语法块，请校验规则！！！"
        return

    if verify_file_res[_NOBLOCK_]:
        # print "mei you shen ming bu yao du qu" + name
        return

    print 'Change: ' + name

    f = open(os.path.realpath(name))
    text = ""
    block_status = _NORMAL_
    for line in f:
        # if block_status == _DEANNA_:
        #     print "hint", line
        # elif block_status == _ANNA_:
        #     print "anna", line
        match = mark_pattern.search(line)
        if match and match.group(1).strip() == _END_:
            block_status = _NORMAL_
        text += anna_code(line, file_type) if block_status == _ANNA_ else deanna_code(line,
                                                                                      file_type) if block_status == _DEANNA_ else line
        if match:
            if match.group(1).strip() in hit_mode:
                block_status = _DEANNA_
            elif match.group(1).strip() in anna_mode:
                block_status = _ANNA_

    f.close()

    f = open(os.path.realpath(name), "w+")
    f.write(text)
    f.close()


def scan_dir(file_path):
    # 如果是文件的话，解析
    if os.path.isfile(file_path):
        process_file(file_path)
        return

    dir_name = file_path.split(_SLASH_)[-1]
    if is_ignore_dir(dir_name):
        return

    # 进行递归
    file_list = os.listdir(file_path)
    for f in file_list:
        scan_dir(os.path.join(file_path, f))


def check_config():
    global mode_symmetry
    check = []
    for sym in mode_symmetry:
        for item in sym:
            if item in check:
                print "配置出错：mode_symmetry 中模式" + item + "不能重复，请检查！"
                exit(0)
            else:
                check.append(item)


check_config()
process_args()
code_pattern = None
mark_pattern = None
sample_pattern = None
print "==========开始切换代码版本=========="
scan_dir(".")
print "=============切换完成=============="
