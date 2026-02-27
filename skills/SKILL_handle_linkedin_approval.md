---
type: agent_skill
---

## Description:
Check LinkedIn draft approval status and prepare for manual posting (draft-only, no execution).

## Prompt:
Use filesystem tools only. Set vault_path to 'AI_Employee_Vault'. List all .md files in /Pending_Approval folder with type 'linkedin_draft' or 'linkedin_post_draft' in frontmatter. For each file, read the content and check the Approval Actions checkboxes.

If '- [ ] Approve' is marked (user adds [x]):
- Extract the post text from ## Post Text section
- Copy post text to clipboard using pyperclip
- Update file status to 'approved_ready_for_manual_post'
- Move file to /Done folder
- Append note: "Approved at {timestamp} - Post text copied to clipboard. User to paste and post manually on LinkedIn."
- Output: "LinkedIn draft approved. Post text copied to clipboard. Please paste on LinkedIn and post manually."

If '- [ ] Reject' is marked:
- Extract rejection reason (text below Reject checkbox)
- Move file to /Done folder
- Append note: "Rejected at {timestamp} - Reason: {extracted reason}"
- Output: "LinkedIn draft rejected: {reason}"

If '- [ ] Edit' is marked or no checkboxes marked:
- Leave file in /Pending_Approval
- Output: "Draft pending edit/review. No action taken."

**CONSTRAINTS:**
- Do NOT open browsers
- Do NOT post to LinkedIn
- Do NOT use external APIs
- Only filesystem and clipboard operations allowed
- No additions, no hallucinations
