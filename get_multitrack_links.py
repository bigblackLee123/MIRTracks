import os
import json
import requests
from bs4 import BeautifulSoup
import re

def read_index_files():
    """读取所有索引文件并提取乐曲信息"""
    tracks = []
    mir_dir = 'MIR'
    
    for genre in os.listdir(mir_dir):
        genre_path = os.path.join(mir_dir, genre)
        if not os.path.isdir(genre_path):
            continue
            
        for track_dir in os.listdir(genre_path):
            if not track_dir.endswith('_MIR'):
                continue
                
            track_path = os.path.join(genre_path, track_dir)
            index_file = os.path.join(track_path, f"{track_dir[:-4]}.txt")
            
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取乐曲信息
                    track_name = track_dir[:-4]  # 去掉_MIR后缀
                    tracks.append({
                        'name': track_name,
                        'genre': genre,
                        'index_file': index_file
                    })
    
    return tracks

def get_cambridge_mt_links():
    """从Cambridge MT网站获取多轨音频链接"""
    base_url = "https://www.cambridge-mt.com/ms/mtk/"
    tracks = read_index_files()
    
    # 创建结果目录
    if not os.path.exists('download_links'):
        os.makedirs('download_links')
    
    # 获取网页内容
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 存储所有找到的链接
        found_links = {}
        
        # 遍历所有链接
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and ('Full Multitrack' in link.text or 'Edited Excerpt' in link.text):
                # 提取乐曲名称
                track_name = link.find_previous('strong').text.strip() if link.find_previous('strong') else None
                if track_name:
                    found_links[track_name] = {
                        'full': href if 'Full Multitrack' in link.text else None,
                        'excerpt': href if 'Edited Excerpt' in link.text else None
                    }
        
        # 为每个索引文件创建下载链接文件
        for track in tracks:
            track_name = track['name']
            if track_name in found_links:
                output_file = os.path.join('download_links', f"{track_name}_links.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Track: {track_name}\n")
                    f.write(f"Genre: {track['genre']}\n")
                    f.write("\nDownload Links:\n")
                    if found_links[track_name]['full']:
                        f.write(f"Full Multitrack: {found_links[track_name]['full']}\n")
                    if found_links[track_name]['excerpt']:
                        f.write(f"Edited Excerpt: {found_links[track_name]['excerpt']}\n")
                print(f"已创建链接文件: {output_file}")
            else:
                print(f"未找到乐曲链接: {track_name}")
                
    except Exception as e:
        print(f"获取网页时出错: {str(e)}")

if __name__ == "__main__":
    get_cambridge_mt_links()
    print("处理完成！") 