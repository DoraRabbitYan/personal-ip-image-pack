# personal-ip-image-pack

个人 IP 形象与表情包生成 Codex skill。

这个 skill 用于根据用户提供的 1-3 张个人照片，为小红书博主或个人品牌制作可长期复用的卡通 IP，包括风格选择、人物锚点提取、卡通原型生成、表情包和动作包扩展。

## Contents

- `SKILL.md`: skill 的主说明与工作流程。
- `references/`: 风格预设与图像生成提示词模板。
- `assets/style-library/`: 可在浏览器中打开的中文风格库。
- `assets/style-examples/`: 示例风格素材。
- `agents/`: skill 相关 agent 配置。

## Usage

在 Codex 中触发 `personal-ip-image-pack` 后，按以下阶段推进：

1. 选择 `IP-01` 至 `IP-06` 的风格编码。
2. 上传 1-3 张人物照片。
3. 生成并确认卡通原型。
4. 在原型确认后扩展表情、动作或贴纸套图。

生成图片前应先读取 `references/generation-prompts.md`，并按所选风格读取 `references/style-presets.md` 中的完整规范。
