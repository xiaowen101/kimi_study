from flask import Flask, request, jsonify, render_template
from pathlib import Path
from openai import OpenAI
import os
import markdown

app = Flask(__name__,static_folder='static')

# 配置文件上传目录
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg','pgf','txt','xlsx'}

# 创建上传目录
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 配置 OpenAI 客户端
client = OpenAI(
    api_key="sk-PmiqgT5ddWohhlkk1HAOUQdFvTIr95gK7SsR8Htwv5IZP3hA",
    base_url="https://api.moonshot.cn/v1",
)


# 检查文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
# 根路径路由
@app.route('/')
def home():
    return render_template('index.html')

# 路由：上传文件
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "没有文件上传"}), 400

    file = request.files['file']

    # 检查文件名是否合法
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 上传文件并调用 OpenAI API 生成报告
        file_object = client.files.create(file=Path(filepath), purpose="file-extract")
        file_content = client.files.content(file_id=file_object.id).text

        # 构建消息并生成学习报告
        messages = [
            {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手。"},
            {"role": "system", "content": file_content},
            {"role": "system", "content": "你将充当数据分析师，为学生制定个性化学习报告。"},
            {"role": "user", "content": "请根据上传的文件中的得分情况，为该学生制定个性化学习报告，分析该学生的强项、弱项等，并给出合理的建议"},
        ]

        completion = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=messages,
            temperature=0.3,
        )

        # 获取生成的报告
        report = completion.choices[0].message.content
        report = markdown.markdown(report)

        # 返回生成的报告
        return jsonify({"report": report})

    return jsonify({"error": "不支持的文件类型"}), 400


if __name__ == '__main__':
    app.run(debug=True)
