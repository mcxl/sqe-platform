# Arm C Feasibility Concern

Recorded: 16 September 2026, after correction2 build passed and before any Arm C execution.

Status: Read-only planning concern. No native placement failure has been observed. Not an application defect finding.

Approved Arm C requires Copy action 1 entirely above the ScrollView midpoint after scrolling, with stable frames.

The unchanged copyConfirmation fixture has one action and no notices.
Source: DebugScenario.swift lines 26–30 and 56–57, at commit 52b212aca02190ee0e742debe383fa6016fe36b9.

The Copy control is last in its action card. Only its confirmation, card padding, Refresh, Sign out and spacing follow.
Source: Views.swift lines 183–214 and 294–310, SHA-256 3635901a1aa80410bbfeb138a5dafd3b233c2b4b312b8c90ee6fd57a29aa10dd.

The retained A5 post-copy image shows Copy in the lower viewport. Refresh follows and Sign out starts near the bottom.
PNG: arm-A/repetition-5/batches/001/attachments/F09A5969-F68A-457B-A935-786533BFFAA4.png.
SHA-256: f67cc32e79c38a0d768a2f2801f346f69ff76cd09efa4cd6be6d0a17d140646a.

Inference: There appears insufficient trailing content to place Copy above the viewport midpoint at a stable scroll offset.
This is not a measured maximum-offset result. Native scroll geometry could disprove the inference.
Adding a spacer, another action, a smaller viewport or another orientation would change the approved comparison.
Do not make any such change silently. Keep Arm C on hold pending resolution of this concern.

Arm B is independent and may continue under existing authority and stop conditions.
If B reports a finding, apply its existing stop row regardless of this concern.
