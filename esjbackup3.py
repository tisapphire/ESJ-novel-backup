#!/usr/bin/env python
#coding=utf-8

import requests
import lxml.html
import re
import json
import os
import sys

from bs4 import BeautifulSoup

symbol_list = {
    "\\": "-",
    "/": "-",
    ":": "：",
    "*": "☆",
    "?": "？",
    "\"": " ",
    "<": "《",
    ">": "》",
    "|": "-",
    ".": "。",
    "\t": " ",
    "\n": " ",
}

cookies = {"ews_key": "xxxx", "ews_token": "xxxx"}

def get_subpage_links(directory_url):
    subpage_links = []

    # 发送GET请求获取目录页面内容
    response = requests.get(directory_url, cookies=cookies)
    if response.status_code == 200:
        # 使用BeautifulSoup解析目录页面
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到所有tag属性为'a'的元素
        links = soup.find_all('a')

        # 提取每个链接的URL并添加到子页面链接列表
        for link in links:
            subpage_url = link.get('href')
            if subpage_url and re.match(r'https://www\.esjzone\.cc/forum/.+\.html', subpage_url):
                subpage_links.append(subpage_url)

    return subpage_links

def write_page(url, dst_file, single_file=True):
    r = requests.get(url, cookies=cookies)
    html_element = lxml.html.document_fromstring(r.text)
    if html_element.xpath('//h2'):
        title = html_element.xpath('//h2')[0]
        author = html_element.xpath('//div[@class="single-post-meta m-t-20"]/div')[0]
        content = html_element.xpath('//div[@class="forum-content mt-3"]')[0]
        if single_file:
            with open(dst_file, 'a', encoding='utf-8') as f:
                f.write('[' + title.text_content() + '] ' + author.text_content().strip() + '\n')
                f.write(content.text_content()+'\n\n')
        else:
            with open(dst_file, 'w', encoding='utf-8') as f:
                f.write('[' + title.text_content() + '] ' + author.text_content().strip() + '\n')
                f.write(content.text_content()+'\n\n')

def contain(string: str, array):
    if isinstance(array, dict):
        return any(symbol in string for symbol in array.keys())
    elif isinstance(array, list) or isinstance(array, tuple):
        return any(symbol in string for symbol in array)
    return False


def escape_symbol(string: str):
    while contain(string, symbol_list):
        for char, replace_char in symbol_list.items():
            string = string.replace(char, replace_char)
    return string


if __name__ == "__main__":


    current_path = os.path.split(os.path.realpath(__file__))[0]
    novel_flag = False
    forum_flag = False
    page_flag = False

    if len(sys.argv) == 1:
        print("Usage: ", __file__, " https://www.esjzone.cc/detail/1599746513")
        print("       ", __file__, " https://www.esjzone.cc/forum/1584679807/1599746513/")
        print("       ", __file__, " https://www.esjzone.cc/forum/1599746513/121688.html")
        sys.exit()
    
  
    url = sys.argv[1]
    if re.search(r'https://www\.esjzone\.cc/detail/\d+\.html', url):
        novel_flag = True
    elif re.search(r'https://www\.esjzone\.cc/detail/\d', url):
        novel_flag = True
    elif re.search(r'https://www\.esjzone\.cc/forum/\d+/\d+/', url):
        forum_flag = True
    elif re.search(r'https://www\.esjzone\.cc/forum/\d+/\d+\.html', url):
        page_flag = True
    else:
        print("Wrong url")
        sys.exit()


    if novel_flag :

        r = requests.get(url, cookies=cookies)
        html_element = lxml.html.document_fromstring(r.text)

        s=get_subpage_links(url)

        novel_name = html_element.xpath('//h2[@class="p-t-10 text-normal"]')[0].text_content()
        novel_name = escape_symbol(novel_name)
        dst_filename = os.path.normpath( current_path + '/' + novel_name + '.txt')
        with open(dst_filename, 'w', encoding='utf-8') as f:
            f.write(u"书名: " + novel_name + "\n")
        with open(dst_filename, 'a', encoding='utf-8') as f:
            f.write(u"URL: " + url)

        novel_details_element = html_element.xpath('//ul[@class="list-unstyled mb-2 book-detail"]')[0]
        if novel_details_element.xpath('//ul[@class="list-unstyled mb-2 book-detail"]/li/div'):
            bad_divs = novel_details_element.xpath('//ul[@class="list-unstyled mb-2 book-detail"]/li/div')
            for bad_div in bad_divs:
                bad_div.getparent().remove(bad_div)
        novel_details = novel_details_element.text_content()
        with open(dst_filename, 'a', encoding='utf-8') as f:
            f.write(novel_details)

        novel_outlink_element = html_element.xpath('//div[@class="row out-link"]')[0]
        if len(novel_outlink_element) != 0:
            outlink_list = novel_outlink_element.getchildren()
            for element in outlink_list:
                with open(dst_filename, 'a', encoding='utf-8') as f:
                    f.write(element.getchildren()[0].text_content() + u":\n" + element.getchildren()[0].attrib['href'] + "\n")

        if re.search('id="details"', r.text):
            novel_description = html_element.get_element_by_id("details").text_content()
            with open(dst_filename, 'a', encoding='utf-8') as f:
                f.write(novel_description)
        else:
            with open(dst_filename, 'a', encoding='utf-8') as f:
                f.write('\n\n')

        for url in s:
            write_page(url, dst_filename, single_file=True)


    if forum_flag:

        r = requests.get(url, cookies=cookies)
        html_element = lxml.html.document_fromstring(r.text)
        novel_name = html_element.xpath('//h2[@class="p-t-10 text-normal"]')[0].text_content()
        novel_name = escape_symbol(novel_name)

        m = re.search(r"var mem_id='(u?\d+)',mem_nickname='.*',token='(.+)';", r.text) 
        mem_id, token = m.groups()
        m = re.search(r"forum_list_data\.php\?token=.+&totalRows=(\d+)&bid=(\d+)", r.text) 
        totalRows, bid = m.groups()

        r = requests.get(url + 'forum_list_data.php?token=' + token + '&totalRows=' + str(totalRows) + '&bid=' + str(bid) + \
                         '&sort=cdate&order=asc&offset=0&limit=' + str(totalRows) )

        chapter_josn = json.loads(r.text)

        if chapter_josn["rows"]:

            if not os.path.isdir( os.path.normpath( current_path + '/' + novel_name ) ):
                os.system("mkdir " + str(os.path.normpath( current_path + '/' + novel_name )))

            for chapter in chapter_josn["rows"]:
                chapter_name = chapter["subject"].split('target="_blank">')[1].split('</a>')[0]
                chapter_name = escape_symbol(chapter_name)
                dst_filename = os.path.normpath( current_path + '/' + novel_name + '/' + chapter_name + '.txt')
                chapter_url = re.sub(r'/forum/\d+/\d+/', chapter["subject"].split('"')[1], url)
                write_page(chapter_url, dst_filename, single_file=False)


    if page_flag :
        
        write_page(url, url.split('/')[-1].split('.')[0] + ".txt", single_file=False)
