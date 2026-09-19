Create one horizontal animation strip for Codex pet `bone-horn-sorceress`, state `running-left`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly 8 full-body frames in one left-to-right row on flat pure user-selected #0000FF. Treat the row as 8 invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: Preserve exact existing chibi adventurer: tan face, green eyes, horned skull helmet, white hair, dark green cloak, tan boots and original parchment scroll. Maintain unchanged head/torso/scroll scale across all actions. Restrained readable animation and smooth state transitions.. Preserve silhouette, face, proportions, markings, palette, material, style, and props.
Style: Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, clear silhouette, simple face, stable palette/materials, and crisp edges for chroma-key extraction. Style `auto`: Infer the most appropriate pet-safe style from the user request and reference images, then keep that exact style consistent across every row. User style notes: Match the existing clean shaded chibi illustration..
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: Dragging-left loop: show directional movement to the left through body and limb poses only.

State requirements:
- Show directional drag movement to the left through body, limb, and prop movement only.
- The row must unmistakably face and travel left.
- The movement cadence must alternate visibly across the 8 frames instead of repeating one nearly static stride.
- Do not draw speed lines, dust clouds, floor shadows, motion trails, or detached motion effects.

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet.


Repair goal: a true single eight-phase LEFTWARD gait with alternating support, not duplicated four-frame cycles. Use eight successive contact/absorption/passing/toe-off phases across both legs. Face and nose clearly screen-left. Preserve canonical proportions and original scroll; hair and cloak follow slightly late. Complete separated poses and ample outer margin. Last frame should flow into first, not abruptly switch leg or scale. Match approved rightward gait rhythm without mirroring the entire character.
