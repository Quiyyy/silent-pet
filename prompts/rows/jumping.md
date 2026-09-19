Create one horizontal animation strip for Codex pet `bone-horn-sorceress`, state `jumping`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly 5 full-body frames in one left-to-right row on flat pure user-selected #0000FF. Treat the row as 5 invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: Preserve exact existing chibi adventurer: tan face, green eyes, horned skull helmet, white hair, dark green cloak, tan boots and original parchment scroll. Maintain unchanged head/torso/scroll scale across all actions. Restrained readable animation and smooth state transitions.. Preserve silhouette, face, proportions, markings, palette, material, style, and props.
Style: Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, clear silhouette, simple face, stable palette/materials, and crisp edges for chroma-key extraction. Style `auto`: Infer the most appropriate pet-safe style from the user request and reference images, then keep that exact style consistent across every row. User style notes: Match the existing clean shaded chibi illustration..
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: Hover jump loop: anticipation, lift, airborne peak, descent, and settle through body height.

State requirements:
- Show the jump through pose and vertical body position only: anticipation, lift, airborne peak, descent, settle.
- Do not draw ground shadows, contact shadows, drop shadows, oval shadows, landing marks, dust, smears, bounce pads, or motion marks under the pet.
- Keep the background outside the pet perfectly flat chroma key with no darker key-colored patches.

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet.


CRITICAL REPAIR: the old jump looked globally smaller than idle. This row must preserve head, skull helmet, face, torso and scroll pixel scale throughout, matching canonical standing proportions. Very gentle 5-phase hop: near-neutral shallow knee bend, push-off, tiny airborne apex with tucked knees, soft landing, return very close to the first shallow bend. Express most foot lift by knee flexion, NOT shrinking body/head/scroll. Head apex rises only about 2 percent of standing body height. Keep the total row envelope within about 1.03 times natural standing height. The head and scroll must look equally large before, during and after jump. No huge empty vertical travel, no deep crouch, no body scaling. Full figure, floor-free blue background.
