# voice_ime
自适应VAD语音输入，流式实时识别

---

## 项目简介

VoiceIME是一款基于环境噪声自适应 VAD（Voice Activity Detection）的智能语音输入法。项目采用 Silero VAD + FunASR Paraformer 双模型架构，结合实时噪声估计与动态阈值调整，实现高精度的语音活动检测与流式语音识别。支持实时字幕输出、音频特征可视化、LLM 文本纠错等高级功能，适用于各种噪声环境下的语音输入场景。

---

## 核心特性

- **自适应 VAD 检测**：基于最小统计量和指数移动平均的噪声估计，根据信噪比（SNR）动态调整检测阈值
- **流式语音识别**：不等说话结束即可开始识别，实现增量式文本输出（类似实时字幕）
- **音频特征工程**：实时 FFT 频谱、梅尔频谱、过零率、谱质心计算与语音质量评估
- **可视化分析界面**：频谱图、波形图、噪声水平、阈值变化、检测状态实时展示
- **LLM 文本纠错**：自动去除语气词、修正标点符号，提升识别结果可读性
- **连续模式**：支持最长 5 分钟持续录音，麦克风始终保持开启
- **识别记录持久化**：普通模式与连续模式分别保存至独立目录
- **热键驱动**：全键盘操作，无需鼠标即可完成所有功能

---

## 目录结构

```
voice-ime/
├── main.py                      # 应用入口，初始化各模块并连接信号
├── requirements.txt             # Python 依赖包列表
├── .env                         # 环境配置（热键、API密钥等）
│
├── core/                        # 核心业务模块
│   ├── adaptive_vad.py          # 自适应VAD控制器（Silero VAD + 动态阈值）
│   ├── noise_estimator.py       # 噪声估计模块（最小统计量 + EMA跟踪）
│   ├── audio_features.py        # 音频特征提取与语音质量评估
│   ├── streaming_asr.py         # 流式语音识别引擎（增量处理）
│   ├── asr_engine.py            # 批量语音识别引擎（FunASR Paraformer）
│   ├── audio_capture.py         # 麦克风音频捕获（sounddevice）
│   ├── llm_corrector.py         # LLM文本纠错（去除语气词、修正标点）
│   ├── text_injector.py         # 文本注入（剪贴板粘贴 + 模拟按键）
│   ├── history_logger.py        # 识别记录持久化（分模式保存）
│   ├── statistics.py            # 使用统计（字数、会话数、时长）
│   └── vad_controller.py        # 原始VAD控制器（保留兼容）
│
├── ui/                          # 用户界面模块
│   ├── visualization.py         # 可视化组件（频谱图、波形图、状态指示）
│   ├── analysis_window.py       # 音频分析窗口（集中展示实时数据）
│   ├── overlay_window.py        # 悬浮状态窗口（识别状态与结果）
│   └── tray_manager.py          # 系统托盘与热键管理
│
├── utils/                       # 工具模块
│   ├── config.py                # 配置管理（单例模式 + 热更新）
│   ├── logger.py                # 日志模块（控制台 + 文件双输出）
│   └── __init__.py
│
├── experiments/                 # 实验与对比
│   └── vad_comparison.py        # VAD性能对比实验（固定阈值 vs 自适应）
│
├── history/                     # 识别记录存储
│   ├── voice_YYYYMMDD.txt       # 普通模式识别记录
│   ├── continuous/
│   │   └── continuous_YYYYMMDD.txt  # 连续模式识别记录
│   └── statistics.json          # 统计数据持久化
│

test_mic.py              # 麦克风诊断
test_vad.py              # VAD功能测试
test_audio_stream.py     # 音频流测试
check_deps.py            # 依赖检查
```

---

## 环境要求

- **操作系统**：Windows 10/11（Linux/macOS 需调整热键配置）
- **Python 版本**：3.8+（推荐 3.11+）
- **硬件要求**：麦克风、4GB+ 内存（GPU 可选，加速 ASR 推理）

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-username/voice-ime.git
cd voice-ime
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

编辑 `.env` 文件，根据需要修改配置：

```ini
# 热键配置
HOTKEY=f8
EXIT_KEY=f12

# VAD配置
VAD_THRESHOLD=0.5

# LLM配置（用于文本纠错）
GEMINI_API_KEY=your-api-key-here
GEMINI_BASE_URL=https://api.openai.com/v1
GEMINI_MODEL=your-llm-model
LLM_ENABLED=true

# 功能开关
CONTINUOUS_MODE=false
AUTO_PUNCTUATION=true
SPACE_APPEND=true
```

---

## 启动项目

```bash
python main.py
```

首次运行时，FunASR 模型会自动下载（约 1-2GB），请耐心等待。

注意，需在.env文件中的GEMINI_API_KEY选项添加你自己的api key，如有需要，联系本作者：liaoxcool@163.com

---

## 使用说明

### 热键操作

| 热键 | 功能 | 说明 |
|------|------|------|
| **F8**（按住） | 语音录制 | 按住说话，松开后自动识别并输入 |
| **F9** | 查看设置 | 弹出当前配置信息窗口 |
| **F10** | 连续模式 | 连续录音模式（最长5分钟）使用时只需按一次F10键即可，停止时再次按F10键即为停止 |
| **F11** | 音频分析 | 打开实时频谱与分析窗口 |
| **F12** | 退出程序 | 完全退出 VoiceIME Pro |

### 普通模式

1. 将光标定位到需要输入文字的位置
2. **按住 F8** 开始说话
3. 松开 F8 后，系统自动识别并将文字输入到光标处
4. 悬浮窗口显示识别状态和结果

### 连续模式

1. 按 **F10** 开启连续模式，麦克风持续开启
2. 可以连续说话，系统实时流式识别
3. 再次按 **F10** 停止录音并处理全部音频
4. 识别结果自动输入并保存到 `history/continuous/` 目录

### 音频分析窗口

按 **F11** 打开分析窗口，可查看：

- **波形图**：实时音频波形显示
- **FFT 频谱**：频率分布可视化（绿-黄-红表示能量强度）
- **梅尔频谱**：人耳感知频率分布
- **VAD 状态**：语音活动检测实时状态
- **麦克风状态**：设备连接状态
- **运行模式**：普通/连续模式指示
- **指标面板**：SNR、噪声水平、VAD阈值、语音质量评分
- **流式识别**：实时增量文本输出

---

## 技术架构

### 自适应 VAD 系统

```
音频输入 → 噪声估计 → SNR计算 → 动态阈值 → Silero VAD → 语音检测
```

- **噪声估计**：采用最小统计量跟踪 + 指数移动平均（EMA），实时估计环境噪声基线
- **自适应阈值**：根据 SNR 动态调整检测灵敏度
  - SNR < 0dB：阈值 +0.2（高噪声环境，提高检测门限）
  - SNR 0-5dB：阈值 +0.1
  - SNR 5-15dB：基准阈值 0.5
  - SNR 15-25dB：阈值 -0.1
  - SNR > 25dB：阈值 -0.15（安静环境，降低检测门限）
- **双重检测**：神经网络概率 + 能量阈值联合判断，降低误检率

### 流式识别流程

```
持续录音 → 重叠分块 → 噪声抑制 → 增量识别 → 部分结果 → 最终结果
```

- 每 2 秒音频块，0.5 秒重叠窗口
- 实时输出部分识别结果（类似字幕滚动）
- 说话结束后输出最终完整结果

### 语音质量评估

综合以下指标计算质量评分（0-1）：

| 指标 | 权重 | 说明 |
|------|------|------|
| SNR | 40% | 信噪比，越高越好 |
| 削波率 | 30% | 信号过载比例，越低越好 |
| 动态范围 | 20% | 信号幅度变化范围 |
| RMS 能量 | 10% | 平均信号强度 |

---

## 性能对比实验

运行以下命令对比固定阈值与自适应 VAD 的性能：

```bash
python experiments/vad_comparison.py
```

实验在不同 SNR 环境下（0dB ~ 25dB）对比两种方法的精确率、召回率和 F1 分数。

---

## 识别记录

所有识别结果自动保存至 `history/` 目录：

- **普通模式**：`history/voice_YYYYMMDD.txt`
- **连续模式**：`history/continuous/continuous_YYYYMMDD.txt`

每条记录包含时间戳和识别文本，方便回溯与分析。

---

## 常见问题

### Q: 麦克风没有反应？
A: 运行 `python test_mic.py` 检查麦克风设备是否正常，确认系统已选择正确的输入设备。

### Q: 识别速度慢？
A: 首次运行需下载模型文件。如有 NVIDIA GPU，确保安装了 CUDA 版本的 PyTorch 以加速推理。

### Q: 热键不生效？
A: 确保程序以管理员权限运行，某些应用可能会拦截全局热键。

### Q: 如何启用 LLM 纠错？
A: 在 `.env` 中配置 `LLM_API_KEY` 和 `LLM_BASE_URL`，设置 `LLM_ENABLED=true`。

---

## 许可证

MIT License

---

## 作者

VoiceIME Pro - 基于环境噪声自适应 VAD 的智能语音输入法

