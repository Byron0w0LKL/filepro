import os
from tkinter.filedialog import askdirectory
import PyPDF2
import docx2pdf
import doc2docx
from flask import Flask, redirect, render_template, request, send_file
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_bootstrap import Bootstrap

# 创建Flask应用对象
app = Flask(__name__)
bootstrap = Bootstrap(app)
ppath = "/"

app.config['keyword']=''


# 创建SQLite数据库的连接
db_path = r'C:\Users\30132\Desktop\文件查询pro\files.db'
url = f'sqlite:///{db_path}'  # 构建SQLite数据库的URL

engine = create_engine(url)

# 创建一个基类，用于定义数据表的映射类
Base = declarative_base()


# 定义一个File类，用于表示文件的信息
class File(Base):
    # 指定数据表的名称为files
    __tablename__ = 'files'

    # 定义id列为主键，自增长
    id = Column(Integer, primary_key = True)

    # 定义path列为文件的路径，唯一且不为空
    path = Column(String, unique = True, nullable = False)

    # 定义content列为文件的内容，用于全文搜索，不为空
    content = Column(String, nullable = False)


# 创建数据表
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# 创建会话类，用于操作数据库
Session = sessionmaker(bind = engine)


# 定义一个函数，用于从给定的目录中扫描所有的pdf或word文件，并将它们的路径和内容保存到数据库中
def scan_files(dir):
    # 创建一个会话对象
    session = Session()

    # 遍历给定目录及其子目录中的所有文件
    for root, dirs, files in os.walk(dir):
        for file in files:
            # 获取文件的完整路径
            path = os.path.join(root, file)

            # 判断文件是否为pdf或word格式
            if path.endswith('.pdf') or path.endswith('.docx') or path.endswith('.doc'):
                # 初始化一个空字符串，用于存储文件的内容
                content = ''

                # 如果文件为pdf格式，则使用PyPDF2库来读取内容
                if path.endswith('.pdf'):
                    # 打开pdf文件对象
                    pdf_file = open(path, 'rb')

                    # 创建一个pdf阅读器对象
                    pdf_reader = PyPDF2. PdfReader(pdf_file)

                    # 获取pdf文件的页数
                    num_pages = len(pdf_reader.pages)

                    # 遍历每一页，并将内容追加到字符串中
                    for i in range(num_pages):
                        page = pdf_reader.pages[i]
                        content += page.extract_text()

                    # 关闭pdf文件对象
                    pdf_file.close()

                # 如果文件为docx
                elif path.endswith( ".docx"):
                    # # 打开word文档对象
                    # doc_file =Document(path)
                    #
                    # # 遍历每一段，并将内容追加到字符串中
                    # for para in doc_file.paragraphs:
                    #     content += para.text+'\n'

                    docx2pdf.convert(path, path + ".pdf")
                    # 打开pdf文件
                    pdf_file = open(path + ".pdf", "rb")
                    # 创建pdf阅读器对象
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    # 初始化内容为空字符串
                    content = ""
                    # 获取pdf文件的页数
                    num_pages = len(pdf_reader.pages)
                    # 遍历每一页，并将内容追加到字符串中
                    for i in range(num_pages):
                        page = pdf_reader.pages[i]
                        content += page.extract_text()
                    # 关闭pdf文件对象
                    pdf_file.close()
                    # 删除临时的pdf文件
                    os.remove(path + ".pdf")


                # 如果文件为doc
                elif path.endswith(".doc"):
                    doc2docx.convert(path, path + ".docx")
                    docx2pdf.convert(path + ".docx", path + ".pdf")
                    # 打开pdf文件
                    pdf_file = open(path + ".pdf", "rb")
                    # 创建pdf阅读器对象
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    # 获取pdf文件的页数
                    num_pages = len(pdf_reader.pages)
                    # 遍历每一页，并将内容追加到字符串中
                    for i in range(num_pages):
                        page = pdf_reader.pages[i]
                        content += page.extract_text()
                    # 关闭pdf文件对象
                    pdf_file.close()
                    # 删除临时的pdf文件
                    os.remove(path + ".docx")
                    os.remove(path + ".pdf")


                # 去除字符串中的空白字符，并转换为小写形式，以便于全文搜索
                content = content.strip().lower()

                # 判断数据库中是否已经存在该文件的记录，如果不存在，则创建一个新的File对象，并添加到会话中
                if not session.query(File).filter_by(path = path).first():
                    file_obj = File(path = path, content = content)
                    session.add(file_obj)

    # 提交会话，将数据保存到数据库中
    session.commit()

    # 关闭会话
    session.close()

def make_tree(path):
    # 创建一个字典，存储文件名和子目录
    tree = dict(name=path, children=[]) # 使用path而不是os.path.basename(path)
    # 尝试列出路径下的所有文件和目录
    try:
        lst = os.listdir(path)
    except OSError:
        pass # 忽略错误
    else:
        # 遍历所有文件和目录
        for name in lst:
            fn = os.path.join(path, name)
            # 如果是目录，递归调用make_tree函数
            if os.path.isdir(fn):
                tree['children'].append(make_tree(fn))
            # 如果是文件，忽略
            else:
                pass
    # 返回树形结构的字典
    return tree

# # 定义一个路由函数，用于处理用户选择查询目录的请求
# @app.route('/', methods = ['GET', 'POST'])
# def index():
#     # 如果请求方法为GET，则渲染一个模板，让用户输入查询目录
#     if request.method == 'GET':
#         return render_template("index.html")
#
#     # 如果请求方法为POST，则获取用户选择的查询目录，并调用scan_files函数，然后重定向到搜索页面
#     elif request.method == 'POST':
#         dir = askdirectory()
#
#         return redirect('/search')


@app.route('/')
def disks():
    # 获取本地所有的磁盘名称
    disks = [d + ':\\' for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(d + ':\\')]
    # 渲染一个模板文件，传入磁盘名称列表
    return render_template('disks.html', disks=disks)

@app.route('/files/<path:path>')
def files_path(path):
    # 根据路径参数生成一个树形结构的字典，包含文件名和子目录
    tree = make_tree(path)
    # 渲染一个模板文件，传入树形结构和os模块
    return render_template('files.html', tree=tree, os=os, path=path)

# 定义一个路由函数，用于处理用户输入关键字的请求，并返回符合要求的结果
@app.route('/search/<path:path>', methods = ['GET', 'POST'])
def search(path):
    # 如果请求方法为GET，则渲染一个模板，让用户输入关键字
    if request.method == 'GET':
        scan_files(path)
        return render_template('search.html')

    # 如果请求方法为POST，则获取用户输入的关键字，并在数据库中进行全文搜索，然后渲染一个模板，显示搜索结果
    elif request.method == 'POST':
        keyword = request.form.get('keyword')
        keyword = keyword.strip().lower()
        app.config['keyword'] = keyword
        session = Session()
        files = session.query(File).filter(File.content.ilike(f'%{keyword}%')).all()
        for file in files:
            lines = file.content.split('\n')
            content=''
            for i, line in enumerate(lines):
                if app.config['keyword'] in line:
                    line = line.replace(app.config['keyword'], f"<span style='color:red'>{app.config['keyword']}</span>")
                    content += "行号：" + str(i + 1) + "  " + line + "\n"
            content += "\n\n"
            file.content=content
        session.close()
        return render_template('result.html', files = files,keyword = keyword)


# 定义一个路由函数，用于处理用户选择多个查询结果内容，并保存到文本并下载的请求
@app.route('/save', methods = ['POST'])
def save():
    # 获取用户选择的文件id列表
    file_ids = request.form.getlist('file_id')

    # 创建一个会话对象
    session = Session()

    # 初始化一个空字符串，用于存储所有选择的文件内容
    content = ''

    # 遍历每个文件id，并从数据库中查询对应的文件对象，然后将其路径和内容追加到字符串中
    for file_id in file_ids:
        file_obj = session.query(File).filter_by(id = file_id).first()
        content += file_obj.path + '\n'
        content += '-------------------------------\n'
        # content += file_obj.content + '\n\n'
        lines = file_obj.content.split('\n')
        for i, line in enumerate(lines):
            if app.config['keyword'] in line:
                content += "行号：" + str(i + 1) + "  " + line + "\n"
        content += "\n\n"

    # 关闭会话
    session.close()

    # 将字符串保存到一个临时文件中，并返回给用户下载
    print(content)
    with open('temp.txt', 'w',encoding="utf-8") as f:
        f.write(content)
    return send_file('temp.txt', as_attachment = True)


