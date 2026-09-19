# silent pet

一个安静的 Codex v2 桌面宠物项目。当前角色名称为 **猎豹**：白发、骨角、绿披风，手持卷轴。

包含九组状态动画、16 个顺时针视线方向及独立默认姿势，重点改善动作循环、裁帧造成的尺寸跳动和方向切换。

<p>
  <img src="previews/idle.gif" alt="安静待机" width="192" height="208">
  <img src="previews/look-directions.gif" alt="16 个视线方向" width="192" height="208">
</p>

## 安装

将仓库根目录的 `pet.json` 与 `spritesheet.webp` 放在同一个宠物目录中：

```text
~/.codex/pets/bone-horn-sorceress/
  pet.json
  spritesheet.webp
```

若配置了 `CODEX_HOME`，则使用该目录下的 `pets/bone-horn-sorceress/`。更新已有宠物前，请备份原目录。

项目名为 **silent pet**，宠物 ID 仍为 `bone-horn-sorceress`，显示名称仍为“猎豹”，便于替换现有宠物。

## 内容

```text
pet.json                  可安装的宠物配置
spritesheet.webp          完成验证的 v2 图集
atlas.json                图集布局及状态描述
previews/                 九组动作、方向循环和图集预览
source/rows/              选定的原始生成条带
source/reference.png      原角色身份参考
source/look-anchors.png   已批准的四主方向
source/layout-guides/     生成时使用的布局参考
prompts/                  图像生成提示词
production.json           源图与提示词映射
docs/                    制作说明与验收记录
```

## 动画布局

图集为 **1536 × 2288**，8 列 × 11 行，每格 **192 × 208**。`spriteVersionNumber` 为 `2`。

| 行 | 状态 | 动画帧数 |
|---|---|---:|
| 0 | idle：呼吸与眨眼 | 6 |
| 1 | running-right：向右移动 | 8 |
| 2 | running-left：向左移动 | 8 |
| 3 | waving：招手 | 4 |
| 4 | jumping：小跳 | 5 |
| 5 | failed：失落反应 | 8 |
| 6 | waiting：期待用户回应 | 6 |
| 7 | running：读卷轴、处理任务 | 6 |
| 8 | review：检查结果 | 6 |
| 9–10 | 视线方向 | 16 |

第 0 行第 6 列（从 0 开始计数）保存 v2 默认视线姿势。其他未使用格保持透明。

视线以屏幕正上方为 `000`，按每步 22.5° 顺时针排列；`090` 为右，`180` 为下，`270` 为左。默认姿势独立于 `000`。

[查看完整方向图](previews/look-directions.png) · [查看完整图集](previews/contact-sheet.png)

## 制作与验证

在现有角色参考上使用内置 `image_gen` 制作，随后完成确定性提取、共享缩放、图集合成与一次边缘去色。仓库保存选定源图及提示词，不包含生成服务凭据或原工作环境的本机路径。

- 图集尺寸、版本、有效格和透明区域检查通过。
- 清理过程保持 alpha 不变，安装图集哈希与验收版本一致。
- 三个隔离审查代理完成随机 A/B 方向盲测，四主方向通过。
- 独立视觉审查检查了正常尺寸逐帧顺序与闭环；未宣称在桌面应用中实时播放验收。

完整记录见 [验收摘要](docs/artifact.json)、[最终视觉检查](docs/qa/final-visual-qa.json) 和 [制作说明](docs/production.md)。

## 2026-09-19 优化与验收

- 小跳落地姿态的高度相对待机由87.9%改善为97.0%，宽度由92.5%改善为98.7%；独立视觉检查确认头脸和卷轴没有随跳跃缩放。
- 左右跑采用不同支撑腿的连续相位；工作时追踪卷轴，完成时抬眼和克制点头。
- 16方向重新制作，修复三个低头斜向的左右辨识与跨行俯仰跳变。
- 三个隔离审查代理完成14组A/B盲测：28/28多数判定正确；84次个体判断79正确、5不确定、0反向。157.5、202.5、225三处重点水平判断一致正确。
- 提供原生尺寸/缩小/放大、逐帧及连续状态切换的本地预览，并附自动校验。

详细结果与限制见[本轮验收报告](docs/optimization-2026-09-19.md)。宿主桌面客户端的实时鼠标操作未自动测试，浏览器预览验收单独记录。

## 本地动作检查

在仓库根目录启动本地服务：

```bash
python -m http.server 8768 --bind 127.0.0.1
```

打开 [http://127.0.0.1:8768/preview/](http://127.0.0.1:8768/preview/)。

预览器支持九种状态、16方向、默认姿势、暂停与逐帧、0.5/1/2倍速、深浅背景和放大检查，也可运行工作、拖动、小跳三种连续切换场景。指针跟随仅在预览区内生效，不代表桌面客户端的触发方式。状态间直接切换原始帧，不使用淡入淡出掩盖问题。

## 自检

```bash
npm test
python -m pip install -r requirements.txt
python tools/validate_pet.py
```

Node测试覆盖帧时长边界、16方向映射、指针象限和状态序列边界；Python检查图集版本、尺寸、有效/空白格、透明像素和发布哈希。结构检查不能代替正常尺寸的动作、视线和跨状态视觉验收。
