from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
from threading import Lock
from visualization.data_visualizer import DataVisualizer

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


# 不生成图表的文件名列表（不含后缀）
SKIP_VISUALIZATION_LIST = [
    "Dr. Paul Farmer", "DrSmith", "ElonMusk", "Huhu", 
    "Lin", "Rubin Carter", "Ya", "Zoe"
]

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
                    "description": "从主服务器接收的玩家数据存储",
                    "version": "1.0",
                    "total_players": 0,
                    "current_number": 0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "color_info": "R、G、B字段表示玩家的颜色属性，取值范围为0-255整数"
                }
            },
            "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_server": "unknown"
        }

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)


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


def generate_visualizations_for_files(save_dir):
    """为新保存的CSV文件生成可视化图表"""
    try:
        # 获取所有CSV文件
        csv_files = [f for f in os.listdir(save_dir) if f.endswith('.csv')]
        
        generated_count = 0
        skipped_count = 0
        
        for csv_file in csv_files:
            # 检查文件名（不含后缀）是否在跳过列表中
            filename_without_ext = os.path.splitext(csv_file)[0]
            # 去除可能的编号前缀（如 "0_@zlj.csv" -> "@zlj"）
            if '_@' in filename_without_ext:
                actual_name = filename_without_ext.split('_@', 1)[1]
            elif '_' in filename_without_ext:
                actual_name = filename_without_ext.split('_', 1)[1]
            else:
                actual_name = filename_without_ext
            
            if actual_name in SKIP_VISUALIZATION_LIST:
                log_message(f"跳过为 {csv_file} 生成可视化图表（在跳过列表中）")
                skipped_count += 1
                continue
            
            csv_file_path = os.path.join(save_dir, csv_file)
            
            # 检查可视化文件是否已经存在
            csv_basename = os.path.basename(csv_file)
            output_dir = "output_videos"  # DataVisualizer使用的输出目录
            
            # 定义需要检查的可视化文件列表
            expected_files = [
                os.path.join(output_dir, f"{csv_basename}_money_video.gif"),
                os.path.join(output_dir, f"{csv_basename}_body_state_video.gif"),
                os.path.join(output_dir, f"{csv_basename}_mind_state_video.gif"),
                os.path.join(output_dir, f"{csv_basename}_movement_video.gif")
            ]
            
            # 检查是否所有可视化文件都已存在
            all_files_exist = all(os.path.exists(file_path) for file_path in expected_files)
            
            if all_files_exist:
                log_message(f"跳过为 {csv_file} 生成可视化图表（所有可视化文件已存在）")
                skipped_count += 1
                continue
            
            log_message(f"开始为 {csv_file} 生成可视化图表...")
            
            try:
                visualizer = DataVisualizer(csv_file_path)
                
                # 生成三个数值变化的GIF
                value_gifs = visualizer.create_all_value_gifs(duration=8)
                gif_count = len([gif for gif in value_gifs if gif is not None])
                
                # 生成行动轨迹视频
                movement_video = visualizer.create_movement_video(duration=8)
                if movement_video:
                    gif_count += 1
                
                log_message(f"成功为 {csv_file} 生成 {gif_count} 个可视化文件")
                generated_count += 1
                
            except Exception as e:
                log_message(f"为 {csv_file} 生成可视化图表时出错: {str(e)}")
        
        log_message(f"可视化生成完成：成功 {generated_count} 个，跳过 {skipped_count} 个")
        return generated_count, skipped_count
        
    except Exception as e:
        log_message(f"生成可视化图表时发生错误: {str(e)}")
        return 0, 0
def write_data_file(data):
    """写入数据文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/receive_transferred_data', methods=['POST'])
def receive_transferred_data():
    """接收从主服务器传输过来的完整数据并完全替换本地数据"""
    try:
        log_message(f"接收到来自主服务器的数据传输请求", request.remote_addr)
        
        # 获取主服务器发送的数据
        transferred_data = request.get_json()
        
        # 验证数据格式
        if not transferred_data or 'status' not in transferred_data or transferred_data['status'] != 'success':
            log_message(f"无效的数据传输请求: {transferred_data}", request.remote_addr)
            return jsonify({
                "status": "error",
                "message": "Invalid data transfer request"
            }), 400
        
        # 检查是否为完整复制模式
        transfer_type = transferred_data.get('transfer_type', 'partial')
        
        # 获取实际的数据
        received_data = transferred_data['data']
        
        # 检查是否有文件数据需要保存
        files_received = transferred_data.get('files', [])
        saved_files_count = 0
        
        # 创建保存文件的目录
        save_dir = "received_files"
        os.makedirs(save_dir, exist_ok=True)
        
        # 处理并保存每个文件
        for file_info in files_received:
            try:
                filename = file_info.get('filename')
                file_content_hex = file_info.get('content')
                
                if filename and file_content_hex:
                    # 将十六进制字符串转换回二进制数据
                    file_content = bytes.fromhex(file_content_hex)
                    
                    # 保存文件到本地
                    file_path = os.path.join(save_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(file_content)
                    
                    saved_files_count += 1
                    log_message(f"成功保存文件: {filename}", request.remote_addr)
            except Exception as e:
                log_message(f"保存文件时发生错误: {str(e)}", request.remote_addr)
        
        # 为新保存的CSV文件生成可视化图表
        viz_generated, viz_skipped = 0, 0
        if saved_files_count > 0:
            log_message(f"开始为新保存的文件生成可视化图表...", request.remote_addr)
            viz_generated, viz_skipped = generate_visualizations_for_files(save_dir)
        
        with file_lock:
            if transfer_type == 'full_copy':
                # 完整复制模式：完全替换本地数据
                log_message(f"完整复制模式：完全替换本地数据", request.remote_addr)
                
                # 完全使用主服务器的数据结构
                new_data = {
                    "received_data": received_data,
                    "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_server": request.remote_addr,
                    "transfer_type": "full_copy"
                }
                
                # 写入新数据
                write_data_file(new_data)
                
                total_players = len(received_data['players'])
                log_message(f"完整数据复制成功，总玩家数: {total_players}", request.remote_addr)
                
                return jsonify({
                    "status": "success",
                    "message": "Complete data copy received and saved successfully",
                    "total_players": total_players,
                    "saved_files_count": saved_files_count,
                    "visualizations_generated": viz_generated,
                    "visualizations_skipped": viz_skipped,
                    "transfer_type": "full_copy"
                })
            else:
                # 原有的增量模式（保持兼容性）
                log_message(f"增量模式：合并数据到本地", request.remote_addr)
                
                # 读取本地现有数据
                local_data = read_data_file()
                
                # 合并接收到的玩家数据到本地数据中
                existing_players = local_data['received_data']['players']
                new_players = received_data['players']
                
                # 为新玩家分配新的编号
                current_max_number = max((player.get('Number', -1) for player in existing_players), default=-1)
                for i, player in enumerate(new_players):
                    player['Number'] = current_max_number + i + 1
                    player['Timestamp'] = datetime.now().isoformat()
                    existing_players.append(player)
                
                # 更新元数据
                metadata = local_data['received_data']['metadata']
                metadata['total_players'] = len(existing_players)
                metadata['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 更新接收时间和来源服务器
                local_data['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                local_data['source_server'] = request.remote_addr
                
                # 写回更新后的数据
                write_data_file(local_data)
                
                log_message(f"成功接收并保存 {len(new_players)} 个玩家数据，本地总玩家数: {len(local_data['received_data']['players'])}", request.remote_addr)
                return jsonify({
                    "status": "success",
                    "message": "Player data and files received and saved successfully",
                    "received_count": len(new_players),
                    "total_count": len(local_data['received_data']['players']),
                    "saved_files_count": saved_files_count,
                    "visualizations_generated": viz_generated,
                    "visualizations_skipped": viz_skipped,
                    "transfer_type": "incremental"
                })
    
    except Exception as e:
        import traceback
        log_message(f"接收数据时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    log_message(f"健康检查请求", request.remote_addr)
    return jsonify({"status": "ok", "message": "Remote server is running"})


@app.route('/get_all_player_data', methods=['GET'])
def get_all_player_data():
    """获取所有玩家数据（用于测试）"""
    try:
        log_message(f"接收到获取所有玩家数据请求", request.remote_addr)
        with file_lock:
            data = read_data_file()
        log_message(f"返回所有玩家数据成功", request.remote_addr)
        return jsonify(data)
    except Exception as e:
        import traceback
        log_message(f"获取所有玩家数据时发生错误: {str(e)}", request.remote_addr)
        log_message(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


if __name__ == '__main__':
    # 初始化数据文件
    initialize_data_file()
    
    # 服务器监听端口
    server_port = 10002
    
    # 启动服务器
    log_message(f"启动远程服务器，监听端口 {server_port}")
    app.run(host='0.0.0.0', port=server_port, debug=False)