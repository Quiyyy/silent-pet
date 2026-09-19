# 制作说明

当前版本为 2026-09-20 短直卡通腿与招手局部运动修复版。参见 [当前制作与验收](cartoon-motion-2026-09-20.md) 和 [角色约束](character-spec.md)。

内置 imagegen 以原角色为参考制作短腿母图，随后按用户授权将完整腿部小幅旋转、交替抬起，禁止膝踝网格弯折。招手使用独立手掌图层，头骨、角、头发与身体固定。其他姿态统一短直裸腿，上半身只平移，不缩放头脸和卷轴。

当前来源为 `source/preclean/spritesheet.png`、`source/current-rows/`、`source/rig/master.png`、`source/wave/master.png`；工具与参数见 `source/rig/rig.json`，提示词与历史映射见 `production.json`。最终图集只从未清理基线进行一次边缘清理。

历史生成素材、旧工具和旧QA保留追溯用途。早期鞋子、肌肉腿、S形膝踝、招手牵连头角和中间候选的视线腿部缺口均被拒绝，不能视作当前制作依据。

结构、运动、视觉、浏览器和原生桌面测试分别记录。本轮已进行前四类检查，未进行原生桌面实时播放验收。当前有效证据由 `docs/artifact.json` 指定。
