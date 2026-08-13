# 个人 IP 生图提示词

本文件只定义统一组装方法。六种风格的 render_rules、negative_rules、能力和风格 QA 均以 style-specs.yaml 为准；不要再为不同风格手写不对称的图号、人物或身体默认值。

## 生成前门槛

每次生成前依次读取：

1. 当前 input-brief.yaml，确认 likeness_consent 为 confirmed、照片可用、资产形式在风格能力范围内。
2. 当前 character-spec-vN.yaml。扩展资产必须使用 status 为 approved 的 vN；草案 dN 只能生成原型候选。
3. 选中的 style-specs.yaml 条目与 asset-forms.yaml。
4. style-asset-rights.yaml。只有 rights group 为 cleared 时才可附带内置风格图；否则设定 reference_mode 为 text_spec_only。

优先级固定为：

1. 用户明确确认的角色版本。
2. 用户本轮明确要求的 mutable_fields。
3. 所选风格的 render_rules。
4. 风格与资产形式的默认值。

若用户要求改变 identity_lock、visual_lock 或 do_not_change 中的字段，不要直接改提示词；先创建 dN+1，确认后再冻结为 vN+1。

## 输入图片职责

不要使用图1、图2等硬编码位置。为每张图分配有名字的职责：

~~~text
身份参考：
- ID-01（primary_identity）：只定义脸型、发型、发色、分缝、眼镜、标志性穿搭。
- ID-02（optional_feature_check）：仅校正 [具体特征]；与 ID-01 冲突时以 ID-01 和已确认角色卡为准。

风格参考：
- STYLE-01…：只定义头身比例、五官简化、线条、色块、明暗、材质和背景语言。
- 若 style_reference_mode 为 text_spec_only：不附带任何内置风格图，直接使用 style-specs.yaml 的文字规则。
~~~

身份图不得传递皮肤纹理、真实鼻唇结构、牙齿、单根发丝、景深或摄影光影。风格图不得传递参考人物的身份、发色、服装、宠物、道具、文字、签名或水印。

## 统一五段式模板

将以下五段按顺序填入图像工具。方括号内容必须来自 brief、当前角色卡、style spec 或 asset form；不要虚构信息。

~~~text
[输入图职责]
[身份参考与风格参考的命名职责；冲突优先级。]

[不可变的人物锁]
严格保持已确认角色 [character-spec-vN] 的：[identity_lock、visual_lock、do_not_change]。
不要保留真人照片的皮肤纹理、真实鼻唇结构、牙齿、单根发丝或摄影光影。

[风格渲染]
按 [style-id] 的 render_rules 绘制：[逐条填入 style-specs.yaml 的规则]。
不要复制任何参考人物的身份、服装、道具、文字、签名或水印。

[资产与本轮唯一变量]
生成一个 [asset_form]，画幅 [aspect_ratio]，目标输出 [target_pixel_size]，背景 [requested_background]。
人物数量为 1；安全边距 [safe_padding 或全身留白规则]。
本轮唯一可变项：[expression / pose / gesture / required_prop]。

[禁止项]
通用禁止：文字、签名、水印、无关标志、重复人物、裁切 [本资产必须完整的部位]。
风格禁止：[style-specs.yaml 的 negative_rules]。
~~~

## 原型、全身与扩展规则

### 原型

- 使用所选风格 default_prototype 和 background 默认值；用户明确品牌色或背景要求可替换默认值，只要不破坏风格规则。
- 优先单人、干净构图、无无关道具。角色轮廓缩小后仍要清楚可辨。
- 原型不通过 QA 时只修改失败字段。用户确认前，不生成表情包、动作包或换装包。

### 全身资产

仅在 style-specs.yaml 的 supported_forms 或用户确认的 conditional_forms 中生成全身。不要复用 IP-03 的体型、肩宽、腰线、腿长、裙子或鞋子作为通用默认。

~~~text
输入图是已确认的 approved_anchor。把同一个人物延展为完整全身 [asset_form]，不要重新设计脸、发型、上衣、眼镜、配饰、配色或绘画材质。
严格保持当前 character-spec-vN 的 proportions；如果未定义比例，使用所选风格 render_rules 的比例范围，不以样例人物体型为准。
人物从头顶到鞋底完整出现，四周保留安全边距。下装、袜子、鞋子和动作按以下优先级决定：本轮用户明确要求 → 已确认角色卡 → 输入照片的明确特征 → 与账号定位和已确认上衣协调的中性补全。无法判断时先提问。
~~~

### 表情、动作和贴纸

- 每次只生成一个独立 source_asset；不要要求模型在一张图中画多个人物或九宫格。
- 只允许改变当前 mutable_fields。其他身份和画风都必须继承 approved_anchor。
- 需要透明贴纸时，明确要求真实透明背景；输出后用 validate_delivery.py 检查实际 alpha。
- 所有独立资产 QA 通过后，才使用它们生成 preview_sheet。拼图只用于查看，不替代源资产。

## 生成后检查

每张图生成后，先执行通用检查，再执行 style spec 中该风格 qa：

- 角色版本、发型、眼镜、服装、比例和配色与 vN 一致。
- 一张图只有一个主体，且画幅、肢体、鞋子和安全边距符合 asset form。
- 没有文字、签名、水印、无关标志或参考人物可识别元素。
- 背景、尺寸和真实透明通道与 manifest 中的实际记录一致。
- 风格特征和 negative_rules 均符合。

一次失败只重做该资产，且仅修改失败原因相关字段。最多两次针对性重做；仍未通过时保留失败记录并请用户决定下一步。
