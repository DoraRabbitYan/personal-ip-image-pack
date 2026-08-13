# 个人 IP 稳定交付契约

使用本契约把一次对话中的人物设定、已确认原型、独立资产和验收记录连接起来。不要把用户原始照片复制进 Skill 仓库、模板目录或默认交付包。

## 工作目录

在用户指定的私有输出目录中创建以下结构；未指定时使用工作区的 outputs/<character-id>/。输出目录应被 Git 忽略。优先运行以下脚本创建骨架，脚本会拒绝覆盖已有交付包：

~~~text
python scripts/init_delivery_package.py <character-id> --output-root outputs
~~~

~~~text
<output-root>/<character-id>/
├── contracts/
│   ├── input-brief.yaml
│   ├── character-spec-d1.yaml
│   ├── character-spec-v1.yaml
│   ├── delivery-manifest-r1.json
│   └── acceptance-qa-r1.md
├── assets/
│   ├── prototype-v1-r1.png
│   └── stickers/
│       └── happy-wave-v1-r1.png
└── previews/
    └── sticker-sheet-v1-r1.png
~~~

脚本会复制 assets/templates/ 中的模板到此目录后再填写。不要修改内置模板。若当前环境不能写入文件，输出同样的结构化内容并明确说明它只是草案，不能声称已经交付文件。

## 四个契约

- input-brief.yaml：私有输入、主体授权、照片可用性、风格选择、用途和范围。它是生成门槛，不默认交给最终用户。
- character-spec-vN.yaml：已冻结的人物身份与视觉锁。它是后续扩展的唯一人物锚点。
- delivery-manifest-rN.json：真实交付物的来源、尺寸、透明通道、哈希和 QA 状态。预览拼图不能替代 source_asset。
- acceptance-qa-rN.md：AI 发布前检查和用户验收的独立记录。

模板路径：

- assets/templates/input-brief.yaml
- assets/templates/character-spec.yaml
- assets/templates/delivery-manifest.json
- assets/templates/acceptance-qa.md

## 状态与版本

- dN：原型草案。可自由迭代，不能用来批量扩展。
- vN：用户明确确认后冻结的角色身份版本。任何 identity_lock、visual_lock 或 do_not_change 的变化必须产生 vN+1。
- rN：同一角色版本的一次交付发布。只改一个已允许的表情、姿势、道具、裁切或输出尺寸时产生 rN+1，不升级人物版本。

状态按 draft → qa_passed → accepted → superseded 推进。回退只切换当前生效的 vN 或 rN；不得覆盖旧文件、旧提示词或旧验收记录。

## 发布门槛

交付前必须全部满足：

1. input brief 中的 likeness_consent 为 confirmed，且每张身份图被标记 usable。
2. 当前风格的参考素材在 references/style-asset-rights.yaml 中已清权；若未清权，只能使用 style-specs.yaml 的文字规范，不能把内置参考图传给图像模型。
3. 存在用户确认的 character-spec-vN，且 approved_anchor 指向对应原型。
4. 每个可用资产都单独生成、单独 QA，并登记为 manifest 中的 source_asset。
5. 预览拼图仅由已 QA 通过的独立资产组成，并登记为 preview。
6. 运行 scripts/validate_delivery.py <delivery-root> --ready 无错误。

## 命名与可追溯性

使用 <asset-id>-v<N>-r<N>.png 命名独立 PNG，例如 happy-wave-v1-r2.png。manifest 中记录文件的实际 pixel_size、actual alpha、SHA-256 和来源人物版本；不要凭目标规格填写实际值。

参考 references/asset-forms.yaml 选择默认规格。图像工具不能输出透明背景或指定尺寸时，使用该工具实际输出，准确记录 alpha: false 或实际像素；不要把白底图标成透明贴纸。
