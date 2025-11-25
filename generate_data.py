import json
import random
from datetime import datetime

def generate_player_data(count=10):
    """
    Generate player data according to the data.json format
    
    Args:
        count (int): Number of players to generate (default: 500)
    
    Returns:
        dict: Complete data structure matching the original format
    """
    players = []
    
    for i in range(count):
        player = {
            "Player Name": f"{i}_@{i}",
            "Player Money": random.randint(8000000, 100000000),
            "Player Age": 18,  # Fixed value
            "Player Body State": 80,  # Fixed value
            "Player Mind State": 100,  # Fixed value
            "PlayerIQ": 120,  # Fixed value
            "Player El": 120,  # Fixed value
            "R": random.randint(0, 255),
            "G": random.randint(0, 255),
            "B": random.randint(0, 255),
            "Additional Info": "游戏生成的玩家数据",  # Fixed value
            "Number": i,
            "Timestamp": datetime.now().isoformat()
        }
        players.append(player)
    
    # Create the complete data structure
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "received_data": {
            "players": players,
            "metadata": {
                "description": "玩家数据存储",
                "version": "1.0",
                "total_players": count,
                "current_number": 0,
                "last_updated": current_time,
                "color_info": "R、G、B字段表示玩家的颜色属性，取值范围为0-255整数"
            }
        },
        "received_at": current_time,
        "source_server": "http://localhost:10001/save_player_data"
    }
    
    return data

def save_to_json(data, filename="data.json"):
    """
    Save the generated data to a JSON file
    
    Args:
        data (dict): The data to save
        filename (str): Output filename (default: "data.json")
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully generated {len(data['received_data']['players'])} player records")
    print(f"Data saved to: {filename}")

def main():
    """
    Main function to generate and save player data
    """
    print("Generating 500 player data records...")
    
    # Generate the data
    generated_data = generate_player_data(10)
    
    # Save to JSON file
    save_to_json(generated_data)
    
    # Display sample data
    print("\nSample of generated data:")
    print("First player:", json.dumps(generated_data['received_data']['players'][0], ensure_ascii=False, indent=2))
    print("Last player:", json.dumps(generated_data['received_data']['players'][-1], ensure_ascii=False, indent=2))
    
    print(f"\nMetadata:")
    print(f"Total players: {generated_data['received_data']['metadata']['total_players']}")
    print(f"Last updated: {generated_data['received_data']['metadata']['last_updated']}")

if __name__ == "__main__":
    main()