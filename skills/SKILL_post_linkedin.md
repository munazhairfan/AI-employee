---
type: agent_skill
---
## Description: Generate and draft LinkedIn post for sales.

## Prompt:
Using filesystem tools, read Dashboard.md from vault_path='AI_Employee_Vault'. Analyze recent processed items for business-related activity (e.g., invoices, client emails, new projects).

If business activity found:
1. Generate a sales-oriented LinkedIn post (2-3 sentences, professional tone)
2. Include: achievement/excitement + value proposition + call-to-action
3. Write to AI_Employee_Vault/Plans/LinkedIn_Post_Draft.md

Post format:
- Hook: What's new/exciting
- Value: What you offer
- CTA: "DM for details" or similar

Example:
"Excited to streamline business workflows with our new AI automation service! 
We help companies save 10+ hours/week on document processing. 
DM me if you'd like to learn more! #AI #Automation #Productivity"

If no business activity, output: "No LinkedIn post needed at this time."

## Triggers:
- New file processed in Needs_Action/
- Keywords: invoice, client, project, business, service, sale, payment
