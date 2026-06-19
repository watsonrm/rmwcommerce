# Commerce Taxonomy Design — Claude Code Skill

**Trigger phrases:**
- "Audit my taxonomy against the commerce-taxonomy framework"
- "Design a faceted taxonomy for my commerce company database"
- "My agents are classifying the same company differently — help me find why"
- "Review my ecosystem role vocabulary"
- "Help me design scope notes for my taxonomy"
- "Should I add a new category to my taxonomy"

**when_to_use:** Load when the user is designing, auditing, or debugging a company/entity classification taxonomy for a commerce-adjacent CRM, database, or agent pipeline. Especially relevant when they have AI agents classifying companies and noticing inconsistent results.

---

## What this skill does

Given a description of how you currently classify companies (roles, verticals, relationship types — what fields you use, what values you allow, whether agents write to these fields), this skill:

1. Identifies which of the seven taxonomy design problems are present in your current setup
2. Recommends the highest-leverage fix for your specific situation
3. Drafts vocabulary values with scope notes for any new or revised facets you want to build
4. Writes deterministic conflict-resolution rules if agents are disagreeing on the same entity

The skill works from the framework in [Designing an E-Commerce Taxonomy Your AI Agents Can Maintain](../../guides/ecommerce-taxonomy-for-ai-agents.md).

---

## Step 0 — Understand what you have

Ask the user:
- What system holds your company/entity records? (CRM, database, spreadsheet, custom store)
- What fields do you currently use to classify companies? List the field names and the allowed values.
- Do AI agents write to these fields? If so, how many agents, and do they share a definition of what each value means?
- Where are you seeing inconsistency? (Same company tagged differently in two places, or agents producing different tags for the same entity, or something else)

If the user has already described their setup, skip directly to Step 1.

---

## Step 1 — Diagnose against the seven practices

Check the user's described setup against each of these. Flag only the ones that are actually present — do not manufacture findings.

| # | Check | Present? |
|:--|:--|:--|
| 1 | Is the Role/Type vocabulary inherited from LinkedIn industry codes, SIC, NAICS, or a similar general-purpose list? | |
| 2 | Is Role, Vertical (end-market), and Relationship type all in one field rather than three separate facets? | |
| 3 | Are vocabulary values defined only by their names — no include/exclude examples, no scope notes? | |
| 4 | Do agents reference vocabulary values by their human-readable label (string) rather than by a stable ID? | |
| 5 | Are there classification assignments without provenance metadata (source, date, confidence)? | |
| 6 | Does the vocabulary lack hierarchy (sub-types), typed entity-entity relationships, or lifecycle status for acquired/defunct companies? | |
| 7 | Does classification happen in only one surface (e.g., content tagging) rather than at ingestion and reused across all surfaces? | |

---

## Step 2 — Recommend the highest-leverage fix

Order the present issues by the priority table in the guide. Lead with one concrete recommendation. Do not prescribe all seven at once unless the user explicitly asks for a full audit.

For the top issue, produce:

1. A short description of the problem as it appears in their specific setup (not generic)
2. The concrete change required (field addition, vocabulary redesign, schema change, scope note template)
3. An estimate of effort
4. One example of what the fixed version looks like for a company they named or a category they mentioned

---

## Step 3 — Draft vocabulary if requested

If the user wants to build or extend an Ecosystem Role vocabulary (or another facet), draft the values with scope notes in this format:

```
Value: [Role Name]
ID: [stable-id-slug]  ← this must be a slug, not the label
Definition: [1-2 sentences describing what this role covers in the commerce stack]
Includes: [2-3 examples of companies or company types that belong here]
Excludes: [1-2 examples of types that are adjacent but should NOT be here, with where they belong instead]
Parent (if sub-type): [broader role]
```

Produce only the values the user is actually building. Do not produce a full vocabulary unprompted — ask how many values they need before drafting.

---

## Step 4 — Write conflict-resolution rules if agents disagree

If the problem is two agents classifying the same entity differently, produce a deterministic resolution policy:

```
Source priority: [list sources in priority order — e.g., human review > agent-A > agent-B > import]
Scalar conflict: newer timestamp wins when both sources have the same priority
High-confidence contradiction: if confidence >= [threshold] and two sources disagree, escalate to [queue/human/flag — pick the one that fits their system]
Escalation format: log {entity_id, facet, agent_a_value, agent_a_confidence, agent_b_value, agent_b_confidence, timestamp}
```

Fill in the thresholds and escalation target based on what the user has told you about their system.

---

## Verification step

After delivering a recommendation, ask:

> "Does this match what you actually see in your classification records? If you can share one or two examples of companies that are classified in a way that seems wrong, I can verify the recommendation applies to your specific case."

This step is not optional — it catches the case where the diagnosis was based on a misunderstood description.

---

## What this skill does not do

- It does not write code to implement the taxonomy changes (point the user to a developer or to Claude Code's general coding mode for that)
- It does not import or read actual CRM records (the user must describe or paste the relevant data)
- It does not make vocabulary decisions on behalf of the user — it drafts options for human review and approval, per the governance principle in Step 4 of the guide
