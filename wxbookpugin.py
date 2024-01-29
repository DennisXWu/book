# -*- coding: utf-8 -*-
import sys
import re
import os
import urllib.request
from multiprocessing import Pool, freeze_support

current_dir = os.path.dirname(os.path.abspath(__file__))


def convert_to_markdown():
    markdown_lines = ["[TOC]\n"]
    note_list = []
    current_section = ""
    chapter_name = ""
    image_index = 1
    note_index = 1
    chapter_dict = {}
    note_dict = {}
    image_dict = {}
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            numbers = re.findall(r'\d+', line)
            if line.startswith("◆") and "书签" not in line:
                chapter_dict[chapter_name] = markdown_lines
                note_dict[chapter_name] = note_list
                markdown_lines = []
                note_list = []
                first_num, second_num, third_num, chapter_name, current_section = first_title(numbers, markdown_lines,
                                                                                              line)
            elif "发表想法" in line:
                current_section = "idea"
            elif current_section == "idea" and "##" in line:
                third_num, current_section = third_title(file, markdown_lines, line, first_num, second_num, third_num)
            elif current_section == "idea" and line.startswith("http"):
                current_section, image_index = image_title(line, markdown_lines, image_index, image_dict, chapter_name)
            elif current_section == "idea" and line.startswith("%"):
                current_section = code_title(file, markdown_lines, line)
            elif current_section == "idea" and line.startswith("^"):
                current_section, note_index = note_line(file, line, markdown_lines, note_index, note_list)
            elif current_section == "idea" and line.startswith("*"):
                current_section = bold_title(file, markdown_lines)
            elif current_section == "idea" and line.startswith("b"):
                current_section = bold_line(file, markdown_lines)
            elif current_section == "idea" and "#" in line:
                second_num, third_num, current_section = second_title(file, markdown_lines, first_num, second_num, line)
            elif current_section == "content" and line.startswith(">>") and "[插图]" not in line:
                markdown_lines.append("  %s" % line[2:])
            elif line.startswith("") and "[插图]" not in line:
                markdown_lines.append("  %s" % line)

    args_param = ((key, image_dict[key]) for key in image_dict)
    async_map_pool(download_images, args_param, 5)
    chapter_dict[chapter_name] = markdown_lines
    note_dict[chapter_name] = note_list
    write_chapter_result(chapter_dict, note_dict)


def write_md_file(md_file, markdown_lines):
    if len(markdown_lines) == 0:
        return
    with open(md_file, 'w', encoding='utf-8') as file:
        file.write('\n'.join(markdown_lines))


def first_title(numbers, markdown_lines, line):
    if len(numbers) > 0:
        first_num = numbers[0]
    else:
        first_num = 1
    if first_num.startswith("0"):
        first_num = first_num[1:]

    second_num = 0
    third_num = 0
    markdown_lines.append("# %s" % line[2:])
    return first_num, second_num, third_num, line[2:], "content"


def third_title(file, markdown_lines, line, first_num, second_num, third_num):
    third_num += 1
    if line.strip() == "##":
        line = next(file).strip()
    line = line.replace('\u3000', ' ').replace('#', '').replace('>', '')
    markdown_lines.append("### %s.%s.%s %s" % (first_num, second_num, third_num, line))
    return third_num, "content"


def async_map_pool(func, iter_obj, pool_size):
    freeze_support()
    pool = Pool(pool_size)
    pool.map_async(func, iter_obj)
    pool.close()
    pool.join()


def download_images(args_param):
    try:
        image_name, image_url = args_param
        parent_directory = os.path.dirname(image_name)
        os.makedirs(parent_directory, exist_ok=True)
        response = urllib.request.urlopen(image_url)
        with open(image_name, "wb") as file:
            file.write(response.read())
    except urllib.error.URLError as e:
        print("download image failed:", e)


def second_title(file, markdown_lines, first_num, second_num, line):
    second_num += 1
    third_num = 0
    if line.strip() == "#":
        line = next(file).strip()
    line = line.replace('\u3000', ' ').replace('#', '').replace('>', '')
    markdown_lines.append("## %s.%s %s" % (first_num, second_num, line))
    return second_num, third_num, "content"


def image_title(image_url, markdown_lines, image_index, image_dict, chapter_name):
    if type == '--chapter':
        dest_image_path = "%s/%s/images/%s.jpg" % (markdown_file_path, chapter_name, image_index)
        markdown_lines.append("![](images/%s.jpg)" % image_index)
    else:
        dest_image_path = "%s/%s.jpg" % (image_file_path, image_index)
        markdown_lines.append("![](images/%s.jpg)" % image_index)
    image_dict[dest_image_path] = image_url
    return "content", image_index + 1


def bold_title(file, markdown_lines):
    line = next(file).strip()
    markdown_lines.append("- *%s*" % line[3:])
    return "content"


def code_title(file, markdown_lines, line):
    code_lines = line[1:] + "\n"
    line = next(file).strip()
    while not line.startswith(">>"):
        code_lines += line + "\n"
        line = next(file).strip()
    markdown_lines.append("```java\n%s\n```" % code_lines.replace("", "").replace("", ""))
    return "content"


def bold_line(file, markdown_lines):
    line = next(file).strip()
    line_ = line[3:]
    is_match = False
    item = markdown_lines[-5:]
    for item_line in item:
        if line_ in item_line:
            is_match = True
            index = markdown_lines.index(item_line)
            markdown_lines[index] = item_line.replace(line_, "**%s**" % line_)
    if not is_match:
        markdown_lines.append("**%s**" % line_)
    return "content"


def note_line(file, line, markdown_lines, note_index, note_list):
    note_list.append("[^%s]:%s" % (note_index, line[1:]))
    line = next(file).strip()
    line_ = line[3:]
    size = len(markdown_lines)
    is_match = False
    item = markdown_lines[size - 1]
    if line_ in item:
        is_match = True
        markdown_lines[size - 1] = item.replace(line_, "%s[^%s]" % (line_, note_index))
    if not is_match:
        markdown_lines.append("%s[^%s]" % (line_, note_index))
    return "content", note_index + 1


def write_chapter_result(chapter_dict, note_dict):
    if type == '--chapter':
        for key, value in chapter_dict.items():
            if len(key) > 0:
                value.insert(0, "[TOC]\n")
                value.extend(note_dict[key])
                markdown_path = "%s/%s/" % (markdown_file_path, key)
                markdown_file = "%s/%s.md" % (markdown_path, key)
                os.makedirs(markdown_path, exist_ok=True)
                write_md_file(markdown_file, value)
    else:
        lines = []
        for value in chapter_dict.values():
            lines.extend(value)
        for value in note_dict.values():
            lines.extend(value)
        write_md_file(output_file, lines)


if __name__ == '__main__':
    input_file = sys.argv[1]
    output_file_name = sys.argv[2]
    type = ""
    if len(sys.argv) == 4:
        type = sys.argv[3]

    if len(input_file) == 0 or len(output_file_name) == 0:
        print("args invalid")
        exit()
    markdown_file_path = "%s/%s" % (current_dir, output_file_name)
    if os.path.exists(markdown_file_path):
        os.system("rm -rf %s" % markdown_file_path)
    os.makedirs(markdown_file_path, exist_ok=True)
    image_file_path = "%s/images" % markdown_file_path
    output_file = "%s/%s.md" % (markdown_file_path, output_file_name)
    convert_to_markdown()
