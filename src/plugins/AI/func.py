import re
import functools
import copy
import asyncio
import httpx
from pathlib import Path
from PIL import Image
from markdown import markdown
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from aiogram.types import Message

from ...utils import CONFIG

cupa=Path.cwd()/'src/plugins/AI/record'
tmp=Path.cwd()/'assets'
key=CONFIG['api_keys']['siliconflow_key']

rc=lambda role,content:{"role":role,"content":content}
per='你是智能机器人助手Fool'
ini=[
    rc("system",per),
    rc("system","你的开发者是「L the Fool」"),
    rc("system","重要：接下来的对话若无必要请不要使用除简体中文和英语之外的任何语言，请使用markdown格式"),
    rc("system","在适当的情境下，请适量使用emoji")
]

client=httpx.AsyncClient(
    base_url="https://api.siliconflow.cn/v1",
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    },
    timeout=90.0
)

def ensure_user_session(session:dict,default:dict):
    def ensure_user_session(func):
        @functools.wraps(func)
        async def wrapper(message:Message,*args,**kwargs):
            user=str(message.chat.id)
            if user not in session:
                session[user]=copy.deepcopy(default)
                print(f"🆕 [Decorator] 为用户 {user} 初始化会话")
            return await func(message,*args,**kwargs)
        return wrapper
    return ensure_user_session

head = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-okaidia.min.css" rel="stylesheet" />
    <style>
        @font-face {
            font-family: 'SegUIEmoji';
            src: url('seguiemj.ttf') format('truetype');
        }
        @font-face {
            font-family: 'MyMainFont';
            src: url('font.ttf') format('truetype');
        }
        * {
            margin: 0;
            padding: 0;
            font-family: 'SegUIEmoji', 'MyMainFont', 'Segoe UI Emoji', sans-serif !important;
            font-size: 16px;
            white-space: pre-wrap;
            line-height: 1.5em;
            box-sizing: border-box;
            color: #333;
        }
        body {
            display: inline-block;
            width: fit-content;
            min-width: 600px;
            padding: 5px 5px 85px 5px;
            border: 3px solid #FFB400; 
            background-color: #ffffff; 
            position: relative;
            margin: 0 auto;
        }
        pre[class*="language-"] {
            background-color: #2d2d2d !important; 
            border-radius: 8px;
            margin: 15px 0;
            padding: 15px;
            border: 1px solid #444;
            color: #f8f8f2 !important;
            white-space: pre;
            overflow-x: auto; /* 允许横向滚动 */
            width: 100%;
            max-width: 100%;
            text-shadow: none; /* 去除某些主题的阴影 */
        }
        code[class*="language-"], pre[class*="language-"] {
            font-family: 'Consolas', 'Monaco', 'Courier New', 'SegUIEmoji', 'MyMainFont', monospace !important;
            font-size: 14px;
            text-shadow: none !important;
        }
        p code, li code, td code {
            background-color: #f0f0f0 !important;
            color: #e83e8c !important;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'SegUIEmoji', 'MyMainFont', monospace !important;
            font-size: 0.9em;
            white-space: nowrap;
        }
        blockquote {
            background-color: #f8f9fa;
            border-left: 4px solid #e338e6;
            margin: 15px 0;
            padding: 10px 15px;
            color: #555;
            border-radius: 0 4px 4px 0;
        }
        br {
            display: none; 
        }
        .color-lump {
            width: 80px;
            height: 80px;
            background-color: #FFB400;
            position: absolute;
            left: 0;
            bottom: 0;
            border-radius: 0;
            z-index: 9999;
            margin: 0;
            transform: none;
        }
    </style>
</head>
<body>
'''

tail='''
<div class="color-lump"></div>
</body>
</html>'''

PRISM_COMPONENTS={
    'python':'prism-python.min.js',
    'py':'prism-python.min.js',
    'bash':'prism-bash.min.js',
    'shell':'prism-bash.min.js',
    'sh':'prism-bash.min.js',
    'html':'prism-markup.min.js',
    'xml':'prism-markup.min.js',
    'json':'prism-json.min.js',
    'javascript':'prism-javascript.min.js',
    'js':'prism-javascript.min.js',
    'css':'prism-css.min.js',
    'sql':'prism-sql.min.js',
    'yaml':'prism-yaml.min.js',
    'yml':'prism-yaml.min.js',
    'markdown':'prism-markdown.min.js',
    'md':'prism-markdown.min.js',
    'diff':'prism-diff.min.js',
    'git':'prism-git.min.js'
}

CDN_BASE="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/"

def generate_html(msg:str,user:str):
    html_body=markdown(
            msg,
            extensions=['fenced_code','tables','nl2br','codehilite'],
            extension_configs={
                'codehilite':{
                    'linenums':False,
                    'use_pygments':False,
                    'lang_prefix':'language-'
                }
            }
        )
    langs_found=set(re.findall(r'language-([\w-]+)',html_body))
    scripts=['\n<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>']
    for lang in langs_found:
        lang_key=lang.lower()
        if lang_key in PRISM_COMPONENTS:
            js_file=PRISM_COMPONENTS[lang_key]
            scripts.append(f'<script src="{CDN_BASE}{js_file}"></script>')
    scripts_html="\n".join(scripts)
    final_html=head+html_body+scripts_html+tail
    return final_html

def mark(nm,path):
    pa=str(cupa/f"{nm}.png")
    options=Options()
    options.add_argument("--headless")
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.binary_location=str(tmp/'googlechrome/chrome.exe')
    service=Service(executable_path=str(tmp/'googlechrome/chromedriver.exe'))
    driver=ChromeDriver(options=options,service=service)
    try:
        driver.set_window_position(0,0)
        INITIAL_WIDTH=1920
        INITIAL_HEIGHT=1080
        driver.set_window_size(INITIAL_WIDTH,INITIAL_HEIGHT)
        driver.get(f'file:///{path}')
        driver.implicitly_wait(2)
        total_height=driver.execute_script("return document.body.scrollHeight;")
        total_width=driver.execute_script("return document.body.scrollWidth;")
        final_height=total_height+50
        final_width=total_width+50
        driver.set_window_size(final_width,final_height)
        driver.implicitly_wait(2)
        driver.save_screenshot(pa)
    except Exception as e:
        print(f"❌ 截图过程出错: {e}")
    finally:
        driver.quit()
    img=Image.open(pa).convert('RGB')
    img.show()
    width,height=img.size
    ORANGE=(255,180,0)
    BORDER_WIDTH=3
    def row_has_orange(y,x_start,x_end):
        for x in range(x_start,x_end+1):
            if 0<=x<width and img.getpixel((x,y))==ORANGE:
                return True
        return False
    def col_has_orange(x,y_start,y_end):
        for y in range(y_start,y_end+1):
            if 0<=y<height and img.getpixel((x, y))==ORANGE:
                return True
        return False
    top=0
    for y in range(height):
        if row_has_orange(y,0,width-1):
            top=y
            break
    bottom=height-1
    for y in range(height-1,-1,-1):
        if row_has_orange(y,0,width-1):
            bottom=y
            break
    left=0
    for x in range(width):
        if col_has_orange(x,top,bottom):
            left=x
            break
    right=width-1
    for x in range(width-1,-1,-1):
        if col_has_orange(x,top,bottom):
            right=x
            break
    if top<bottom and left<right:
        inner_left=left+BORDER_WIDTH
        inner_right=right-BORDER_WIDTH
        inner_top=top+BORDER_WIDTH
        inner_bottom=bottom-BORDER_WIDTH-80
        if inner_top<inner_bottom and inner_left<inner_right:
            cropped_img=img.crop((inner_left,inner_top,inner_right,inner_bottom))
            cropped_img.save(pa)
            print(f"✅ 成功裁剪：[{inner_left}, {inner_top}, {inner_right}, {inner_bottom}]")
        else:
            print("⚠️ 警告：扣除边框后区域无效，可能图片过小，保存原图。")
            img.save(pa)
    else:
        print("⚠️ 警告：未检测到橙色边框，保存原图。")
        img.save(pa)

async def send_long_message(message:Message,text):
    MAX_LEN=4000
    total_len=len(text)
    for i in range(0,total_len,MAX_LEN):
        chunk=text[i:i+MAX_LEN]
        try:
            await message.reply(chunk)
        except Exception as e:
            print(f"发送失败: {e}")
        if total_len>MAX_LEN*5:
            await asyncio.sleep(1)

def get_black_list():
    path=cupa/'black.txt'
    if not path.exists():
        return []
    with open(path,'r',encoding='utf-8') as a:
        return [line.strip() for line in a if line.strip()]
    
def save_black_list(black_list:list):
    with open(cupa/'black.txt','w',encoding='utf-8') as a:
        a.write('\n'.join(black_list))