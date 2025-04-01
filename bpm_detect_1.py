# Copyright 2012 Free Software Foundation, Inc.
#
# This file is part of The BPM Detector Python
#
# The BPM Detector Python is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

import array
import math
import wave
import os
import json

import matplotlib.pyplot as plt
import numpy
import pywt
from scipy import signal
import librosa


def read_wav(filename):
    try:
        y, sr = librosa.load(filename, sr=None, mono=True)
        return y.tolist(), sr
    except Exception as e:
        print(f"无法打开文件: {e}")
        return None, None


def no_audio_data():
    print("没有找到有效的音频数据，跳过...")
    return None, None


def peak_detect(data):
    max_val = numpy.amax(abs(data))
    peak_ndx = numpy.where(data == max_val)
    if len(peak_ndx[0]) == 0:  # if nothing found then the max must be negative
        peak_ndx = numpy.where(data == -max_val)
    return peak_ndx


def bpm_detector(data, fs):
    cA = []
    cD = []
    correl = []
    cD_sum = []
    levels = 4
    max_decimation = 2 ** (levels - 1)
    min_ndx = math.floor(60.0 / 220 * (fs / max_decimation))
    max_ndx = math.floor(60.0 / 40 * (fs / max_decimation))

    for loop in range(0, levels):
        cD = []
        # 1) DWT
        if loop == 0:
            [cA, cD] = pywt.dwt(data, "db4")
            cD_minlen = len(cD) / max_decimation + 1
            cD_sum = numpy.zeros(math.floor(cD_minlen))
        else:
            [cA, cD] = pywt.dwt(cA, "db4")

        # 2) Filter
        cD = signal.lfilter([0.01], [1 - 0.99], cD)

        # 3) 抽取并处理
        cD = abs(cD[:: (2 ** (levels - loop - 1))])
        cD = cD - numpy.mean(cD)

        # 4) 重组信号
        cD_sum = cD[0 : math.floor(cD_minlen)] + cD_sum

    if [b for b in cA if b != 0.0] == []:
        return no_audio_data()

    # 添加近似数据
    cA = signal.lfilter([0.01], [1 - 0.99], cA)
    cA = abs(cA)
    cA = cA - numpy.mean(cA)
    cD_sum = cA[0 : math.floor(cD_minlen)] + cD_sum

    # ACF
    correl = numpy.correlate(cD_sum, cD_sum, "full")

    midpoint = math.floor(len(correl) / 2)
    correl_midpoint_tmp = correl[midpoint:]
    
    # 确保索引范围有效
    if min_ndx >= len(correl_midpoint_tmp) or max_ndx > len(correl_midpoint_tmp):
        return no_audio_data()
    
    peak_ndx = peak_detect(correl_midpoint_tmp[min_ndx:max_ndx])
    if len(peak_ndx[0]) == 0:
        return no_audio_data()

    peak_ndx_adjusted = peak_ndx[0] + min_ndx
    bpm = 60.0 / peak_ndx_adjusted * (fs / max_decimation)
    return bpm, correl


def detect_file_bpm(audio_path, window_size=3):
    """检测单个文件的BPM"""
    print(f"正在分析文件: {audio_path}")
    
    # 检查文件是否存在
    if not os.path.exists(audio_path):
        print(f"文件不存在: {audio_path}")
        return None
    
    # 读取音频文件
    samps, fs = read_wav(audio_path)
    if samps is None or fs is None:
        print("无法读取音频文件")
        return None
    
    nsamps = len(samps)
    window_samps = int(window_size * fs)
    
    # 如果样本数小于窗口大小，使用整个文件
    if nsamps < window_samps:
        window_samps = nsamps
    
    max_window_ndx = math.floor(nsamps / window_samps)
    bpms = []

    # 遍历所有窗口
    for window_ndx in range(0, max_window_ndx):
        samps_ndx = window_ndx * window_samps
        data = samps[samps_ndx : samps_ndx + window_samps]
        
        bpm, _ = bpm_detector(data, fs)
        if bpm is not None:
            bpms.append(bpm)
    
    # 如果没有找到有效的BPM
    if not bpms:
        print("未能检测到有效的BPM")
        return None
    
    # 计算中位数BPM
    bpm = numpy.median(bpms)
    print(f"检测完成! 估计的BPM: {bpm:.1f}")
    return round(float(bpm), 1)


def detect_segment_bpm(audio_data, fs, start_time, end_time, window_size=3):
    """检测音频段落的BPM"""
    print(f"正在分析段落: {start_time:.2f}s - {end_time:.2f}s")
    
    # 将时间转换为样本索引
    start_sample = int(start_time * fs)
    end_sample = int(end_time * fs)
    
    # 确保索引在有效范围内
    if start_sample >= len(audio_data) or end_sample > len(audio_data) or start_sample >= end_sample:
        print(f"无效的段落范围: {start_time:.2f}s - {end_time:.2f}s")
        return None
    
    # 提取段落数据
    segment_data = audio_data[start_sample:end_sample]
    
    # 计算窗口大小（样本数）
    window_samps = int(window_size * fs)
    
    # 如果段落小于窗口大小，使用整个段落
    if len(segment_data) < window_samps:
        window_samps = len(segment_data)
    
    max_window_ndx = math.floor(len(segment_data) / window_samps)
    bpms = []

    # 遍历所有窗口
    for window_ndx in range(0, max_window_ndx):
        samps_ndx = window_ndx * window_samps
        data = segment_data[samps_ndx : samps_ndx + window_samps]
        
        bpm, _ = bpm_detector(data, fs)
        if bpm is not None:
            bpms.append(bpm)
    
    # 如果没有找到有效的BPM
    if not bpms:
        print(f"段落 {start_time:.2f}s - {end_time:.2f}s 未能检测到有效的BPM")
        return None
    
    # 计算中位数BPM
    bpm = numpy.median(bpms)
    print(f"段落 {start_time:.2f}s - {end_time:.2f}s BPM: {bpm:.1f}")
    return round(float(bpm), 1)


def load_segments(segment_file):
    """加载分段信息"""
    try:
        with open(segment_file, 'r', encoding='utf-8') as f:
            segment_data = json.load(f)
        return segment_data
    except Exception as e:
        print(f"加载分段文件失败: {e}")
        return None


def process_audio_with_segments(audio_file, segment_file, output_folder, window_size=3):
    """使用分段信息处理音频文件"""
    print(f"处理音频文件: {audio_file}")
    print(f"使用分段信息: {segment_file}")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载分段信息
    segment_data = load_segments(segment_file)
    if not segment_data:
        return None
    
    # 读取音频文件
    audio, fs = read_wav(audio_file)
    if audio is None or fs is None:
        print(f"无法读取音频文件: {audio_file}")
        return None
    
    # 获取音频文件名（不含扩展名）
    audio_name = os.path.splitext(os.path.basename(audio_file))[0]
    
    # 分析结果
    results = {
        "audio_file": os.path.basename(audio_file),
        "total_segments": len(segment_data["segments"]),
        "segments": []
    }
    
    # 处理每个段落
    for i, segment in enumerate(segment_data["segments"]):
        start_time = segment["start_time"]
        end_time = segment["end_time"]
        
        # 检测段落BPM
        bpm = detect_segment_bpm(audio, fs, start_time, end_time, window_size)
        
        # 保存结果
        segment_result = {
            "segment_index": i,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "bpm": bpm
        }
        
        results["segments"].append(segment_result)
    
    # 保存结果到JSON文件
    output_file = os.path.join(output_folder, f"{audio_name}_segment_bpm.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"已保存分段BPM分析结果到: {output_file}")
    return results


def process_segment_folder(segment_folder, audio_folder, output_folder, window_size=3):
    """处理文件夹中的所有分段文件"""
    print(f"处理分段文件夹: {segment_folder}")
    print(f"音频文件夹: {audio_folder}")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 处理结果统计
    processed = 0
    errors = 0
    
    # 遍历分段文件夹中的所有JSON文件
    for filename in os.listdir(segment_folder):
        if filename.lower().endswith('_segments.json'):
            segment_file = os.path.join(segment_folder, filename)
            
            # 从分段文件名中提取音频文件名
            audio_base_name = filename.replace('_segments.json', '')
            
            # 查找对应的音频文件
            audio_file = None
            for ext in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                potential_file = os.path.join(audio_folder, audio_base_name + ext)
                if os.path.exists(potential_file):
                    audio_file = potential_file
                    break
            
            if audio_file:
                try:
                    # 处理音频文件和分段信息
                    process_audio_with_segments(audio_file, segment_file, output_folder, window_size)
                    processed += 1
                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {e}")
                    errors += 1
            else:
                print(f"找不到对应的音频文件: {audio_base_name}")
                errors += 1
    
    # 打印统计信息
    print(f"\n处理完成:")
    print(f"成功处理文件数: {processed}")
    print(f"处理失败文件数: {errors}")


def process_audio_folder(audio_folder, output_folder, window_size=3):
    """处理文件夹中的所有音频文件并检测BPM"""
    print(f"处理音频文件夹: {audio_folder}")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 处理结果统计
    processed = 0
    errors = 0
    
    # 收集结果用于可视化
    results = []
    
    # 支持的音频格式
    supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
    
    # 遍历音频文件夹中的所有文件
    for filename in os.listdir(audio_folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in supported_formats:
            audio_file = os.path.join(audio_folder, filename)
            
            try:
                # 检测文件BPM
                bpm = detect_file_bpm(audio_file, window_size)
                
                if bpm is not None:
                    # 获取文件名（不含扩展名）
                    audio_name = os.path.splitext(os.path.basename(audio_file))[0]
                    
                    # 保存结果
                    result = {
                        "audio_file": filename,
                        "bpm": bpm
                    }
                    
                    # 将结果添加到列表
                    results.append(result)
                    
                    # 保存单个文件结果到JSON
                    output_file = os.path.join(output_folder, f"{audio_name}_bpm.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    processed += 1
                else:
                    print(f"未能检测到文件 {filename} 的BPM")
                    errors += 1
                    
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {e}")
                errors += 1
    
    # 如果有结果，创建并保存可视化
    if results:
        visualize_bpm_results(results, output_folder)
    
    # 保存所有结果到一个JSON文件
    if results:
        all_results = {
            "total_files": len(results),
            "results": results
        }
        
        output_file = os.path.join(output_folder, "all_bpm_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"已保存所有BPM分析结果到: {output_file}")
    
    # 打印统计信息
    print(f"\n处理完成:")
    print(f"成功处理文件数: {processed}")
    print(f"处理失败文件数: {errors}")
    
    return results


def visualize_bpm_results(results, output_folder):
    """可视化BPM分析结果"""
    if not results:
        print("没有可视化的结果")
        return
    
    # 提取数据用于可视化
    file_names = [r["audio_file"] for r in results]
    bpms = [r["bpm"] for r in results]
    
    # 创建柱状图
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(file_names)), bpms, color='skyblue')
    plt.xlabel('音频文件')
    plt.ylabel('BPM')
    plt.title('音频文件BPM分析结果')
    plt.xticks(range(len(file_names)), file_names, rotation=45, ha='right')
    plt.tight_layout()
    
    # 在柱状图上添加BPM值标签
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                 str(bpms[i]), ha='center', va='bottom')
    
    # 保存图表
    output_file = os.path.join(output_folder, "bpm_visualization.png")
    plt.savefig(output_file, dpi=300)
    print(f"已保存BPM可视化结果到: {output_file}")
    
    # 关闭图表
    plt.close()
    
    # 创建BPM分布直方图
    plt.figure(figsize=(10, 6))
    plt.hist(bpms, bins=20, color='lightgreen', edgecolor='black')
    plt.xlabel('BPM')
    plt.ylabel('频率')
    plt.title('BPM分布直方图')
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()
    
    # 保存直方图
    output_file = os.path.join(output_folder, "bpm_histogram.png")
    plt.savefig(output_file, dpi=300)
    print(f"已保存BPM分布直方图到: {output_file}")
    
    # 关闭图表
    plt.close()


def main():
    # 设置路径
    audio_folder = r"F:\ai_program_2\audio_assessment\code_1\input"
    output_folder = r"F:\ai_program_2\audio_assessment\code_1\input\bpm_analysis\result"
    window_size = 10  # 分析窗口大小（秒）
    
    # 直接处理所有音频文件
    process_audio_folder(audio_folder, output_folder, window_size)
    
    # 如果需要继续处理段落BPM，可以取消下面的注释
    # segment_folder = r"F:\ai_program_2\audio_assessment\code_1\processed\segment_analysis\result"
    # segment_output_folder = r"F:\ai_program_2\audio_assessment\code_1\processed\segment_bpm\result"
    # process_segment_folder(segment_folder, audio_folder, segment_output_folder, window_size)


if __name__ == "__main__":
    main()