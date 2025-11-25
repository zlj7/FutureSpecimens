from flask import Flask, request, jsonify, send_from_directory
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os
from threading import Lock
import sys
import io

# 获取当前脚本或可执行文件的目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置标准输出流的编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据文件路径
DATA_FILE = os.path.join(BASE_DIR, "data.json")
# 线程锁，确保多线程安全写入
file_lock = Lock()


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
        # 使用正确的基础目录
        game_html_path = os.path.join(BASE_DIR, 'game.html')
        log_message(f"尝试提供文件: {game_html_path}")
        
        if os.path.exists(game_html_path):
            return send_from_directory(BASE_DIR, 'game.html')
        else:
            log_message(f"game.html文件不存在: {game_html_path}")
            return jsonify({"status": "error", "message": "游戏页面文件不存在"}), 404
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
                "Player Name": f"{next_number}_@{player_data['Player Name']}",
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
    """复制完整的data.json数据到远程服务器，不删除本地数据"""
    try:
        log_message(f"接收到数据传输请求", request.remote_addr)

        # 获取请求参数（保持接口兼容性）
        request_data = request.get_json()
        if not request_data:
            request_data = {}
        
        # 检查是否是UE游戏请求，以及是否有数据需要发送
        is_ue_game_request = 'CanGenerateAgantNum' in request_data
        should_send_to_cloud = False
        
        if is_ue_game_request:
            # 检查是否有数据可以发送给UE游戏
            with file_lock:
                current_data = read_data_file()
                available_players = current_data['received_data']['players']
                
            if len(available_players) > 0:
                should_send_to_cloud = True
                log_message(f"UE游戏请求且有 {len(available_players)} 个玩家数据，需要先向云服务器传输", request.remote_addr)
            else:
                log_message(f"UE游戏请求但没有可用的玩家数据，跳过云服务器传输", request.remote_addr)
        
        # 如果不需要向云服务器传输，直接处理UE游戏请求（如果有）
        if not should_send_to_cloud:
            if is_ue_game_request:
                # 直接处理UE游戏请求，不进行云服务器传输
                with file_lock:
                    current_data = read_data_file()
                
                response_data = {
                    "status": "success",
                    "data": current_data['received_data'],
                    "transfer_type": "no_cloud_transfer",
                    "total_players": len(current_data['received_data']['players']),
                    "files_count": 0,
                    "cloud_transfer_skipped": True
                }
                
                # 仍然处理UE游戏数据请求
                num_samples = request_data['CanGenerateAgantNum']
                all_players = current_data['received_data']['players']
                
                response_data.update({
                    "ue_game_data": {
                        "players": [],
                        "metadata": current_data['received_data']['metadata']
                    },
                    "requested_samples": num_samples,
                    "actual_samples": 0,
                    "message": "No data available for UE game"
                })
                
                return jsonify(response_data)
            else:
                # 非UE游戏请求且不需要传输，直接返回
                with file_lock:
                    current_data = read_data_file()
                
                return jsonify({
                    "status": "success",
                    "message": "No transfer needed",
                    "total_players": len(current_data['received_data']['players']),
                    "files_count": 0,
                    "cloud_transfer_skipped": True
                })
        
        # === 需要向云服务器传输的情况 ===
        log_message(f"开始执行云服务器传输流程", request.remote_addr)
        
        # 收集 C:\output 路径下的 csv 和 txt 文件
        files_to_transfer = []
        output_path = "C:\\output"
        
        try:
            if os.path.exists(output_path):
                for filename in os.listdir(output_path):
                    file_path = os.path.join(output_path, filename)
                    if os.path.isfile(file_path) and filename.lower().endswith(('.csv', '.txt')):
                        try:
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                            files_to_transfer.append({
                                'filename': filename,
                                'content': file_content.hex()  # 将二进制文件转换为十六进制字符串传输
                            })
                            log_message(f"成功读取文件: {filename}")
                        except Exception as e:
                            log_message(f"读取文件 {filename} 失败: {str(e)}")
                log_message(f"总共收集到 {len(files_to_transfer)} 个文件用于传输")
            else:
                log_message(f"C:\\output 路径不存在，跳过文件传输")
        except Exception as e:
            log_message(f"收集文件时发生异常: {str(e)}")

        with file_lock:
            # 读取完整的当前数据（传输前的数据）
            current_data = read_data_file()

            # 构建要返回的数据（完整复制）
            response_data = {
                "status": "success",
                "data": current_data['received_data'],  # 传输完整数据
                "transfer_type": "full_copy",  # 标记为完整复制
                "total_players": len(current_data['received_data']['players']),
                "files_count": len(files_to_transfer),  # 添加文件数量信息
                "cloud_transfer_executed": True
            }

        log_message(f"成功读取完整数据，包含 {len(current_data['received_data']['players'])} 个玩家，准备传输 {len(files_to_transfer)} 个文件", request.remote_addr)

        # 先向云服务器发送当前的data.json数据
        try:
            import requests
            remote_server_url = "http://47.118.21.234:10002/receive_transferred_data"
            log_message(f"开始将完整数据发送到远程服务器: {remote_server_url}")

            # 发送完整数据结构，包含玩家数据和文件数据
            send_data = {
                "status": "success",
                "data": current_data['received_data'],  # 传输完整数据
                "transfer_type": "full_copy",
                "total_players": len(current_data['received_data']['players']),
                "files": files_to_transfer  # 添加收集到的文件数据
            }

            # 设置超时为30秒
            response = requests.post(remote_server_url, json=send_data, timeout=30)
            
            log_message(f"远程服务器响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    remote_response = response.json()
                    log_message(f"完整数据成功发送到远程服务器，远程服务器响应: {remote_response}")
                except Exception as json_error:
                    log_message(f"解析远程服务器JSON响应失败: {str(json_error)}")
            else:
                log_message(f"发送数据到远程服务器失败，状态码: {response.status_code}, 响应: {response.text}")
                
        except Exception as e:
            log_message(f"发送数据到远程服务器时发生异常: {str(e)}")
        
        # 清空C:\output下的文件
        if len(files_to_transfer) > 0:
            log_message(f"开始清空 C:\\output 中的 {len(files_to_transfer)} 个文件")
            try:
                files_deleted = 0
                for filename in os.listdir(output_path):
                    file_path = os.path.join(output_path, filename)
                    if os.path.isfile(file_path) and filename.lower().endswith(('.csv', '.txt')):
                        try:
                            os.remove(file_path)
                            files_deleted += 1
                            log_message(f"成功删除文件: {filename}")
                        except Exception as e:
                            log_message(f"删除文件 {filename} 失败: {str(e)}")
                log_message(f"总共删除了 {files_deleted} 个文件")
            except Exception as e:
                log_message(f"清空 C:\\output 文件夹时发生异常: {str(e)}")
        else:
            log_message(f"没有文件需要删除")

        # === 云服务器传输完成后，处理UE游戏请求 ===
        if is_ue_game_request:
            try:
                num_samples = request_data['CanGenerateAgantNum']
                log_message(f"云服务器传输完成，现在处理UE游戏请求 {num_samples} 个样本数据", request.remote_addr)
                
                with file_lock:
                    # 重新读取当前数据（使用传输前的数据进行UE游戏处理）
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
                    
                    # 更新元数据
                    metadata = current_data['received_data']['metadata']
                    
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
                
                # 更新响应数据，添加UE游戏相关信息
                response_data.update({
                    "ue_game_data": {
                        "players": samples_to_send,
                        "metadata": current_data['received_data']['metadata']
                    },
                    "requested_samples": num_samples,
                    "actual_samples": actual_samples
                })
                
                log_message(f"成功发送 {actual_samples} 个玩家数据样本给UE游戏，本地剩余 {len(remaining_players)} 个玩家", request.remote_addr)
                
            except Exception as e:
                log_message(f"UE游戏数据处理时发生错误: {str(e)}", request.remote_addr)
                # UE游戏处理错误不影响云服务器的成功结果
                response_data["ue_game_error"] = str(e)

        return jsonify(response_data)

    except Exception as e:
        import traceback
        log_message(f"数据传输时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route('/get_queue_status', methods=['GET'])
def get_queue_status():
    """获取队列状态信息，从本地data.json读取玩家数据计算队列"""
    try:
        log_message(f"接收到获取队列状态请求", request.remote_addr)
        
        # 读取本地的data.json文件（用户的数据保存在这里）
        local_data_file = DATA_FILE  # 使用全局定义的DATA_FILE
        log_message(f"尝试读取数据文件: {local_data_file}")
        
        if os.path.exists(local_data_file):
            with file_lock:
                data = read_data_file()
            
            # 从本地data.json获取玩家数据
            players = data.get('received_data', {}).get('players', [])
            total_players = len(players)  # 总玩家数 = 实际玩家数量
            current_number = 1  # 当前处理的编号，从1开始
            
            # 计算等待人数：total_players - current_number
            queue_count = max(0, total_players - current_number)
            
            # 计算等待时间：等待人数 × 3分钟
            wait_minutes = queue_count * 3
            
            # 格式化等待时间显示
            if wait_minutes == 0:
                wait_time_text = "无需等待"
            elif wait_minutes <= 60:
                wait_time_text = f"{wait_minutes}分钟"
            else:
                hours = wait_minutes // 60
                minutes = wait_minutes % 60
                if minutes == 0:
                    wait_time_text = f"{hours}小时"
                else:
                    wait_time_text = f"{hours}小时{minutes}分钟"
            
            queue_status = {
                "queue_count": queue_count,
                "wait_time_text": wait_time_text,
                "wait_minutes": wait_minutes,
                "current_number": current_number,
                "total_players": total_players
            }
            
            log_message(f"队列状态: 排队{queue_count}人, 等待时间{wait_time_text} (总玩家:{total_players})", request.remote_addr)
            return jsonify({
                "status": "success",
                **queue_status
            })
        else:
            log_message(f"本地data.json文件不存在", request.remote_addr)
            return jsonify({
                "status": "error",
                "message": "Queue data not available",
                "queue_count": 0,
                "wait_time_text": "数据不可用",
                "wait_minutes": 0
            })
            
    except Exception as e:
        import traceback
        log_message(f"获取队列状态时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "queue_count": 0,
            "wait_time_text": "计算错误",
            "wait_minutes": 0
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
        # 使用正确的基础目录
        file_path = os.path.join(BASE_DIR, filename)
        log_message(f"尝试提供文件: {file_path}")
        
        if os.path.exists(file_path):
            return send_from_directory(BASE_DIR, filename)
        else:
            log_message(f"文件不存在: {file_path}")
            return jsonify({"status": "error", "message": "文件不存在"}), 404
    except Exception as e:
        log_message(f"提供静态文件{filename}失败: {str(e)}", request.remote_addr)
        return jsonify({"status": "error", "message": "无法提供静态文件"}), 404


if __name__ == '__main__':
    # 输出基础目录信息
    log_message(f"当前基础目录: {BASE_DIR}")
    log_message(f"数据文件路径: {DATA_FILE}")
    
    # 检查关键文件是否存在
    game_html_path = os.path.join(BASE_DIR, 'game.html')
    if os.path.exists(game_html_path):
        log_message(f"game.html文件存在: {game_html_path}")
    else:
        log_message(f"警告: game.html文件不存在: {game_html_path}")
    
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