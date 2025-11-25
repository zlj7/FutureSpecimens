import pandas as pd
import matplotlib
# 设置matplotlib使用非交互式后端，避免在非主线程中出现问题
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os
from matplotlib.ticker import FuncFormatter
import cv2

class DataVisualizer:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.data = self.load_data()
        # 设置输出目录为项目根目录下的output_videos
        # 从cloud目录调用时，需要正确设置路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 如果当前在cloud/visualization目录，则向上两级到项目根目录
        if 'cloud' in current_dir and 'visualization' in current_dir:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'output_videos')
        else:
            # 原有逻辑保持不变
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'output_videos')
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def load_data(self):
        # 读取CSV文件，跳过第0行，从第1行开始读取数据
        columns = ['round', 'money', 'body_state', 'mind_state', 'x', 'y', 'z']
        df = pd.read_csv(self.csv_file_path, header=None, names=columns, skiprows=1)
        return df
    
    def format_money(self, value, pos):
        # 将金钱格式化为更易读的形式
        if value >= 1000000:
            return f'{value/1000000:.1f}M'
        elif value >= 1000:
            return f'{value/1000:.1f}K'
        return f'{value}'
    
    def create_single_value_gif(self, value_name, color, duration=10):
        """为单个数值创建GIF动画"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # 设置图表样式
            titles = {
                'money': 'Money Over Time',
                'body_state': 'Body State Over Time',
                'mind_state': 'Mind State Over Time'
            }
            
            ax.set_title(titles.get(value_name, f'{value_name} Over Time'), fontsize=16)
            ax.set_xlabel('Round', fontsize=12)
            ax.set_ylabel(value_name.replace('_', ' ').title(), fontsize=12)
            
            # 为金钱设置特殊的格式化器
            if value_name == 'money':
                money_formatter = FuncFormatter(self.format_money)
                ax.yaxis.set_major_formatter(money_formatter)
            
            # 设置数据点数量和帧率
            num_frames = duration * 30  # 假设30fps
            
            # 初始化线条
            line, = ax.plot([], [], f'{color}-', linewidth=2)
            
            # 设置坐标轴范围
            ax.set_xlim(0, self.data['round'].max())
            ax.set_ylim(self.data[value_name].min() * 0.9, self.data[value_name].max() * 1.1)
            
            # 初始化函数
            def init():
                line.set_data([], [])
                return (line,)
            
            # 更新函数
            def update(frame):
                # 计算当前应该显示到哪一行数据
                progress = frame / num_frames
                last_idx = min(int(len(self.data) * progress), len(self.data) - 1)
                
                # 更新线条数据
                line.set_data(self.data['round'][:last_idx+1], self.data[value_name][:last_idx+1])
                
                return (line,)
            
            # 创建动画
            ani = animation.FuncAnimation(
                fig, update, init_func=init, frames=num_frames,
                interval=1000/30, blit=True
            )
            
            # 保存为GIF格式
            gif_path = os.path.join(self.output_dir, f'{os.path.basename(self.csv_file_path)}_{value_name}_video.gif')
            ani.save(gif_path, writer='pillow', fps=30)
            
            # 关闭图形以释放内存
            plt.close(fig)
            
            return gif_path
            
        except Exception as e:
            print(f"创建 {value_name} GIF 动画时出错: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
        
    def create_all_value_gifs(self, duration=10):
        """为钱、身体状态、心理状态三个数值分别创建GIF动画"""
        gif_paths = []
        
        # 创建钱的GIF
        money_gif = self.create_single_value_gif('money', 'r', duration)
        if money_gif:
            gif_paths.append(money_gif)
        
        # 创建身体状态的GIF
        body_gif = self.create_single_value_gif('body_state', 'g', duration)
        if body_gif:
            gif_paths.append(body_gif)
        
        # 创建心理状态的GIF
        mind_gif = self.create_single_value_gif('mind_state', 'b', duration)
        if mind_gif:
            gif_paths.append(mind_gif)
        
        return gif_paths
    
    def create_movement_video(self, duration=10):
        """创建俯视角行动轨迹视频"""
        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # 设置图表样式
            ax.set_title('Player Movement Trajectory', fontsize=16)
            ax.set_xlabel('X Coordinate', fontsize=12)
            ax.set_ylabel('Y Coordinate', fontsize=12)
            ax.grid(True)
            
            # 设置数据点数量和帧率
            num_frames = duration * 30  # 假设30fps
            
            # 初始化轨迹线和当前位置点
            trajectory_line, = ax.plot([], [], 'b-', label='Trajectory', linewidth=1)
            current_point, = ax.plot([], [], 'ro', markersize=8, label='Current Position')
            
            # 设置图例
            ax.legend(loc='best')
            
            # 设置坐标轴范围，留出一些边距
            x_min, x_max = self.data['x'].min(), self.data['x'].max()
            y_min, y_max = self.data['y'].min(), self.data['y'].max()
            x_margin = (x_max - x_min) * 0.1
            y_margin = (y_max - y_min) * 0.1
            ax.set_xlim(x_min - x_margin, x_max + x_margin)
            ax.set_ylim(y_min - y_margin, y_max + y_margin)
            
            # 初始化函数
            def init():
                trajectory_line.set_data([], [])
                current_point.set_data([], [])
                return trajectory_line, current_point
            
            # 更新函数
            def update(frame):
                # 计算当前应该显示到哪一行数据
                progress = frame / num_frames
                last_idx = min(int(len(self.data) * progress), len(self.data) - 1)
                
                # 更新轨迹和当前位置
                trajectory_line.set_data(self.data['x'][:last_idx+1], self.data['y'][:last_idx+1])
                
                if last_idx < len(self.data):
                    current_point.set_data([self.data['x'].iloc[last_idx]], [self.data['y'].iloc[last_idx]])
                
                return trajectory_line, current_point
            
            # 创建动画
            ani = animation.FuncAnimation(
                fig, update, init_func=init, frames=num_frames,
                interval=1000/30, blit=True
            )
            
            # 保存为GIF格式，不依赖ffmpeg
            video_path = os.path.join(self.output_dir, f'{os.path.basename(self.csv_file_path)}_movement_video.gif')
            ani.save(video_path, writer='pillow', fps=30)
            
            # 关闭图形以释放内存
            plt.close(fig)
            
            return video_path
            
        except Exception as e:
            print(f"创建行动轨迹视频时出错: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None

if __name__ == "__main__":
    # 示例使用
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 计算CSV文件目录的绝对路径
    csv_files_dir = os.path.join(script_dir, '..', 'received_files')
    
    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(csv_files_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_file_path = os.path.join(csv_files_dir, csv_file)
        print(f"Processing {csv_file}...")
        
        try:
            visualizer = DataVisualizer(csv_file_path)
            
            # 创建三个数值变化的GIF
            value_gifs = visualizer.create_all_value_gifs()
            for gif_path in value_gifs:
                print(f"Value GIF created: {gif_path}")
            
            # 创建行动轨迹视频
            movement_video = visualizer.create_movement_video()
            print(f"Movement video created: {movement_video}")
            
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")