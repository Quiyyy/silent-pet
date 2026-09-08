# Look mechanics
Original character: white-haired chibi adventurer wearing a brown-horned bone skull, forest-green cloak, ivory/brown armor, brown boots, holding the original parchment scroll.
Anchor: both boots and lower torso stay fixed, full body upright. Scroll remains in the same hands at chest height and same side. No whole-sprite rotation or rocking. Stable body/head proportions.
Natural mechanism: neck turns and pitches the head, skull/horns rotate with the head, green eyeballs and eyelids move together inside the face, long hair follows the head slightly while draping naturally. Lower torso and cloak hem remain anchored. No new eye layers.
000 up: chin and nose lift; lower facial surface visible; green eyes aim clearly above head center beneath lifted upper eyelids. Head is pitched up, not neutral.
090 screen-right: face turns toward image right, nose tip and pupils move right of head center; left facial surface more visible and far eye narrower. Torso still front-facing.
180 down: chin and nose tip lower toward the scroll, eyelids lower; upper skull surface becomes more visible. Eyes clearly aim downward, not shut.
270 screen-left: face turns toward image left, nose tip and pupils move left of head center; right facial surface more visible and far eye narrower. Torso still front-facing.
Motion budget: head yaw up to 30 degrees toward either screen side, pitch up/down about 18 degrees; position change modest, head scale constant. Equal 22.5-degree attention steps must smoothly interpolate these pose families, moving the same features by comparable amounts. No teleporting scroll or boots. Neck and hair follow continuously. Preserve row-9 scale and registration for row 10 and closure 337.5 -> 000.
Diagonals need both an unmistakable horizontal head turn and vertical pitch/eye cue. Near-vertical directions may use subtler horizontal cues but must advance monotonically through the sequence.
