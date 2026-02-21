---
type: agent_skill
---

## Description:
Check for user approval on LinkedIn draft and handle actions safely.

## Prompt:
Use Claude Code filesystem tools only. Set vault_path to 'AI_Employee_Vault'. List all .md files in /Pending_Approval folder that have 'linkedin_draft' in type frontmatter. For each file, read the content. Check the checkboxes under ## Approval Actions.

If the line '- [x] Approve and Post' is present (case-sensitive, with x inside []), then:
- Extract the post text from ## Post Text section.
- Append to Dashboard.md under a new section ## Recent Updates with timestamp and 'LinkedIn draft approved - ready for manual post. Text copied to clipboard.'.
- Move the .md file to /Done folder and add note at end 'Approved - user to paste and click Post manually.'.

If '- [x] Reject' is present, move the .md file to /Done folder and add note at end 'Rejected - reason: [extract any text below Reject checkbox]'.

If no checkboxes marked or only Edit, do nothing.

Do not open browsers or post to LinkedIn in this skill. Do not use external tools.
