#!/usr/bin/env python3
"""
AI Agent Selfie Generator Skill
支持两种模式：直接自拍 / 镜子自拍
"""

import os
import sys
import base64
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI


# ========== 固定的提示词模板头 ==========
PROMPT_TEMPLATE_HEADER = """按照要求生成一张动漫风格的自拍照，需要保持参考图中人物角色的设定和画风，可以更换服装、姿势、表情和场景。"""

# ========== 两种自拍模式的模板 ==========
MODE_TEMPLATES = {
    "direct": """【拍摄模式：举着手机自拍（无镜子）】
- 这是直接用手机前置摄像头自拍的照片
- 照片中**看不到手机本身**，因为手机就是拍摄设备
- 人物手臂姿势暗示在举着手机自拍
- 视角：近距离自拍角度，自然手持高度
- 因为是前置摄像头直接拍摄，画面里不会出现手机

场景设定：{scene}
人物动作/表情：{action}""",
    "mirror": """【拍摄模式：对着镜子自拍】
- 这是人物举着手机对着镜子拍摄的照片
- 镜头**只对着镜子**，所以照片里**只能看到镜子里的倒影**
- **镜子外（真实环境）不会出现在照片里**，因为镜头只拍摄镜子中的画面
- 镜子里能看到：人物的完整倒影，以及倒影中举着手机的手和手机
- 镜子类型：{mirror_type}

重要约束：
1. 照片里**只有镜子**，镜子占据了画面主体
2. 镜子里能看到人物的倒影，包括举着手机的样子
3. **镜子外没有人物**，也没有手机，因为镜头是对着镜子拍的
4. 可以稍微看到镜子周围的环境（如墙壁、灯光），但看不到拍摄者本人

场景设定：{scene}
人物动作/表情：{action}""",
}


def load_config():
    """从.env加载配置"""
    load_dotenv()

    config = {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "model": os.getenv("MODEL_NAME", "google/gemini-3.1-flash-image-preview"),
        "reference_image": os.getenv("REFERENCE_IMAGE", "reference.png"),
        "output_dir": os.getenv("OUTPUT_DIR", "outputs"),
    }

    if not config["api_key"]:
        raise ValueError("错误: OPENROUTER_API_KEY 未设置，请在.env中配置")

    return config


def encode_image_to_base64(image_path):
    """将图片编码为base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_prompt(mode, scene, action, mirror_type=None):
    """构建完整提示词"""
    # 使用模板头
    prompt_parts = [PROMPT_TEMPLATE_HEADER]

    # 根据模式选择模板
    if mode == "mirror":
        if not mirror_type:
            mirror_type = "普通镜子"
        mode_content = MODE_TEMPLATES["mirror"].format(
            scene=scene, action=action, mirror_type=mirror_type
        )
    else:  # direct mode
        mode_content = MODE_TEMPLATES["direct"].format(scene=scene, action=action)

    prompt_parts.append(mode_content)

    return "\n\n".join(prompt_parts)


def validate_aspect_ratio(ratio):
    """验证并返回标准格式的aspect ratio"""
    valid_ratios = [
        "1:1",
        "2:3",
        "3:2",
        "3:4",
        "4:3",
        "4:5",
        "5:4",
        "9:16",
        "16:9",
        "21:9",
    ]
    if ratio not in valid_ratios:
        raise ValueError(
            f"不支持的aspect ratio: {ratio}. 支持的比值: {', '.join(valid_ratios)}"
        )
    return ratio


def generate_selfie(config, mode, scene, action, mirror_type=None, aspect_ratio=None):
    """
    调用API生成自拍照

    Args:
        config: 配置字典
        mode: "direct" 或 "mirror"
        scene: 场景描述
        action: 动作/表情描述
        mirror_type: 镜子类型（仅在mirror模式下使用）
        aspect_ratio: 可选的画面比例

    Returns:
        生成的图片保存路径
    """
    # 检查参考图是否存在
    ref_path = Path(config["reference_image"])
    if not ref_path.exists():
        raise FileNotFoundError(f"参考图不存在: {ref_path}")

    print(f"参考图片: {ref_path.absolute()}")

    # 编码参考图
    base64_image = encode_image_to_base64(ref_path)
    data_url = f"data:image/png;base64,{base64_image}"

    # 构建提示词
    full_prompt = build_prompt(mode, scene, action, mirror_type)

    # 初始化客户端
    client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])

    # 构造消息 - 使用OpenAI格式传递参考图
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": full_prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]

    print(f"\n正在生成自拍照...")
    print(f"模式: {'对着镜子自拍' if mode == 'mirror' else '直接自拍'}")
    print(f"场景: {scene}")
    print(f"动作: {action}")
    if mirror_type:
        print(f"镜子类型: {mirror_type}")
    if aspect_ratio:
        print(f"画面比例: {aspect_ratio}")

    # 构建extra_body
    extra_body = {"modalities": ["image", "text"]}

    if aspect_ratio:
        validate_aspect_ratio(aspect_ratio)
        extra_body["image_config"] = {"aspect_ratio": aspect_ratio}

    # 调用API
    response = client.chat.completions.create(
        model=config["model"], messages=messages, extra_body=extra_body
    )

    # 解析响应
    message = response.choices[0].message

    if not hasattr(message, "images") or not message.images:
        # 检查是否有文本内容说明
        if hasattr(message, "content") and message.content:
            print(f"API返回文本: {message.content}")
        raise RuntimeError("API未返回图片")

    # 获取图片数据
    image_data = message.images[0]["image_url"]["url"]

    # 确保输出目录存在
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_suffix = "mirror" if mode == "mirror" else "direct"
    output_path = output_dir / f"selfie_{mode_suffix}_{timestamp}.png"

    # 保存图片
    if image_data.startswith("data:image"):
        # 提取base64数据
        base64_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(base64_data)
    else:
        # 直接是base64
        image_bytes = base64.b64decode(image_data)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return str(output_path)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Agent Selfie Generator - 生成动漫风格自拍照",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 模式1: 直接自拍（照片里看不到手机）
  python selfie_gen.py direct "在咖啡厅窗边" "微笑着喝咖啡"
  
  # 模式2: 对着镜子自拍（照片里能看到手机）
  python selfie_gen.py mirror "在浴室" "整理头发" --mirror-type "浴室大镜子"
  
  # 指定画面比例
  python selfie_gen.py direct "在公园" "比耶" --ratio 9:16
        """,
    )

    # 子命令选择模式
    subparsers = parser.add_subparsers(dest="mode", help="自拍模式")

    # 模式1: 直接自拍
    direct_parser = subparsers.add_parser(
        "direct", help="举着手机直接自拍（照片里看不到手机）"
    )
    direct_parser.add_argument("scene", help="场景描述（例如：在海边、在咖啡厅）")
    direct_parser.add_argument("action", help="动作/表情描述（例如：微笑着、比耶）")
    direct_parser.add_argument(
        "--ratio",
        choices=[
            "1:1",
            "2:3",
            "3:2",
            "3:4",
            "4:3",
            "4:5",
            "5:4",
            "9:16",
            "16:9",
            "21:9",
        ],
        help="画面比例（可选，默认1:1）",
    )
    direct_parser.add_argument("--output", "-o", help="输出图片路径（可选）")

    # 模式2: 镜子自拍
    mirror_parser = subparsers.add_parser(
        "mirror", help="对着镜子自拍（照片里能看到手机）"
    )
    mirror_parser.add_argument("scene", help="场景描述（例如：在浴室、在健身房）")
    mirror_parser.add_argument(
        "action", help="动作/表情描述（例如：整理头发、展示肌肉）"
    )
    mirror_parser.add_argument(
        "--mirror-type",
        default="镜子",
        help="镜子类型描述（例如：浴室镜子、全身镜、梳妆镜）",
    )
    mirror_parser.add_argument(
        "--ratio",
        choices=[
            "1:1",
            "2:3",
            "3:2",
            "3:4",
            "4:3",
            "4:5",
            "5:4",
            "9:16",
            "16:9",
            "21:9",
        ],
        help="画面比例（可选，默认1:1）",
    )
    mirror_parser.add_argument("--output", "-o", help="输出图片路径（可选）")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        sys.exit(1)

    try:
        # 加载配置
        config = load_config()
        print(f"配置加载成功")
        print(f"使用模型: {config['model']}")

        # 生成自拍照
        mirror_type = getattr(args, "mirror_type", None)
        output_path = generate_selfie(
            config,
            args.mode,
            args.scene,
            args.action,
            mirror_type=mirror_type,
            aspect_ratio=args.ratio,
        )

        print(f"\n生成成功!")
        print(f"图片保存路径: {output_path}")

        return output_path

    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
