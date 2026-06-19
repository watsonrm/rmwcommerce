---
title: Designing an E-Commerce Taxonomy Your AI Agents Can Maintain
description: Why inherited industry codes rot the moment AI agents start reading and writing them at scale — and the seven design decisions that produce a taxonomy that doesn't.
date: 2026-06-19
author: Rick Watson
agent_friendly: true
keywords: ecommerce taxonomy, commerce ontology, AI agents taxonomy maintenance, faceted classification, SKOS, ecosystem roles, entity classification, knowledge organization, CRM taxonomy design
---

# Designing an E-Commerce Taxonomy Your AI Agents Can Maintain

**Most company taxonomies are borrowed industry-code lists. They look fine in a CRM field. They collapse the moment AI agents start reading and writing them at scale.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-06-19 · Roughly 18 min read*

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- A well-designed taxonomy makes AI-classified entities consistent across every agent that touches them — no drift, no contradictions, no "we classified Adyen as payments in one place and fintech in another."
- Faceted classification (separate dimensions for role, vertical, and relationship) makes the same entity answerable to many questions without forcing it into a single wrong bucket.
- Stable IDs with human-readable scope notes give agents a classification target that survives renames and organizational re-thinks.
- A split governance model — human-gated vocabulary changes, agent-driven instance classification — is the difference between a taxonomy that improves over time and one that rots.

### Where to spend your time, in priority order

| # | Practice | Why it matters | Effort |
|:--|:--|:--|:--|
| 1 | **Build an Ecosystem Role axis** — replace the inherited industry-code spine with a commerce-specific role taxonomy | Industry codes collapse your most important contacts into "Computer Software." A role axis tells agents what each company actually *does* in the commerce stack. | 1–2 days to draft; one calibration pass |
| 2 | **Separate the three conflated dimensions into orthogonal facets** — Role, Vertical, and Relationship independent of one another | A single industry field smears three different questions into one answer. Facets let you ask and answer each independently. | Schema refactor; existing records need a backfill pass |
| 3 | **Write scope notes every agent will read** — include/exclude examples for every value, not just a name | Identical names classify identically only when agents read identical definitions. Without scope notes, classification drifts. | 2–4 hrs per vocabulary value |
| 4 | **Assign stable IDs to every vocabulary value** — labels can change, IDs can't | A rename from "3PL" to "Logistics & Fulfillment" should be a label update, not a schema migration. | One-time schema discipline |
| 5 | **Add provenance + confidence per assignment** — source, assigning agent, date, confidence score | Provenance is what lets you detect contradiction and route low-confidence items to human review. | Schema addition |
| 6 | **Add the graph layer** — hierarchy, typed relationships, and lifecycle status | Hierarchy lets agents classify coarse or fine. Relationships turn the taxonomy into a traversable graph. Deprecation beats deletion for acquired/merged companies. | Incremental build-out |
| 7 | **Tag at ingestion, reuse everywhere** — one seam, not a sidecar | A taxonomy nobody actually reads at classification time is decoration. Tag once when an entity enters the system; reuse across every surface. | Integration work; pays off continuously |

**Most teams should fix #1 and #2 and stop. The rest matters for agents that write — not just agents that read.**

---

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/ecommerce-taxonomy/`](../skills/ecommerce-taxonomy/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/ecommerce-taxonomy ~/.claude/skills/
```

Then describe your current company/contact classification setup to Claude — how you're currently tagging companies, what fields you use, what an AI agent does with those tags — and say one of these:

> "Audit my taxonomy against the commerce-taxonomy framework"
> "Design a faceted taxonomy for my commerce company database"
> "My agents are classifying the same company differently — help me find why"

Claude will load the skill on demand and walk you through the design decisions most likely to fix your specific problem. The article below is the reasoning behind the framework — read it for the *why*; the skill is the *how*.

---

## 1. Industry lists are the wrong spine for commerce

The most common starting point for a commerce company taxonomy is a standard industry-code list: LinkedIn's industry categories, SIC codes, NAICS codes, or some hybrid thereof. These were designed to classify what a company sells — to regulators, to market researchers, to investors who need a sector label. They were not designed to answer: *where does this company sit in the commerce stack?*

The tell is your largest bucket. Standard codes collapse an enormous range of distinct commerce functions into "Computer Software" or "Information Technology and Services": a commerce platform, a payments processor, a 3PL, a marketplace-enablement layer, a retail-media ad tech stack, and a tax compliance vendor all land in the same place. That's not just imprecise — it actively breaks any downstream logic that depends on the classification.

For a commerce-specific taxonomy, the right spine is an **Ecosystem Role** axis: a vocabulary of the actual positions companies occupy in the commerce stack. Something like:

- **Commerce platform** — the core SaaS layer brands and retailers run their storefront on (Shopify, BigCommerce, Salesforce Commerce Cloud)
- **Payments / fintech** — payment processors, gateways, BNPL providers (Adyen, Stripe, Klarna)
- **Logistics / 3PL** — fulfillment, warehousing, last-mile carriers (ShipBob, ShipStation, Maersk)
- **Marketplace enablement** — software that helps brands sell on or operate marketplaces (Mirakl, ChannelAdvisor)
- **Retail media / adtech** — advertising platforms attached to retail or commerce contexts
- **Martech** — marketing automation, personalization, email, CDP tools
- **Systems integrator / agency** — firms that implement the above
- **Brand** — companies that manufacture and sell consumer goods
- **Retailer** — companies whose primary business is reselling goods to consumers
- **Investor** — VCs, PE firms, growth equity focused on commerce
- **Analyst / media** — coverage, research, publications (including newsletters, podcasters, analysts)

This isn't exhaustive — you'll extend it based on the specific corner of commerce you work in. What matters is that every value answers the question *what does this company do in the commerce stack*, not what industry it belongs to.

---

## 2. Separate the three conflated dimensions

Standard CRM design puts everything about a company into a single "Industry" or "Type" field. The problem is that field is being asked to answer three completely different questions at once:

- **What is this company?** (its role in the commerce stack)
- **What does it serve?** (its end-market vertical — apparel, grocery, B2B, automotive)
- **How do I engage it?** (its relationship to you — prospect, partner, investor, competitor, media, sponsor)

These are independent questions. A payments vendor (role) might serve fashion brands (vertical) and be a potential podcast sponsor (relationship). Putting all three into one field means answering one question forces a wrong answer to the others.

The design move here is **faceted classification** — organizing a taxonomy into orthogonal, independent dimensions rather than one deep tree. [Faceted classification](https://en.wikipedia.org/wiki/Faceted_classification) was formalized by S.R. Ranganathan in his Colon Classification (1933), which broke subjects into five independent facets (Personality, Matter, Energy, Space, Time). The core property of facets: they must be orthogonal — the choice of a value on one facet has no bearing on which values are valid on another. ([Source: Ranganathan and the Faceted Classification Theory](https://www.researchgate.net/publication/321840994_Ranganathan_and_the_faceted_classification_theory))

Applied to commerce:

| Facet | What it answers | Example values |
|:--|:--|:--|
| **Ecosystem Role** | What is this company in the commerce stack? | Commerce platform, Payments, Logistics/3PL, Marketplace enablement, Retailer, Brand |
| **Vertical / End-market** | What commerce segment does it primarily serve? | Fashion/apparel, Grocery/CPG, B2B/wholesale, Automotive, Marketplace, Omnichannel |
| **Relationship** | How do you engage this entity? | Prospect, Client, Partner, Sponsor, Competitor, Investor, Media/analyst |

Each facet is a separate field. Each can evolve independently. A company's role doesn't change when your relationship to it changes.

For the theoretical underpinning of why this works: the W3C's Organization Ontology (`org:Role`) was designed as exactly this kind of extensibility hook — it's a subclass of `skos:Concept` with no predefined values, and the spec explicitly states it "does not provide category structures for organization type, organization purpose or roles," expecting domain-specific vocabularies to fill the gap. ([W3C Organization Ontology](https://www.w3.org/TR/vocab-org/)) That gap is precisely what a commerce-specific role axis fills.

---

## 3. Design for agents — the failure mode is classification drift

A taxonomy used by one person in a CRM can tolerate a lot of informality. Names shift, categories blur, and the human who did the original classification keeps the canonical interpretation in their head.

The moment multiple AI agents start reading and writing the same taxonomy, that informality becomes a defect. Two agents will tag the same company differently if they're reading different definitions — or no definitions at all — for what a value means. Over time, the same entity gets classified differently across contexts, and the taxonomy becomes meaningless as a filter or a signal.

The design requirements that prevent this:

**Self-describing vocabulary.** Every value in the taxonomy needs a scope note: a brief statement of what the value includes, what it excludes, and at least one include/exclude example. This is the mechanism SKOS uses — `skos:scopeNote` "supplies some, possibly partial, information about the intended meaning of a concept, especially as an indication of how the use of a concept is limited in indexing practice." ([W3C SKOS Primer](https://www.w3.org/TR/skos-primer/))

A scope note for "Marketplace Enablement" might read: *"Software or services that help brands or retailers sell on existing third-party marketplaces, or that enable a company to operate its own marketplace platform. Includes: marketplace management software, catalog syndication tools, marketplace analytics. Excludes: companies that operate a marketplace themselves (use 'Marketplace') or payment processors (use 'Payments / Fintech')."*

Without that, two agents will each draw their own boundary.

**Stable IDs, not labels, as the referent.** Labels change. A category called "3PL" might become "Logistics & Fulfillment" two years later when you reorganize the vocabulary. If every reference — in code, in data, in other classification records — points to the label rather than a persistent identifier, that rename is a migration project. If references point to a stable ID, the rename is a label update and nothing breaks. The W3C's SKOS specification uses URIs precisely for this property: they allow concepts to be "referred to unambiguously from any context." ([W3C SKOS Reference](https://www.w3.org/TR/skos-reference/))

**Provenance and confidence per assignment.** Every classified entity should carry metadata about *how* the classification was made: the source (an agent, a human, an import), the date, and a confidence score. This data is what lets you detect when two agents have classified the same entity differently, route low-confidence assignments to human review, and reconstruct why an entity ended up with the tag it has.

SKOS itself doesn't handle provenance natively — the specification explicitly notes that "using the SKOS mapping properties is no substitute for the careful management of RDF graphs or the use of provenance mechanisms." You add provenance at the application layer. ([W3C SKOS Reference](https://www.w3.org/TR/skos-reference/))

**Deterministic conflict resolution.** When two agents disagree on a classification, the system needs a rule, not a coin flip. A workable default: one canonical source per facet per entity (e.g., the human-reviewed record wins over agent-assigned), newer timestamp wins on scalars when both are agent-assigned, high-confidence contradiction from a second agent escalates to human review rather than auto-resolving.

---

## 4. Split governance: schema vs. instance

One of the most important distinctions in taxonomy design is between the vocabulary (the set of values and their definitions) and the classification (the assignment of those values to specific entities).

**Vocabulary changes are rare and should be human-gated.** Adding a new Ecosystem Role, retiring an existing one, splitting a category into two — these are structural decisions with wide downstream consequences. Every agent that uses the taxonomy interprets the vocabulary. A vocabulary change that ships without review can break classification logic across the whole system simultaneously. Gate vocabulary changes on human review.

**Instance classification is frequent and should be automated.** An agent tagging a new company's Ecosystem Role when it enters your database, updating a relationship status, inferring a vertical from website copy — this is high-volume, low-consequence work. An agent that misclassifies one company creates one wrong record. An agent that ships a wrong vocabulary change can corrupt thousands.

The division maps to the distinction SKOS draws between concept schemes (the vocabulary) and the individual concepts and their assignments (the instance layer). Both can live in the same system, but their change cadence and authorization model should differ.

This also means agents must **never invent new vocabulary values on their own**. An agent that encounters a company it can't fit into any existing Ecosystem Role should escalate — log the gap, flag for human review, and leave the field blank or set to a controlled "needs classification" value — not generate a new value and start using it. That's how taxonomies rot: the vocabulary expands silently, values multiply without scope notes, and the system loses the ability to make consistent comparisons across entities.

---

## 5. The graph layer beyond facets

Facets classify an entity in isolation. A graph connects entities to each other and gives agents context they couldn't derive from any single record.

Three layers to build in roughly this order:

**Hierarchy within each facet.** Not all Ecosystem Roles are flat peers. BNPL (buy now, pay later) is a sub-type of Payments/Fintech. Same-day delivery software is a sub-type of Logistics. Hierarchy lets an agent classify at the appropriate level of specificity: a company can be tagged as both "Payments / Fintech" (coarse) and "BNPL" (specific), and queries at either level return the right result. SKOS `skos:broader` and `skos:narrower` properties express exactly this: a triple asserting `BNPL skos:broader Payments` says that Payments is more general than BNPL, making BNPL a transitive member of the Payments branch. ([W3C SKOS Reference](https://www.w3.org/TR/skos-reference/))

**Typed entity-to-entity relationships.** The most underused layer in most company databases is the relationship graph between entities. Not a free-text notes field — typed edges with specific semantics:

- `owns` / `acquired-by` — corporate structure
- `sponsors` / `sponsored-by` — financial relationship
- `partners-with` / `integrates-with` — commercial relationship
- `competes-with` — competitive positioning

An agent with access to this graph can answer questions that no facet alone can: *which logistics vendors are now owned by the same parent company as this payment processor?* That's not a lookup — it's a traversal.

**Lifecycle status.** Companies get acquired, merge, go defunct, or go into stealth. A taxonomy that simply deletes an acquired entity loses the history and breaks any downstream reference to it. The right pattern: deprecate, don't delete. Mark the entity with a lifecycle status (active, acquired, merged, defunct, stealth) and redirect to its acquirer. Any reference to the acquired entity resolves to the current canonical record. Any agent that queries for "active" entities gets the right list; any query for "acquired" entities shows the historical record.

---

## 6. One seam, not a sidecar

The most common failure mode for a company taxonomy isn't bad design — it's selective deployment. The taxonomy gets built, applied to published content or the main CRM object, and then everything else in the pipeline ignores it. New data comes in, tasks get created, agents run — and they work with unclassified or inconsistently classified entities, defeating the whole investment.

**Tag at ingestion.** The classification pass should happen when an entity first enters the system, not as a downstream enrichment job. When a new company record is created — from a form fill, an import, a CRM sync, an agent's research — the classification step runs immediately. The facet values get written to the record before anything else reads it.

**Persist to a shared store.** Classifications live in one place. Every agent that needs to know what Ecosystem Role a company occupies reads that single record. They don't re-derive it independently from raw company data. Re-derivation is where drift comes from.

**Reuse across every surface.** The same classification that determines what bucket a prospect falls into in the CRM should also be the classification that filters which companies show up in a newsletter source list, which contacts get tagged in a research brief, and which entities an agent uses when building a competitive landscape. A taxonomy that's applied in one surface and ignored in others isn't a taxonomy — it's a decoration.

**Telemetry closes the loop.** Three signals tell you when the taxonomy needs attention:

- *Unused concepts* — vocabulary values that haven't been assigned to any entity in a meaningful window. These are dead vocabulary: candidates to retire or merge.
- *Unclassifiable entities* — entities that agents consistently fail to assign to any existing value. These are new-concept candidates: signals that the vocabulary has a gap.
- *Cross-agent disagreement* — two agents classifying the same entity differently. The first sign of an ambiguous scope note, and the earliest signal to catch a vocabulary definition problem before it propagates.

---

## 7. Your CRM is a source, not just a consumer

A well-maintained CRM contains a breadth layer that most companies never fully use: every company you've ever tracked, across every relationship and context. That database is a natural seed for the entity graph.

The CRM feeds the taxonomy breadth (the full set of entities); your observed signals feed the taxonomy salience (which entities and which relationships are active, recent, and relevant). Neither alone is sufficient. A taxonomy seeded only from CRM contacts has history but no current relevance signal. A taxonomy built only from recent content mentions has relevance but no structural depth.

The synthesis of the two — entity graph from CRM, salience from observed signals — is what gives an AI agent a foundation to work from rather than starting every classification task cold.

---

## Prior art and the white space

Before designing your own vocabulary, it's worth knowing what already exists — and why none of it is what you need.

Efforts to classify the commerce ecosystem fall into four corners:

**Machine-readable role ontologies — but sparse or wrong axis.**
GoodRelations (Martin Hepp, OWL v1.0) defines `gr:BusinessEntityType` to model a company's "position in the value chain," which is exactly the right axis — but it predefines only four values: Business, Enduser, PublicInstitution, and Reseller. ([GoodRelations v1](http://www.heppnetz.de/ontologies/goodrelations/v1.html) · [schema.org/BusinessEntityType](https://schema.org/BusinessEntityType)) The GS1 Web Vocabulary `OrganizationRoleType` is the most developed precedent: a real machine-readable OWL vocabulary enumerating 137 org roles — RETAILER, E_TAILER, MARKETPLACE_OPERATOR, BRAND_OWNER, DISTRIBUTOR, MANUFACTURER, CARRIER, and more. ([GS1 OrganizationRoleType](https://ref.gs1.org/voc/OrganizationRoleType)) That proves the role-by-position axis is viable as a controlled vocabulary. The catch: GS1's roles are primarily transactional/GDSN party roles (also BILL_TO, SHIP_TO, INVOICEE) — logistics-chain participants, not a populated map of the commerce technology ecosystem. And they're human-governed under GS1's Global Standards Management Process, updated on a standards-body timeline, not agent-maintainable.

**Machine-readable vocabularies — but on a different axis.**
Schema.org `Organization` covers institutional types: Corporation, NGO, NewsMediaOrganization, and the like. ([schema.org/Organization](https://schema.org/Organization)) Wikidata classifies companies by industry via P452. Neither is a commerce-stack role vocabulary — they answer "what kind of entity is this" rather than "where does it sit in the commerce stack."

**Machine-readable protocols — but for data flow, not company classification.**
UCP, ACP, and ONX (covered in Section 8) define how participants connect and transact. They enumerate a small set of protocol actors (merchant, agent, payment provider, consumer). Useful for understanding what flows between participants; not designed to classify the full range of companies in your CRM.

**Richly-populated role maps — but static.**
LUMAscapes and the chiefmartec Marketing Technology Landscape do have rich commerce-role taxonomies, updated annually. They're human-editorial visuals, not machine-readable controlled vocabularies. An agent can't read one to classify a company.

The white space is the combination: a role-by-position vocabulary that is richly populated (more than 4 or even 137 roles), covers the commerce technology ecosystem (not just GDSN logistics parties), and is agent-maintainable at the instance level. The closest existing model architecturally is GS1's — the design is right, the domain is different.

---

## 8. Design for the agentic-commerce era

Every role taxonomy reflects the participants its authors expected to exist. Legacy taxonomies — built around brands, retailers, platforms, and agencies — have no slot for a category that is now driving measurable purchase volume: the AI assistant acting as a commerce surface.

When a consumer asks Gemini to "find and buy the cheapest version of this," Gemini is not a search engine, a marketplace, or a retailer in any traditional sense. It is a discovery and checkout surface — an intermediary that surfaces products, surfaces offers, and (via standards like Google's UCP) converts intent into a transaction without the consumer visiting a storefront. Your Ecosystem Role axis should have a value for this. Something like **AI commerce surface** captures what it actually does: it occupies a position in the commerce stack that is part channel, part agent, and part distribution point, and it behaves differently from every role that existed before it.

Three emerging standards are worth tracking against your taxonomy — not because they replace a role taxonomy, but because they define what *flows* between participants, not who the participants *are*. The UCP spec is explicit about this: participant "roles are defined by direction of capability flow, not by industry vertical." ([ucp.dev — Core Concepts](https://ucp.dev/documentation/core-concepts/)) A well-designed role taxonomy composes with these protocols rather than competing:

- **Google's Universal Commerce Protocol (UCP)** — an open standard for turning AI-surface interactions into purchases. Its actors include a merchant (who retains merchant-of-record status and customer data ownership), a consumer, credential providers, and payment services. Currently operating across AI Mode in Google Search and Gemini. Interoperates with three adjacent protocols: AP2 (Agent Payments Protocol), A2A (Agent-to-Agent), and MCP (Model Context Protocol). ([developers.google.com/merchant/ucp](https://developers.google.com/merchant/ucp) · [UCP Core Concepts](https://ucp.dev/documentation/core-concepts/))

- **OpenAI + Stripe's Agentic Commerce Protocol (ACP)** — a protocol and API spec, not a role taxonomy. ACP defines 3–4 transactional actors (businesses, AI agents, payment providers) and standardizes how they authenticate and transact. The scope is the transaction flow; company classification is out of scope. ([github.com/agentic-commerce-protocol](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol))

- **The Commerce Operations Foundation's ONX (Order Network eXchange)** — an open standard for post-purchase operational data exchange: orders, products, inventory, shipments, and returns. Built as a vocabulary layer on top of MCP, with 14 initial MCP tools and 9 shared resources. Launched with 52 member companies representing over $1 trillion in annual GMV. Where UCP and ACP standardize the transaction moment, ONX standardizes what happens after it — and the spec is clear that it is "not a company classification system." ([commerceopsfoundation.org](https://commerceopsfoundation.org/the-universal-language-for-modern-commerce-introducing-the-order-network-exchange-onx/))

Three practical moves for a taxonomy designer watching this space:

1. **Add an AI commerce surface role** to your Ecosystem Role axis. The entities that belong here — AI assistants with shopping integrations, agentic buying tools — are already parties to real transactions and will increasingly appear in your partner, competitor, and channel data.
2. **Consider a typed "implements" relationship** for standards adoption: which entities in your database have committed to UCP, ACP, ONX, MCP, or AP2. This is forward-looking signal, not noise. A standards adopter list (ONX's founding 52 is a ready-made seed) is a natural starting point.
3. **Treat protocol support as a facet attribute, not a role.** UCP, ACP, and ONX tell you how a participant connects — not what role it plays. Keep them as attributes on an entity record, separate from its Ecosystem Role classification.

---

## Anti-patterns to recognize

Before spending time on a taxonomy refactor, check whether these patterns are already in place. Each one costs more to undo later than to avoid now.

**The industry-list spine.** Building on LinkedIn industry codes, SIC, or NAICS rather than a commerce-specific vocabulary. The immediate symptom: your largest bucket becomes "Computer Software" or "Technology" and covers everything from payments to logistics to brand loyalty platforms.

**One field for everything.** A single "Industry" or "Type" field that conflates Role, Vertical, and Relationship. The immediate symptom: classifying a prospect as "Retail Media" means losing the context that it's also a brand, also a marketplace, and also the company that just signed a sponsorship.

**Human-only scope notes — or none at all.** Definitions written for human readers that assume shared context an AI agent doesn't have. The immediate symptom: two agents assign the same company to two different values with equal confidence, and there's no text in either scope note that would differentiate them.

**Labels as keys.** Using a human-readable label string as the programmatic reference rather than a stable ID. The immediate symptom: renaming a category requires a find-and-replace across every system that uses the taxonomy, and something always gets missed.

**Delete-don't-deprecate.** Removing acquired, merged, or defunct companies from the taxonomy rather than marking them with lifecycle status. The immediate symptom: references break, historical reports become inconsistent, and agents lose context on acquisitions and corporate lineage.

**The sidecar tagger.** Running entity classification in one place (a content-tagging job, a CRM enrichment workflow) while the rest of the pipeline uses unclassified entities. The immediate symptom: the taxonomy exists in one corner of the system while every other agent works without it.

---

## Sources & Attribution

**Standards specifications (primary sources)**

- [W3C SKOS Simple Knowledge Organization System Reference](https://www.w3.org/TR/skos-reference/) — formal specification for `skos:broader`, `skos:narrower`, `skos:scopeNote`, stable URI-based concept identification, and the note on provenance lying outside SKOS's native scope
- [W3C SKOS Primer](https://www.w3.org/TR/skos-primer/) — `skos:scopeNote` definition and usage guidance; `skos:prefLabel` and `skos:altLabel`; SKOS as a framework for thesauri, classification schemes, and controlled vocabularies
- [W3C Organization Ontology (ORG)](https://www.w3.org/TR/vocab-org/) — `org:Role` as a subclass of `skos:Concept` with no predefined values; the spec's explicit statement that it "does not provide category structures for organization type, organization purpose or roles"

**Existing role ontologies and vocabularies (prior art)**

- [GoodRelations v1.0 (Martin Hepp)](http://www.heppnetz.de/ontologies/goodrelations/v1.html) — `gr:BusinessEntityType` models a company's position in the value chain; defines four roles (Business, Enduser, PublicInstitution, Reseller); also at [schema.org/BusinessEntityType](https://schema.org/BusinessEntityType)
- [GS1 Web Vocabulary — OrganizationRoleType](https://ref.gs1.org/voc/OrganizationRoleType) — machine-readable OWL vocabulary enumerating 137 org roles (RETAILER, E_TAILER, MARKETPLACE_OPERATOR, BRAND_OWNER, DISTRIBUTOR, MANUFACTURER, CARRIER, BILL_TO, SHIP_TO, and more); primary proof that the role-by-position axis is viable as a controlled vocabulary; human-governed under GS1's Global Standards Management Process
- [schema.org/Organization](https://schema.org/Organization) — institutional types (Corporation, NGO, NewsMediaOrganization, etc.); a different classification axis than commerce-stack role

**Faceted classification**

- [Faceted Classification — Wikipedia](https://en.wikipedia.org/wiki/Faceted_classification) — overview, orthogonality requirement, navigation across multiple hierarchical paths
- [Ranganathan and the Faceted Classification Theory](https://www.researchgate.net/publication/321840994_Ranganathan_and_the_faceted_classification_theory) — Colon Classification (1933), the PMEST facet framework, and the foundational principle that facets be independent of one another (ResearchGate; human-accessible, crawler-blocked)

**Agentic commerce protocols**

- [Google Universal Commerce Protocol (UCP)](https://developers.google.com/merchant/ucp) — open standard for turning AI-surface interactions into purchases; actor model (merchant, consumer, credential provider, payment service); live on AI Mode in Google Search and Gemini; interoperability with AP2 / A2A / MCP
- [UCP Core Concepts](https://ucp.dev/documentation/core-concepts/) — canonical specification; roles defined by "direction of capability flow, not by industry vertical"
- [Agentic Commerce Protocol (ACP) — OpenAI + Stripe](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol) — protocol and API spec for transactions between businesses, AI agents, and payment providers; 3–4 transactional actors; not a role taxonomy
- [Commerce Operations Foundation — Introducing the Order Network eXchange (ONX)](https://commerceopsfoundation.org/the-universal-language-for-modern-commerce-introducing-the-order-network-exchange-onx/) — open standard for post-purchase operational data exchange (orders, products, inventory, shipments, returns); vocabulary layer on MCP; 52 founding members / >$1T GMV; explicitly not a company classification system

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
