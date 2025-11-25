from flask import Flask, request, make_response, send_from_directory
import hashlib
import xml.etree.ElementTree as ET
import json
import os
import time
from datetime import datetime
from threading import Lock
import glob
from zhipu_chat import ZhipuChat

app = Flask(__name__)

# 微信公众号配置
WECHAT_TOKEN = "futuresample"  # 请替换为你的微信公众号Token

# 智谱AI配置
ZHIPU_API_KEY = "c17166d25b2142e3bde3649d1bd38d97.cixb4bTLpHjFMmH4"  # 请替换为你的智谱AI API密钥

# 数据文件路径
DATA_FILE = "data.json"
file_lock = Lock()

# 配置标准输出流的编码为UTF-8
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def find_player_file_by_number(player_number):
    """根据编号查找对应的txt文件"""
    try:
        # 在received_files目录下查找匹配的txt文件，使用_@分隔符
        pattern = f"received_files/{player_number}_@*.txt"
        matching_files = glob.glob(pattern)
        
        if matching_files:
            return matching_files[0]  # 返回第一个匹配的文件
        else:
            return None
    except Exception as e:
        log_message(f"查找玩家文件时出错: {str(e)}")
        return None


def load_player_story_content(file_path):
    """加载玩家故事内容，尝试多种编码格式"""
    encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'gbk', 'gb2312', 'latin1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read().strip()
            
            # 检查内容是否有效（不是乱码）
            if content and len(content) > 10:
                log_message(f"成功使用 {encoding} 编码读取文件")
                return content
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            log_message(f"读取文件时出错 ({encoding}): {str(e)}")
            continue
    
    log_message(f"所有编码格式都无法读取文件: {file_path}")
    return None


def log_message(message, user_id=None):
    """记录日志信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_info = f"[User: {user_id}]" if user_id else ""
    print(f"{timestamp} {user_info} {message}")

def read_data_file():
    """读取数据文件"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_message(f"读取数据文件失败: {str(e)}")
        return None

def verify_wechat_signature(signature, timestamp, nonce):
    """验证微信签名"""
    token = WECHAT_TOKEN
    tmp_arr = [token, timestamp, nonce]
    tmp_arr.sort()
    tmp_str = ''.join(tmp_arr)
    tmp_str = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
    return tmp_str == signature

def parse_xml_message(xml_data):
    """解析微信XML消息"""
    try:
        root = ET.fromstring(xml_data)
        msg = {}
        for child in root:
            msg[child.tag] = child.text
        return msg
    except Exception as e:
        log_message(f"解析XML消息失败: {str(e)}")
        return None

def create_text_response(to_user, from_user, content):
    """创建文本回复消息"""
    response = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
    return response



def check_existing_visualizations(player_number):
    """检查是否已存在生成的可视化文件"""
    try:
        output_dir = '../output_videos'
        if not os.path.exists(output_dir):
            return None, "输出目录不存在"
        
        # 查找该编号对应的GIF文件
        generated_files = []
        for filename in os.listdir(output_dir):
            if filename.endswith('.gif') and str(player_number) in filename:
                file_path = os.path.join(output_dir, filename)
                generated_files.append(file_path)
        
        if generated_files:
            log_message(f"找到编号 {player_number} 的 {len(generated_files)} 个可视化文件")
            return generated_files, "找到已生成的可视化文件"
        else:
            return None, "未找到对应的可视化文件"
            
    except Exception as e:
        error_msg = f"检查可视化文件时发生错误: {str(e)}"
        log_message(error_msg)
        return None, error_msg
def create_download_response(player_number, generated_files):
    """创建下载链接响应消息"""
    try:
        # 统计文件类型
        file_types = []
        if any('money' in os.path.basename(f) for f in generated_files):
            file_types.append("💰 资金变化动画")
        if any('body_state' in os.path.basename(f) for f in generated_files):
            file_types.append("💪 身体状态变化动画")
        if any('mind_state' in os.path.basename(f) for f in generated_files):
            file_types.append("🧠 心理状态变化动画")
        if any('movement' in os.path.basename(f) for f in generated_files):
            file_types.append("🗺️ 行动轨迹动画")
        
        content_info = "\n".join([f"• {ft}" for ft in file_types])
        
        # 生成下载链接
        download_links = []
        for file_path in generated_files:
            filename = os.path.basename(file_path)
            download_url = f"http://47.110.73.172/download/{filename}"
            download_links.append(f"• {filename}: {download_url}")
        
        download_info = "\n".join(download_links)
        
        response_text = f"🎉 编号 {player_number} 的可视化图表已准备好！\n\n" \
                       f"成功找到 {len(generated_files)} 个动画文件:\n{content_info}\n\n" \
                       f"📩 下载链接:\n{download_info}\n\n" \
                       f"📱 使用说明:\n" \
                       f"点击链接可直接下载对应的GIF动画文件"
        
        return response_text
        
    except Exception as e:
        log_message(f"创建下载响应消息时出错: {str(e)}")
        return f"🎉 编号 {player_number} 的图表已准备好！但生成链接时出错。"



def query_player_status(player_number):
    """查询玩家状态"""
    try:
        player_number = int(player_number)
    except ValueError:
        return "请输入有效的数字编号"
    
    with file_lock:
        data = read_data_file()
        if not data:
            return "系统数据暂时无法读取，请稍后再试"
        
        metadata = data.get('received_data', {}).get('metadata', {})
        current_number = metadata.get('current_number', 0)
        total_players = metadata.get('total_players', 0)
        
        log_message(f"查询编号 {player_number}，当前完成: {current_number}，总数: {total_players}")
        
        if player_number > total_players:
            return f"编号 {player_number} 不存在，当前系统中最大编号为 {total_players}"
        
        if player_number <= current_number:
            # 已完成，可以查看可视化
            return f"🎉 编号 {player_number} 已完成！\n\n回复 '查看图表-{player_number}' 来获取您的个人数据可视化图表\n\n回复 '对话-{player_number}-消息内容' 来和未来的你对话"
        else:
            # 未完成，计算等待时间
            remaining_count = player_number - current_number
            estimated_minutes = remaining_count * 3  # 平均每人3分钟
            
            return f"⏳ 编号 {player_number} 还未完成\n\n" \
                   f"您前面还有 {remaining_count} 人在排队\n" \
                   f"预计还需要等待约 {estimated_minutes} 分钟\n\n" \
                   f"系统会自动处理，请耐心等待 😊"

def handle_chat_with_future_self(message_content, user_id):
    """处理与未来自己对话的请求"""
    try:
        # 解析消息格式：对话-编号-消息内容
        if not message_content.startswith('对话-'):
            return "指令格式错误，请使用：对话-编号-消息内容"
        
        # 移除前缀
        content_part = message_content[3:]  # 移除 '对话-'
        
        # 分割编号和消息
        if '-' not in content_part:
            return "指令格式错误，请使用：对话-编号-消息内容"
        
        parts = content_part.split('-', 1)  # 只分割一次，保证消息内容可以包含“-”
        player_number = parts[0].strip()
        user_message = parts[1].strip()
        
        if not player_number or not user_message:
            return "请输入有效的编号和消息内容"
        
        try:
            player_number_int = int(player_number)
        except ValueError:
            return "请输入有效的数字编号"
        
        log_message(f"用户 {user_id} 请求与编号 {player_number} 的未来自己对话，消息: {user_message[:50]}...")
        
        # 检查是否已完成游戏
        with file_lock:
            data = read_data_file()
            if not data:
                return "系统数据暂时无法读取，请稍后再试"
            
            metadata = data.get('received_data', {}).get('metadata', {})
            current_number = metadata.get('current_number', 0)
            
            if player_number_int > current_number:
                return f"编号 {player_number} 尚未完成游戏，无法与未来自己对话"
        
        # 查找对应的玩家文件
        player_file = find_player_file_by_number(player_number)
        
        if not player_file:
            return f"未找到编号为 {player_number} 的玩家文件，请检查编号是否正确"
        
        # 加载玩家故事内容
        story_content = load_player_story_content(player_file)
        
        if not story_content:
            return f"无法读取玩家文件，请联系管理员"
        
        # 创建智谱AI对话实例
        try:
            chat = ZhipuChat(ZHIPU_API_KEY)
            
            # 设置系统提示
            system_prompt = f"你要扮演未来的我，和现在的我对话，这是你的经历：{story_content}"
            chat.add_message("system", system_prompt)
            
            # 发送用户消息并获取回复
            ai_reply = chat.chat(user_message)
            
            if ai_reply:
                log_message(f"成功为用户 {user_id} 生成AI回复，编号: {player_number}")
                
                # 格式化回复消息
                response_text = f"🤖 未来的你说：\n\n{ai_reply}\n\n💬 想继续对话？请再次使用：对话-{player_number}-你的消息"
                
                # 检查回复长度，微信消息有长度限制
                if len(response_text) > 2000:
                    response_text = f"🤖 未来的你说：\n\n{ai_reply[:1800]}...\n\n[回复过长，已截断]\n\n💬 想继续对话？请再次使用：对话-{player_number}-你的消息"
                
                return response_text
            else:
                return "😔 抱歉，未来的你暂时无法回应，请稍后再试"
                
        except Exception as e:
            log_message(f"创建智谱AI对话实例时出错: {str(e)}")
            return f"😔 AI服务暂时不可用，请稍后再试"
            
    except Exception as e:
        log_message(f"处理与未来自己对话请求时发生错误: {str(e)}")
        return "系统出现错误，请稍后再试"


def handle_generate_charts_request(message_content, user_id):
    """处理查看图表请求（查看预生成的图表）"""
    try:
        # 解析消息格式：查看图表-编号
        if not message_content.startswith('查看图表-'):
            return "指令格式错误，请使用：查看图表-编号"
        
        player_number = message_content.replace('查看图表-', '').strip()
        
        try:
            player_number = int(player_number)
        except ValueError:
            return "请输入有效的数字编号"
        
        # 检查是否已完成游戏
        with file_lock:
            data = read_data_file()
            if not data:
                return "系统数据暂时无法读取，请稍后再试"
            
            metadata = data.get('received_data', {}).get('metadata', {})
            current_number = metadata.get('current_number', 0)
            
            if player_number > current_number:
                return f"编号 {player_number} 尚未完成游戏，无法获取图表"
        
        # 检查是否存在已生成的可视化文件
        log_message(f"用户 {user_id} 请求查看编号 {player_number} 的图表")
        
        generated_files, message = check_existing_visualizations(player_number)
        
        if generated_files:
            # 找到了文件，返回下载链接
            return create_download_response(player_number, generated_files)
        else:
            # 未找到文件
            return f"🔍 编号 {player_number} 的可视化图表尚未生成\n\n" \
                   f"🕰️ 请稍后再试，或联系管理员检查生成状态\n\n" \
                   f"📝 错误信息: {message}"
            
    except Exception as e:
        error_msg = f"处理查看图表请求时发生错误: {str(e)}"
        log_message(error_msg)
        return "系统出现错误，请稍后再试"

def process_message(msg):
    """处理用户消息"""
    msg_type = msg.get('MsgType', '')
    content = msg.get('Content', '').strip()
    user_id = msg.get('FromUserName', '')
    
    log_message(f"收到消息: {content}", user_id)
    
    if msg_type == 'text':
        # 处理与未来自己对话请求
        if content.startswith('对话-'):
            return handle_chat_with_future_self(content, user_id)
        
        # 处理查看图表请求
        if content.startswith('查看图表-'):
            return handle_generate_charts_request(content, user_id)
        
        # 处理数字查询
        if content.isdigit():
            return query_player_status(content)
        
        # 处理帮助信息
        if content.lower() in ['help', '帮助', 'h']:
            return """🤖 使用说明:

1️⃣ 查询状态: 直接输入您的编号数字
   例如: 123

2️⃣ 查看图表: 输入 '查看图表-编号'
   例如: 查看图表-123

3️⃣ 与未来自己对话: 输入 '对话-编号-消息内容'
   例如: 对话-123-你现在过得怎么样？

4️⃣ 获取帮助: 输入 'help' 或 '帮助'

💡 Tips:
• 每个人平均处理时间约3分钟
• 完成后可查看个人数据可视化图表
• 可与基于您游戏经历的“未来自己”对话
• 图表包含资金、状态和轨迹动画"""
        
        # 默认回复
        return """👋 欢迎使用数据查询系统！

请输入您的编号数字来查询处理状态
或输入 'help' 获取使用说明

例如: 123

🎆 新功能：可与“未来的自己”对话！
使用格式：对话-编号-消息内容"""
    
    return "暂不支持该类型的消息"

@app.route('/wechat', methods=['GET', 'POST'])
def wechat_handler():
    """微信公众号消息处理入口"""
    log_message(f"收到请求: {request.method} {request.url}")
    log_message(f"请求参数: {dict(request.args)}")
    
    if request.method == 'GET':
        # 验证服务器配置
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        log_message(f"微信验证请求 - signature: {signature}, timestamp: {timestamp}, nonce: {nonce}, echostr: {echostr}")
        
        if verify_wechat_signature(signature, timestamp, nonce):
            log_message("微信签名验证成功")
            return echostr
        else:
            log_message("微信签名验证失败")
            return 'Invalid signature', 403
    
    elif request.method == 'POST':
        # 处理用户消息
        try:
            xml_data = request.get_data(as_text=True)
            msg = parse_xml_message(xml_data)
            
            if not msg:
                return 'Invalid message format', 400
            
            # 处理消息并生成回复
            response_content = process_message(msg)
            log_message(f"process_message 返回内容长度: {len(response_content) if response_content else 0}")
            log_message(f"回复内容前50字符: {response_content[:50] if response_content else 'None'}...")
            
            # 创建回复XML
            response_xml = create_text_response(
                msg.get('FromUserName', ''),
                msg.get('ToUserName', ''),
                response_content
            )
            
            log_message(f"XML回复生成成功，长度: {len(response_xml)}")
            log_message(f"XML前100字符: {response_xml[:100]}...")
            
            response = make_response(response_xml)
            response.content_type = 'application/xml; charset=utf-8'
            log_message(f"准备返回XML响应，Content-Type: {response.content_type}")
            return response
            
        except Exception as e:
            log_message(f"处理微信消息时发生错误: {str(e)}")
            return 'Internal server error', 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载生成的可视化文件"""
    try:
        # 安全检查，只允许下载特定格式的文件
        if not filename.endswith('.gif'):
            return "Invalid file type", 400
        
        # 检查文件是否存在
        output_dir = '../output_videos'
        file_path = os.path.join(output_dir, filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
        
        log_message(f"用户下载文件: {filename}")
        return send_from_directory(output_dir, filename, as_attachment=True)
        
    except Exception as e:
        log_message(f"下载文件失败: {str(e)}")
        return "Download failed", 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "WeChat bot is running"}

@app.route('/test', methods=['GET'])
def test_endpoint():
    """测试端点，用于验证服务是否正常运行"""
    log_message("收到测试请求")
    return f"WeChat Bot is running on port 80. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@app.route('/', methods=['GET'])
def root_endpoint():
    """根路径端点"""
    return "WeChat Bot Service is running. Use /wechat for WeChat integration."

@app.route('/status', methods=['GET'])
def get_status():
    """获取系统状态API"""
    with file_lock:
        data = read_data_file()
        if not data:
            return {"error": "Cannot read data file"}, 500
        
        metadata = data.get('received_data', {}).get('metadata', {})
        return {
            "current_number": metadata.get('current_number', 0),
            "total_players": metadata.get('total_players', 0),
            "last_updated": metadata.get('last_updated', ''),
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == '__main__':
    log_message("启动微信公众号服务...")
    log_message("请确保已正确配置WECHAT_TOKEN")
    log_message("微信公众号服务器URL: http://your-domain.com/wechat")
    
    # 检查必要的目录
    if not os.path.exists('received_files'):
        os.makedirs('received_files')
        log_message("创建 received_files 目录")
    
    if not os.path.exists('../output_videos'):
        os.makedirs('../output_videos')
        log_message("创建 output_videos 目录")
    
    app.run(host='0.0.0.0', port=80, debug=False)