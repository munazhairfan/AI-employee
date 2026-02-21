---
type: agent_skill
---

## Description:
Generate a LinkedIn post draft based on business triggers for manual posting.

## Prompt:
Use Claude Code filesystem tools only. Set vault_path to 'AI_Employee_Vault'. Read the file Dashboard.md and all .md files in /Needs_Action folder. Look for keywords like 'sales', 'business', 'project', 'lead', 'service', 'opportunity'. If any keyword found, generate a professional LinkedIn post text: 200 to 500 characters long, include 2-3 hashtags, end with a call-to-action like 'DM me for more details!'. Make it engaging and personalized based on the content read.

Then, create a new file in /Pending_Approval folder named LinkedIn_Draft_{use datetime.now().strftime('%Y-%m-%d_%H-%M')}.md. Write to the file:

Frontmatter section with:
```
---
type: linkedin_draft
status: pending
generated_at: {current ISO time}
---
```

Then `## Post Text` followed by the generated text, then `## Approval Actions` with these exact checkboxes:

- [ ] Approve and Post
- [ ] Reject (add your reason below this line)
- [ ] Edit (add your notes or changes below this line)

Do not post anything to LinkedIn. Do not use any external APIs or tools beyond filesystem.
