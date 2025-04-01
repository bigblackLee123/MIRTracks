# MIR Tracks

[English](#english) | [中文](#中文)

<a name="中文"></a>
# MIR Tracks

MIR Tracks 是一个音乐信息检索（Music Information Retrieval）数据集，包含了来自 Cambridge Music Technology 的多轨音频文件及其详细分析数据。本项目遵循非商业使用协议。

## 数据集结构

数据集按音乐流派分类组织，包含以下类别：
- rock（摇滚）
- pop（流行）
- jazz（爵士）
- folk_instrulmental（民乐）
- electronica（电子音乐）
- dance（舞曲）
- country（乡村）

每个音频文件都包含以下分析数据：
- 能量分布分析
- 段落结构分析
- 速度（BPM）分布分析

## 功能特点

1. **多轨音频获取**
   - 通过 `get_multitrack_links.py` 获取音频下载链接
   - 支持从 Cambridge Music Technology 网站获取原始多轨文件
   - 所有音频文件均为 24-bit/16-bit WAV 格式，采样率 44.1kHz

2. **音频分析**
   - `analyze_audio_activity.py`: 分析音频能量分布和活动特征
   - `bpm_detect_1.py`: 检测音频的速度（BPM）分布

## 使用说明

1. 获取音频链接：
```python
python get_multitrack_links.py
```

2. 分析音频特征：
```python
python analyze_audio_activity.py
python bpm_detect_1.py
```

## 数据来源

所有音频文件来源于 [Cambridge Music Technology](https://www.cambridge-mt.com/ms/mtk/#Pop)，遵循其非商业使用协议。

## 使用协议

- 本项目仅用于教育目的
- 禁止将数据用于商业用途
- 使用数据时请遵守 Cambridge Music Technology 的使用条款

## 目录结构

```
MIR/
├── rock/
├── pop/
├── jazz/
├── folk_instrulmental/
├── electronica/
├── dance/
└── country/
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 许可证

本项目遵循非商业使用协议。详细使用条款请参考 [Cambridge Music Technology](https://www.cambridge-mt.com/ms/mtk/#Pop) 的使用协议。

---

<a name="english"></a>
# MIR Tracks

MIR Tracks is a Music Information Retrieval (MIR) dataset containing multitrack audio files and detailed analysis data from Cambridge Music Technology. This project follows a non-commercial usage agreement.

## Dataset Structure

The dataset is organized by music genres, including:
- Rock
- Pop
- Jazz
- Folk Instrumental
- Electronica
- Dance
- Country

Each audio file includes the following analysis data:
- Energy distribution analysis
- Section structure analysis
- Tempo (BPM) distribution analysis

## Features

1. **Multitrack Audio Acquisition**
   - Get audio download links via `get_multitrack_links.py`
   - Support for retrieving original multitrack files from Cambridge Music Technology
   - All audio files are in 24-bit/16-bit WAV format at 44.1kHz sample rate

2. **Audio Analysis**
   - `analyze_audio_activity.py`: Analyze audio energy distribution and activity features
   - `bpm_detect_1.py`: Detect audio tempo (BPM) distribution

## Usage Instructions

1. Get audio links:
```python
python get_multitrack_links.py
```

2. Analyze audio features:
```python
python analyze_audio_activity.py
python bpm_detect_1.py
```

## Data Source

All audio files are sourced from [Cambridge Music Technology](https://www.cambridge-mt.com/ms/mtk/#Pop) and follow their non-commercial usage agreement.

## Usage Agreement

- This project is for educational purposes only
- Commercial use of the data is prohibited
- Users must comply with Cambridge Music Technology's terms of use

## Directory Structure

```
MIR/
├── rock/
├── pop/
├── jazz/
├── folk_instrulmental/
├── electronica/
├── dance/
└── country/
```

## Contributing

Issues and Pull Requests are welcome to improve the project.

## License

This project follows a non-commercial usage agreement. For detailed terms of use, please refer to [Cambridge Music Technology](https://www.cambridge-mt.com/ms/mtk/#Pop)'s usage agreement. 
