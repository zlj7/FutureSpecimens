from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os
from threading import Lock

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据文件路径
DATA_FILE = "data.json"
# 线程锁，确保多线程安全写入
file_lock = Lock()


# 配置标准输出流的编码为UTF-8
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 记录请求日志的辅助方法
def log_message(message, client_ip=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_info = f"[Client: {client_ip}]" if client_ip else ""
    print(f"{timestamp} {client_info} {message}")


def initialize_data_file():
    """初始化数据文件，如果文件不存在则创建"""
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "received_data": {
                "players": [],
                "metadata": {
                    "description": "玩家数据存储",
                    "version": "1.0",
                    "total_players": 0,
                    "current_number": 0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "color_info": "R、G、B字段表示玩家的颜色属性，取值范围为0-255整数"
                }
            },
            "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_server": "http://localhost:10001/save_player_data"
        }

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)


# 检查端口是否被占用
def check_port_available(host='0.0.0.0', port=10001):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False


def read_data_file():
    """读取数据文件"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_message(f"JSON解析错误: {str(e)}")
        # 如果文件损坏，返回初始化结构
        return {
            "received_data": {
                "players": [],
                "metadata": {
                    "total_players": 0,
                    "current_number": 0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        }


def write_data_file(data):
    """写入数据文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/')
def serve_game():
    """提供game.html文件"""
    log_message(f"请求根路径 - 客户端IP: {request.remote_addr}")
    try:
        return send_from_directory('.', 'game.html')
    except Exception as e:
        log_message(f"提供game.html失败: {str(e)}")
        return jsonify({"status": "error", "message": "无法提供游戏页面"}), 404


@app.route('/save_player_data', methods=['POST'])
def save_player_data():
    """接收并保存玩家数据到data.json"""
    try:
        # 获取前端发送的数据
        player_data = request.get_json()
        log_message(f"接收到玩家数据请求: {player_data}", request.remote_addr)

        # 验证必要字段
        required_fields = ['R', 'G', 'B', 'Player Money', 'Player Body State']
        for field in required_fields:
            if field not in player_data:
                log_message(f"缺少必要字段: {field}", request.remote_addr)
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400

        # 使用线程锁确保文件读写安全
        with file_lock:
            # 读取现有数据
            data = read_data_file()

            # 获取下一个编号
            next_number = data['received_data']['metadata']['total_players']

            # 构建完整的玩家数据对象
            complete_player_data = {
                "Player Name": f"Player_{next_number}",
                "Player Money": player_data['Player Money'],
                "Player Age": 18,
                "Player Body State": player_data['Player Body State'],
                "Player Mind State": 100,
                "PlayerIQ": 120,
                "Player El": 120,
                "R": player_data['R'],
                "G": player_data['G'],
                "B": player_data['B'],
                "Additional Info": "游戏生成的玩家数据",
                "Number": next_number,
                "Timestamp": datetime.now().isoformat()
            }

            # 添加玩家数据
            data['received_data']['players'].append(complete_player_data)
            data['received_data']['metadata']['total_players'] = data['received_data']['metadata']['total_players'] + 1

            # 更新元数据
            # data['received_data']['metadata']['total_players'] = len(data['received_data']['players'])
            # data['received_data']['metadata']['current_number'] = len(data['received_data']['players'])
            data['received_data']['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 写回文件
            write_data_file(data)

        log_message(f"玩家数据保存成功，编号: {next_number}", request.remote_addr)
        return jsonify({
            "status": "success",
            "message": "Player data saved successfully",
            "player_number": next_number
        })

    except Exception as e:
        import traceback
        log_message(f"保存玩家数据时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route('/get_player_data', methods=['GET'])
def get_player_data():
    """获取所有玩家数据"""
    try:
        log_message(f"接收到获取玩家数据请求", request.remote_addr)
        with file_lock:
            data = read_data_file()
        log_message(f"返回玩家数据成功", request.remote_addr)
        return jsonify(data)
    except Exception as e:
        import traceback
        log_message(f"获取玩家数据时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route('/transfer_player_data', methods=['POST'])
def transfer_player_data():
    """根据请求中的数量发送指定数量的玩家数据，并删除这些数据"""
    try:
        log_message(f"接收到数据传输请求", request.remote_addr)

        # 获取请求中的样本数量参数
        request_data = request.get_json()
        if not request_data or 'CanGenerateAgantNum' not in request_data:
            return jsonify({
                "status": "error",
                "message": "Missing or invalid 'CanGenerateAgantNum' parameter"
            }), 400

        num_samples = request_data['CanGenerateAgantNum']

        with file_lock:
            # 读取当前数据
            current_data = read_data_file()
            all_players = current_data['received_data']['players']

            # 如果请求的样本数量超过可用数量，则调整实际提取数量
            if num_samples > len(all_players):
                actual_samples = len(all_players)
                log_message(f"请求 {num_samples} 个样本，但只有 {actual_samples} 个可用，返回所有可用样本", request.remote_addr)
            else:
                actual_samples = num_samples

            # 提取指定数量的样本（从前端开始取）
            samples_to_send = all_players[:actual_samples]
            remaining_players = all_players[actual_samples:]

            # 构建要返回的数据
            response_data = {
                "status": "success",
                "data": {
                    "players": samples_to_send,
                    "metadata": current_data['received_data']['metadata']
                },
                "requested_samples": num_samples,  # 记录请求的样本数量
                "actual_samples": actual_samples  # 记录实际返回的样本数量
            }

            # 更新元数据
            metadata = current_data['received_data']['metadata']
            # new_total_players = metadata['total_players'] - actual_samples

            # 创建新的数据结构，只保留剩余玩家，更新metadata
            new_data = {
                "received_data": {
                    "players": remaining_players,
                    "metadata": {
                        "description": metadata['description'],
                        "version": metadata['version'],
                        "total_players": metadata['total_players'],
                        "current_number": metadata['current_number'] + actual_samples,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "color_info": metadata['color_info']
                    }
                },
                "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source_server": current_data['source_server']
            }

            # 写回更新后的数据（已删除发送的样本）
            write_data_file(new_data)

        log_message(f"成功发送 {actual_samples} 个玩家数据样本，本地剩余 {len(remaining_players)} 个玩家", request.remote_addr)
        return jsonify(response_data)

    except Exception as e:
        import traceback
        log_message(f"数据传输时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    log_message(f"健康检查请求", request.remote_addr)
    return jsonify({"status": "ok", "message": "Server is running"})


# 添加静态文件服务，以便提供CSS、JS等资源
@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    log_message(f"请求静态文件: {filename}", request.remote_addr)
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        log_message(f"提供静态文件{filename}失败: {str(e)}", request.remote_addr)
        return jsonify({"status": "error", "message": "无法提供静态文件"}), 404


if __name__ == '__main__':
    # 初始化数据文件
    initialize_data_file()

    # 选择服务器模式：production（生产模式）或 development（开发模式）
    # production 模式：只启动一个进程，没有自动重载功能
    # development 模式：启动两个进程，有自动重载功能
    server_mode = "production"  # 可以改为 "development"

    if server_mode == "development":
        # 开发模式 - 使用debug=True但不进行端口检查（因为Flask会启动两个进程）
        log_message(f"开发模式: 启动服务器，监听端口 10001 (debug=True)")
        app.run(host='0.0.0.0', port=10001, debug=True)
    else:
        # 生产模式 - 进行端口检查并使用debug=False
        if check_port_available(port=10001):
            log_message(f"生产模式: 服务器启动成功，监听端口 10001")
            app.run(host='0.0.0.0', port=10001, debug=False)
        else:
            log_message(f"错误: 端口 10001 已被占用")
            # 尝试使用备用端口
            alt_port = 10002
            if check_port_available(port=alt_port):
                log_message(f"尝试使用备用端口 {alt_port}")
                app.run(host='0.0.0.0', port=alt_port, debug=False)
            else:
                log_message(f"错误: 备用端口 {alt_port} 也已被占用")
                sys.exit(1)

# 错误处理辅助方法
def _send_error_response(message, status_code=400):
    log_message(f"发送错误响应: {message} (状态码: {status_code})")
    return jsonify({"status": "error", "message": message}), status_code