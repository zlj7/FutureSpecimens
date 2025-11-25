import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict
import chardet

class InteractionActivityAnalyzer:
    """分析玩家在txt文件中与其他人的交流活跃度"""
    
    def __init__(self, received_files_dir):
        self.received_files_dir = received_files_dir
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(received_files_dir)), 'output_visualizations')
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 配置中文字体支持
        self.setup_chinese_font()
    
    def setup_chinese_font(self):
        """设置中文字体"""
        try:
            # 尝试使用系统中文字体
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        except:
            print("Warning: Chinese font not available, may display incorrectly")
    
    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            # 首先尝试UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return 'utf-8'
        except UnicodeDecodeError:
            try:
                # 尝试GBK编码
                with open(file_path, 'r', encoding='gbk') as f:
                    f.read()
                return 'gbk'
            except UnicodeDecodeError:
                # 使用chardet自动检测
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    return result['encoding'] if result['encoding'] else 'utf-8'
    
    def read_file_content(self, file_path):
        """读取文件内容，自动处理编码"""
        encoding = self.detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    def parse_txt_file(self, file_path):
        """
        解析txt文件，提取每回合的交流信息
        返回: {round_number: interaction_count}
        """
        content = self.read_file_content(file_path)
        if not content:
            return {}
        
        # 存储每回合的交流次数
        round_interactions = defaultdict(int)
        
        # 使用正则表达式查找所有的回合标记和交流事件
        # 匹配格式: [回合X]...进行交流 或 [VTX]...进行交流
        lines = content.split('\n')
        
        for line in lines:
            # 查找回合标记
            round_match = re.search(r'\[(?:回合|VT)(\d+)\]', line)
            
            if round_match:
                round_num = int(round_match.group(1))
                
                # 检查这一行是否包含"进行交流"
                if '进行交流' in line:
                    round_interactions[round_num] += 1
        
        return dict(round_interactions)
    
    def parse_all_txt_files(self):
        """解析目录下所有txt文件"""
        all_player_data = {}
        
        txt_files = [f for f in os.listdir(self.received_files_dir) if f.endswith('.txt')]
        
        for txt_file in txt_files:
            file_path = os.path.join(self.received_files_dir, txt_file)
            player_name = os.path.splitext(txt_file)[0]
            
            print(f"Processing {txt_file}...")
            interactions = self.parse_txt_file(file_path)
            
            if interactions:
                all_player_data[player_name] = interactions
        
        return all_player_data
    
    def create_interaction_curve(self, player_name, round_interactions):
        """为单个玩家创建交流活跃度曲线"""
        if not round_interactions:
            print(f"No interaction data for {player_name}")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 准备数据 - 填充所有回合（包括零交流的回合）
            min_round = min(round_interactions.keys())
            max_round = max(round_interactions.keys())
            
            # 创建完整的回合序列
            all_rounds = list(range(min_round, max_round + 1))
            all_interactions = [round_interactions.get(r, 0) for r in all_rounds]
            
            # 绘制曲线
            ax.plot(all_rounds, all_interactions, marker='o', linestyle='-', linewidth=2, markersize=6, color='#2E86AB')
            ax.fill_between(all_rounds, all_interactions, alpha=0.3, color='#2E86AB')
            
            # 设置标题和标签
            ax.set_title(f'{player_name} - 交流活跃度曲线', fontsize=16, fontweight='bold')
            ax.set_xlabel('回合数', fontsize=12)
            ax.set_ylabel('交流次数', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # 设置整数刻度
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            
            # 添加统计信息
            total_interactions = sum(all_interactions)
            rounds_with_interaction = sum(1 for x in all_interactions if x > 0)
            avg_interactions = total_interactions / rounds_with_interaction if rounds_with_interaction > 0 else 0
            max_interactions = max(all_interactions) if all_interactions else 0
            
            stats_text = f'总交流次数: {total_interactions}\n有交流的回合: {rounds_with_interaction}/{len(all_rounds)}\n平均每次: {avg_interactions:.1f}\n最高单回合: {max_interactions}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   fontsize=10)
            
            plt.tight_layout()
            
            # 保存图片
            output_path = os.path.join(self.output_dir, f'{player_name}_interaction_curve.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Created interaction curve: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating curve for {player_name}: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def create_comparison_chart(self, all_player_data):
        """创建所有玩家的交流活跃度对比图"""
        if not all_player_data:
            print("No data to create comparison chart")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(16, 8))
            
            # 为每个玩家绘制曲线
            colors = plt.cm.tab20(range(len(all_player_data)))
            
            for idx, (player_name, round_interactions) in enumerate(all_player_data.items()):
                rounds = sorted(round_interactions.keys())
                interactions = [round_interactions[r] for r in rounds]
                
                ax.plot(rounds, interactions, marker='o', linestyle='-', 
                       linewidth=1.5, markersize=4, label=player_name, 
                       color=colors[idx], alpha=0.7)
            
            # 设置标题和标签
            ax.set_title('所有玩家交流活跃度对比', fontsize=16, fontweight='bold')
            ax.set_xlabel('回合数', fontsize=12)
            ax.set_ylabel('交流次数', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            plt.tight_layout()
            
            # 保存图片
            output_path = os.path.join(self.output_dir, 'all_players_interaction_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Created comparison chart: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating comparison chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def create_total_activity_chart(self, all_player_data):
        """创建玩家总交流次数排行榜"""
        if not all_player_data:
            print("No data to create total activity chart")
            return None
        
        try:
            # 计算每个玩家的总交流次数
            player_totals = {}
            for player_name, round_interactions in all_player_data.items():
                player_totals[player_name] = sum(round_interactions.values())
            
            # 按交流次数排序
            sorted_players = sorted(player_totals.items(), key=lambda x: x[1], reverse=True)
            
            if not sorted_players:
                return None
            
            players, totals = zip(*sorted_players)
            
            fig, ax = plt.subplots(figsize=(12, max(6, len(players) * 0.3)))
            
            # 创建水平条形图
            bars = ax.barh(range(len(players)), totals, color='#A23B72')
            
            # 在条形上显示数值
            for i, (bar, total) in enumerate(zip(bars, totals)):
                ax.text(total, i, f' {total}', va='center', fontsize=9)
            
            # 设置标题和标签
            ax.set_yticks(range(len(players)))
            ax.set_yticklabels(players)
            ax.set_xlabel('总交流次数', fontsize=12)
            ax.set_title('玩家交流活跃度排行榜', fontsize=16, fontweight='bold')
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            
            # 保存图片
            output_path = os.path.join(self.output_dir, 'players_total_activity_ranking.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Created total activity chart: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating total activity chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def analyze_and_visualize(self):
        """执行完整的分析和可视化流程"""
        print("Starting interaction activity analysis...")
        
        # 解析所有txt文件
        all_player_data = self.parse_all_txt_files()
        
        if not all_player_data:
            print("No interaction data found in any files")
            return
        
        print(f"\nFound interaction data for {len(all_player_data)} players")
        
        # 为每个玩家创建单独的曲线图
        print("\nCreating individual interaction curves...")
        for player_name, round_interactions in all_player_data.items():
            self.create_interaction_curve(player_name, round_interactions)
        
        # 创建对比图
        print("\nCreating comparison chart...")
        self.create_comparison_chart(all_player_data)
        
        # 创建排行榜
        print("\nCreating total activity ranking...")
        self.create_total_activity_chart(all_player_data)
        
        print(f"\nAll visualizations saved to: {self.output_dir}")
        print("Analysis complete!")


if __name__ == "__main__":
    # 设置received_files目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    received_files_dir = os.path.join(script_dir, '..', 'received_files')
    
    # 创建分析器并执行分析
    analyzer = InteractionActivityAnalyzer(received_files_dir)
    analyzer.analyze_and_visualize()
