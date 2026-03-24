# Agent Selfie Generator

一个轻量化的 AI Agent 技能模块，通过生图模型生成具有人物一致性的动漫风格自拍照。

## 功能特点

- **人物一致性**：通过参考图保持角色形象统一
- **两种自拍模式**：直接自拍 / 镜子自拍
- **时间感知**：根据当前时间选择匹配的场景
- **画面比例**：支持多种比例（1:1, 9:16, 16:9 等）
- **即插即用**：Python 脚本 + 环境变量配置

## 文件结构

```
.
├── selfie_gen.py      # 核心生成脚本
├── .env               # 配置文件（API Key、参考图路径）
├── reference.png      # 角色参考图
├── outputs/           # 生成图片存放目录
├── SKILL.md           # Agent 使用手册
└── README.md          # 本文件
```

## 快速开始

1. **配置环境变量**：复制 `.env.example` 为 `.env`，填入 OpenRouter API Key
2. **准备参考图**：放置角色设定图到 `reference.png`
3. **运行脚本**：

```bash
# 直接自拍
python selfie_gen.py direct "在咖啡厅" "微笑着喝咖啡"

# 镜子自拍
python selfie_gen.py mirror "在浴室" "刚洗完澡" --mirror-type "大镜子"
```

## 详细使用说明

👉 查看 [SKILL.md](./SKILL.md) 了解：
- 意图识别规则（用户说什么应该发自拍）
- 时间感知的场景选择
- 完整的调用示例

## 依赖

```bash
pip install openai python-dotenv
```

## 模型

使用 OpenRouter 提供的 `google/gemini-3.1-flash-image-preview` 图像生成模型。
