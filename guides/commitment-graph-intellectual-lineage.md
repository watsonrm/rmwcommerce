# The Intellectual Lineage of the Commitment Graph

**A directed, event-sourced ledger of "who owes whom what" traces its ancestry through six fields — and reveals why the LLM is the missing organ every previous attempt lacked.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- A commitment graph — a typed ledger of directed obligations, each with a bearer, a counterparty, a state machine, and verifiable evidence for closure — draws on at least six distinct research fields developed since 1951.
- Every individual layer has a formal ancestor. The new thing is realizing the full stack as an LLM-driven agent memory with a human confidence gate on ambiguous inferences.
- The sharpest punchline: Winograd and Flores had essentially the right theory in 1986, but their implementation (The Coordinator) failed because it had to *demand* structured speech acts. A large language model can *observe* commitments in natural messages instead. "Expect a shape, don't demand it" is both the epitaph on that failure and the thesis of the fix.
- The dedup keystone is record linkage applied to obligations: a renegotiated commitment is one superseded edge, not three new ones.

### Where to spend your time, in priority order

| # | Source | Why it matters | Effort |
|---|---|---|---|
| 1 | Singh (1999), "An ontology for commitments in multiagent systems," *Artificial Intelligence and Law* 7:97–113 | Defines C(x, y, r, u) — the debtor, creditor, antecedent, consequent form — and the full commitment lifecycle: created → detached → discharged / violated / cancelled / released. The nearest formal ancestor of the obligation edge. | Medium — short paper, dense formalism |
| 2 | Chopra & Singh (2015), "Cupid: Commitments in Relational Algebra," AAAI 2015, pp. 2052–2059 | Formalizes computing commitment state from an event log using relational algebra. The algebraic form of what a reconciliation pipeline does when it derives obligation state from observed evidence. | High — requires relational-algebra background |
| 3 | McCarthy (1982), "The REA Accounting Model," *The Accounting Review* 57(3):554–578 | REA made Commitment a typed first-class entity linking Agents to future Economic Events — the structural insight the graph inherits. | Low — short, clear |
| 4 | Medina-Mora, Winograd, Flores et al. (1992), "The Action Workflow Approach," ACM CSCW 1992 | The request→promise→performance→acceptance loop. The extraction event-kind vocabulary (request / promise / deliver / ack) maps almost directly from this paper. | Low — practical, readable |
| 5 | Winograd & Flores (1986), *Understanding Computers and Cognition*, Ablex | The Language/Action Perspective grounding and The Coordinator story. Essential context for understanding why "expect a shape, don't demand it" is the right design principle. | Medium — book-length |
| 6 | Herrestad & Krogh (1995), "Obligations directed from bearers to counterparties," ICAIL 1995 | The formal logic behind the directed obligor → obligee edge: i O j, where i is the bearer and j the counterparty. | Medium — logic-heavy |
| 7 | Fellegi & Sunter (1969), "A Theory for Record Linkage," *JASA* 64:1183–1210 | The statistical decision model behind the match-or-create confidence gate that prevents the graph from over-counting renegotiated obligations. | Low — foundational, accessible |

Most readers interested in the AI-agent angle should start with Singh (1999) and Medina-Mora et al. (1992), then return to the others as the design rationale becomes relevant.

---

## The problem

Every AI agent that acts on behalf of a human across email, calls, and messages faces the same question: what was committed to, and to whom?

The informal answer — a to-do list, a summary in the agent's scratchpad, a vector store of "next steps" extracted from transcripts — fails in production for three consistent reasons.

**Duplication.** The same obligation, mentioned in a Monday call, a Thursday email, and a Friday Slack thread, is extracted three times and counted as three open items. A renegotiated deliverable (scope and price changing across three conversations) becomes three independent commitments rather than one superseded edge.

**False closure.** An agent marks a commitment closed because the outbound message was sent, not because the deliverable was confirmed received and accepted. Sending is not fulfilling.

**Fabricated counterparty obligations.** An agent infers "they owe us something" from a unilateral courtesy send — "FYI, attaching the draft for your reference" — rather than from mutual agreement or a genuine request they accepted. A later send is evidence that advances an already-agreed commitment; it is not what creates the commitment.

The pattern that solves all three has the same shape regardless of implementation: a typed, directed, identity-bearing obligation edge (obligor → obligee), opened by a mutual agreement or genuine speech act, closed only on verifiable evidence, and resolved against prior observations rather than blindly created anew. When the same obligation is seen again, it is matched; when renegotiated, it is superseded; when unclear, it is held for human review.

That pattern is not new. It has been independently discovered — with varying degrees of completeness — in at least six research fields over seven decades. The agent-memory realization via LLM extraction is new. The obligation graph itself is old.

---

## The deep roots

### Speech Act Theory: the original taxonomy of obligations

Austin's *How to Do Things with Words* ([Clarendon Press / Harvard University Press, 1962](https://archive.org/details/intentionplanspr0000brat)) established that language is not merely descriptive but performative — that saying "I promise" *is* promising, not a report of an inner state. His analysis of felicity conditions (what makes a performative succeed or misfire) is the first systematic treatment of what must be true for a speech act to create an obligation.

Searle refined and taxonomized this in *Speech Acts* (Cambridge University Press, 1969) and, more precisely, in "A Taxonomy of Illocutionary Acts" ([*Language, Mind, and Knowledge*, University of Minnesota Press, 1975, pp. 344–369](https://conservancy.umn.edu/items/2b9aa876-a427-4f47-8640-74c20f583c86)). His five categories are assertives, directives, commissives, expressives, and declarations. Of these, two matter most for obligation tracking: a **commissive** is a promise — a self-imposed future obligation; a **directive** is a request — an attempt to get the hearer to act. These two categories cover most of what an obligation graph is listening for.

The extraction stage of a commitment pipeline is, in Searle's terms, a classifier over illocutionary acts, gated on whether the felicity conditions for obligation are met in context. That framing is from 1975.

### Language/Action Perspective and The Coordinator

Winograd and Flores brought speech act theory into computer science in *Understanding Computers and Cognition* ([Ablex Publishing Corp., Norwood, NJ, 1986](https://dl.acm.org/doi/book/10.5555/5245)). Their Language/Action Perspective held that work coordination is constituted by linguistic acts — requests, promises, reports, and acknowledgments — rather than by information transfer. An information system, on this view, should model the speech acts, not just the data that flows through them.

Their implementation was **The Coordinator**: workflow software that required users to explicitly tag every message with its speech-act type (request, promise, decline, counter-offer, and so on). The theory was sound. The system failed commercially. Users found the tagging burden artificial and coercive; the software felt like a straitjacket imposed on natural communication rather than support for it.

The direct successor was **Action Workflow**, described in "The Action Workflow Approach to Workflow Management Technology" by Medina-Mora, Winograd, Flores, and Flores ([Proc. ACM CSCW 1992, Toronto, pp. 281–288](https://dl.acm.org/doi/10.1145/143457.143530)). Action Workflow formalized the coordination loop as four phases: **Request → Promise → Performance → Acceptance**. A customer initiates with a request; a performer commits with a promise; the performer executes; the customer acknowledges satisfaction. This four-phase loop is the direct ancestor of the extraction event kinds (request / promise / deliver / ack) in a commitment pipeline. The vocabulary maps almost directly.

Jan Dietz's DEMO (Design & Engineering Methodology for Organizations) and his *Enterprise Ontology* (Springer, 2006) represent a parallel formalization: a transaction actor model with initiator and executor roles and a structured communication pattern around agreeing to, executing, and accepting work. DEMO's transaction states (REQUESTED, PROMISED, STATED, ACCEPTED) mirror the Action Workflow phases closely.

The three — Winograd & Flores, Action Workflow, DEMO — share the same core insight: the commitment lifecycle has a well-defined structure; what varies is how strictly you demand that structure from users. The Coordinator demanded it. Action Workflow modeled it loosely for system designers. DEMO formalized it for enterprise architects. None of them could observe it without asking.

### Directed obligation: the deontic logic lineage

Von Wright's "Deontic Logic" ([*Mind*, vol. LX, no. 237, 1951, pp. 1–15](https://academic.oup.com/mind/article-abstract/LX/237/1/941536)) introduced the systematic formal treatment of obligation (O), permission (P), and prohibition (F) in modal-logic terms. This was the foundation of normative reasoning in formal logic.

The standard deontic logic treats obligations as unary: "it ought to be the case that p." The problem for a commitment graph is that obligations are directed: it is not just that X ought to deliver the document, but that X owes the delivery *to Y*. Von Wright's initial logic had no formal way to express the counterparty.

Kanger's "New Foundations for Ethical Theory" (1957; republished in *Deontic Logic: Introductory and Systematic Readings*, Reidel, 1971) developed the relational treatment of normative positions — obligations that involve both a bearer and a counterparty. This line reached its clearest formulation for computing purposes in Herrestad and Krogh's "Obligations directed from bearers to counterparties" ([Proc. 5th International Conference on Artificial Intelligence and Law, ICAIL 1995](https://link.springer.com/chapter/10.1007/3-540-45941-3_10)), which introduced the operator **i O j** — "i has an obligation toward j" — with explicit bearer and counterparty indices. This is the formal logic behind the directed obligor → obligee edge.

### REA: Commitment as a first-class accounting entity

McCarthy's "The REA Accounting Model: A Generalized Framework for Accounting Systems in a Shared Data Environment" ([*The Accounting Review*, vol. 57, no. 3, July 1982, pp. 554–578](https://www.researchgate.net/publication/239064746_The_REA_Accounting_Model_A_Generalized_Framework_for_Accounting_Systems_Shared_Data_Environment)) is an underappreciated ancestor from accounting information systems. REA models a business in terms of three primitives: **Resources** (what is exchanged), **Events** (the exchanges themselves), and **Agents** (who participates). The result is a typed graph of economic activity.

Geerts and McCarthy extended REA in "An ontological analysis of the economic primitives of the extended-REA enterprise information architecture" ([*International Journal of Accounting Information Systems*, vol. 3, 2002, pp. 1–16](https://www.sciencedirect.com/science/article/abs/pii/S1467089501000203)) by adding a **Commitment** entity: a forward-looking promise to participate in a future Economic Event. A Commitment in extended REA links two Agents to a future Resource exchange, giving it identity, a counterparty, a substance (the resource or service promised), and a due relationship to the anticipated event. This is structurally very close to an obligation edge in a commitment graph — and it appeared in an accounting standard, not an AI paper.

ISO/IEC 15944-4 ([2007, "Information technology — Business Operational View — Part 4: Business transaction scenarios — Accounting and economic ontology"](https://www.iso.org/standard/40348.html)) codified the REA model — including the Commitment entity — in a formal international standard for open-edi business transactions, as part of the UN/CEFACT modeling framework. The standard describes a business transaction state machine moving through planning, negotiation, commitment, and fulfillment phases.

### Declarative workflow: expect a shape, don't demand it

Traditional process modeling (BPMN, flowcharts) defines exactly what must happen and in what order — a closed model that admits only specified sequences. This is the Coordinator problem restated: the model is the specification, and deviations are failures.

DECLARE, introduced by Pesic and van der Aalst in "A Declarative Approach for Flexible Business Processes Management" ([Proc. BPM 2006 Workshops](https://www.vdaalst.com/publications/p419.pdf)), inverted this. A DECLARE model specifies *constraints* — things that must not happen, or must happen before other things — rather than a prescribed flow. Anything the constraints permit is valid. The model is open, not closed. Van der Aalst's broader Adaptive Case Management framework applies the same principle to complex, variable-path work.

The mapping to a commitment graph is direct: a template is a DECLARE-style prior, a set of anticipated obligations with dependencies. The template says "expect this shape" without demanding it. When reality diverges — a deliverable loop that was expected to close in two weeks takes six, or a new workstream opens mid-engagement — the observation overrides the prior, and the divergence is flagged. The system follows the actual obligation graph, not the anticipated one.

### Event sourcing and record linkage: the engineering substrate

Two ideas from software engineering and statistics supply the implementation layer.

Fowler's 2005 article "Event Sourcing" ([martinfowler.com, December 2005](https://martinfowler.com/eaaDev/EventSourcing.html)) and Young's foundational CQRS work ([CodeBetter.com, February 2010](http://codebetter.com/gregyoung/2010/02/13/cqrs-and-event-sourcing/)) establish the pattern: application state is a fold over an append-only log of events. You do not store the current state directly; you derive it from the event history. A commitment graph follows this exactly: the current set of obligation edges and their states is the fold over the event log of speech acts, edits, and evidence. Newer events win on conflict (last-writer-wins by event timestamp, not ingest timestamp — an important distinction when sources arrive out of order).

Fellegi and Sunter's "A Theory for Record Linkage" ([*Journal of the American Statistical Association*, vol. 64, 1969, pp. 1183–1210](https://www2.stat.duke.edu/~rcs46/linkage/presentations/01-baiLi_FelleigSunter1969.pdf)) is the statistical foundation for the dedup gate. A new observation of an obligation — "they mentioned the deliverable again in today's call" — must be matched against existing commitment records rather than creating a new one. Fellegi and Sunter's decision model (link / possibly link / not link, based on likelihood ratios on field agreement) is exactly what the match-or-create gate does at the commitment level: match on (container, obligor, obligee, substance-approximation, due) with a human gate above the ambiguous-match threshold.

---

## The AI and multi-agent lineage

### Social commitments: Singh's formalization

While the fields above were developing their accounts, the multi-agent systems community arrived at a closely parallel formulation independently.

Castelfranchi's "Commitments: From individual intentions to groups and organizations" (Proc. ICMAS 1995) argued that social structures must be modeled by commitments external to any individual agent — not by internal mental states but by interagent obligations. This was a direct challenge to the dominant BDI model (discussed below), which treated commitment as a private mental state rather than a social fact between agents.

Singh carried this to a formal ontology in "An ontology for commitments in multiagent systems: Toward a unification of normative concepts" ([*Artificial Intelligence and Law*, vol. 7, 1999, pp. 97–113](https://link.springer.com/article/10.1023/A:1008319631231)). Singh's formalism is:

**C(x, y, r, u)**: agent x (the debtor) commits to agent y (the creditor) that if r (the antecedent) holds, x will bring about u (the consequent).

The lifecycle states: a commitment is **created**, then **detached** when its antecedent fires (making it unconditional), then **discharged** when fulfilled, or **violated** (antecedent fired, consequent not achieved by deadline), or **cancelled** (debtor withdraws), or **released** (creditor releases the debtor).

The correspondence to a commitment graph's obligation edge is close enough to be startling. The obligor is Singh's debtor; the obligee is the creditor; the substance and due date map to the consequent and its deadline; the state machine is directly analogous. Singh assumed agents would announce commitment operations via explicit protocol messages. He did not have LLM extraction. But the formal structure he defined is the right structure.

### Commitment machines and protocols

Yolum and Singh operationalized this in "Commitment Machines" ([Proc. ATAL 2001, Springer 2002, pp. 235–247](https://link.springer.com/chapter/10.1007/3-540-45448-9_17)): a protocol specification language in which agents interact by making, cancelling, releasing, and discharging commitments. The commitment machine monitors protocol conformance by tracking commitment states, not message sequences. This is the key conceptual step: compliance is about obligation lifecycle, not about sending the right messages in the right order.

Fornara and Colombetti extended this in "Operational specification of a commitment-based agent communication language" ([Proc. AAMAS 2002, ACM Press, pp. 535–542](https://dl.acm.org/doi/10.1145/860575.860659)), defining a language for commitment-based agent communication with explicit operational semantics for creation, discharge, violation, and cancellation.

### Computing commitment state from an event log: Cupid

Chopra and Singh's "Cupid: Commitments in Relational Algebra" ([Proc. AAAI 2015, pp. 2052–2059](https://ojs.aaai.org/index.php/AAAI/article/view/9443)) takes the final formal step. Cupid specifies commitments as first-order queries over an event database schema. Given an event log — a record of what happened, in the form of timestamped events — Cupid computes the current state of each commitment instance using relational algebra. Violated, discharged, detached, and so on are all derived from the log, not stored as mutable state.

This is precisely what the reconciliation stage of a commitment pipeline does: given the event log of speech acts and evidence artifacts, derive the current obligation state for each edge. Cupid's formalization validates the architecture: event-sourced state, queried relationally, with lifecycle semantics defined over event patterns. Chopra and Singh proved this structure works; they just had structured protocol events rather than LLM-extracted speech acts from natural language.

### BDI agents: the contrast

The Belief-Desire-Intention model — Bratman's philosophical account (*Intention, Plans, and Practical Reason*, [Harvard University Press, 1987](https://archive.org/details/intentionplanspr0000brat)) formalized for software agents by Rao and Georgeff ("Modelling rational agents within a BDI-architecture," [Proc. KR-91, Morgan Kaufmann, 1991](https://www.semanticscholar.org/paper/Modeling-Rational-Agents-within-a-BDI-Architecture-Rao-Georgeff/a5eafb6c265e53da2a05606598a0d3480fca11af)) — treats commitment as an agent's *internal* intention: what it has committed itself to doing, as a mental state.

The distinction from social commitment is structural, not terminological. A BDI agent has commitments in the sense of plans it has adopted and intends to execute. A social commitment (Singh's formulation) is a directed obligation between two agents, with a creditor who can demand fulfillment and recognize a violation — an external, interagent fact, not an internal mental state. The commitment graph uses the social commitment concept. An agent's internal plans are irrelevant to whether its obligation to another party exists, and vice versa.

### The Contract Net Protocol: task distribution without obligation tracking

Smith's "The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver" ([*IEEE Transactions on Computers*, vol. 29, 1980, pp. 1104–1113](https://www.reidgsmith.com/The_Contract_Net_Protocol_Dec-1980.pdf)) defined a distributed task-allocation mechanism via announcements, bids, and awards. This is a foundational multi-agent coordination mechanism — but it is not a commitment system in the sense used here. Once a task is awarded, the Contract Net does not track the obligation lifecycle, verify fulfillment, or handle renegotiation. It allocates. The commitment graph begins where the Contract Net leaves off.

---

## Why modern LLM-agent stacks don't do this

Contemporary agent frameworks provide vector-RAG memory, scratchpads, and structured task lists. These are useful, but they are not a typed obligation ledger with identity resolution. The distinctions matter in production:

A scratchpad stores what the agent remembers. A commitment graph stores what the agent *owes* and what is *owed to it*, with a named counterparty on each edge.

A RAG store retrieves by semantic similarity. An obligation ledger resolves by identity: is this new mention the same commitment as a prior one, a renegotiation of it, or something new? The answer changes whether the count is 1 or 3. Getting it wrong either inflates the apparent workload or loses track of real obligations.

A vector store has no state machine. An obligation has states: open (mutually agreed), provisionally open (template-anticipated, awaiting confirmation), closed on verified evidence, superseded on renegotiation, violated on missed deadline.

The closest modern analogs are bi-temporal knowledge-graph memory systems, which track when facts were recorded and when they were true. These handle the temporal dimension that commitment graphs also need — event-time vs. ingest-time — but they are entity-fact graphs, not obligation graphs with lifecycle semantics. Revenue-intelligence platforms that extract "commitments" from call transcripts are useful for sales teams but shallow by comparison: they produce text summaries rather than typed directed edges; they do not resolve identity across mentions; they lack a formal lifecycle; and they do not track counterparty obligations symmetrically.

---

## Where the model sits, and the punchline

Every layer of a commitment graph has a formal ancestor:

- The directed obligation edge: Herrestad & Krogh (1995), via von Wright (1951) and Kanger (1957).
- The Commitment entity as a first-class typed record: McCarthy (1982) and Geerts & McCarthy (2002).
- The lifecycle state machine (created / detached / discharged / violated / cancelled / released): Singh (1999).
- The request→promise→perform→accept extraction vocabulary: Medina-Mora, Winograd, Flores et al. (1992).
- The declarative prior — "expect a shape, don't demand it": Pesic & van der Aalst (2006).
- Computing obligation state from an event log: Cupid, Chopra & Singh (2015).
- The identity-resolution dedup gate: Fellegi & Sunter (1969) applied to obligation records.

The new synthesis is: all of the above, realized as a live running agent memory via LLM extraction from unstructured natural content — email, transcripts, Slack threads — with a human confidence gate at the ambiguous-match boundary.

And that brings the specific claim that earns a place in the intellectual history.

Winograd and Flores had essentially the right theory in 1986. The Language/Action Perspective correctly identified that coordination is constituted by speech acts, that the request→promise→perform→accept loop is the fundamental unit of organized work, and that information systems should model the commitments rather than just the data. Their implementation — The Coordinator — failed because it *demanded* structured tagging. Users had to explicitly classify every message as a request, a promise, or a counter-offer. The cognitive overhead was unacceptable; the rigidity was off-putting; the system was abandoned.

The unlock is natural-language understanding. A large language model can *observe* a commitment in natural text — "I'll get that to you by Thursday" in the middle of an email — without requiring the speaker to know they are creating a commitment record. The extraction is a classification task the model performs, not a tagging discipline the human must maintain. Templates provide anticipated shapes (priors) that the model reconciles against observed reality; when reality diverges, the prior yields. The confidence gate — human review for ambiguous matches and uncertain extractions — acknowledges that LLM classification is probabilistic, not deterministic.

"Expect a shape, don't demand it" is both the direct inversion of The Coordinator's design failure and the precise description of what LLM extraction enables.

Winograd and Flores were right about the theory. They were thirty-five years early on the infrastructure.

---

## Sources & Attribution

Primary sources, in the order they appear above.

**Speech Act Theory:**
- Austin, J.L. *How to Do Things with Words*. Clarendon Press / Harvard University Press, 1962.
- Searle, J.R. *Speech Acts: An Essay in the Philosophy of Language*. Cambridge University Press, 1969.
- Searle, J.R. "A Taxonomy of Illocutionary Acts." In *Language, Mind, and Knowledge* (Minneapolis Studies in the Philosophy of Science, vol. 7). University of Minnesota Press, 1975, pp. 344–369. [University of Minnesota Digital Conservancy](https://conservancy.umn.edu/items/2b9aa876-a427-4f47-8640-74c20f583c86).

**Language/Action Perspective:**
- Winograd, T. & Flores, F. *Understanding Computers and Cognition: A New Foundation for Design*. Ablex Publishing Corp., Norwood, NJ, 1986. [ACM Digital Library](https://dl.acm.org/doi/book/10.5555/5245).
- Medina-Mora, R., Winograd, T., Flores, R., & Flores, F. "The Action Workflow Approach to Workflow Management Technology." *Proc. ACM CSCW 1992*, Toronto, pp. 281–288. [ACM Digital Library](https://dl.acm.org/doi/10.1145/143457.143530).
- Dietz, J.L.G. *Enterprise Ontology: Theory and Methodology*. Springer, 2006.

**Deontic Logic and Directed Obligation:**
- von Wright, G.H. "Deontic Logic." *Mind*, vol. LX, no. 237, 1951, pp. 1–15. [Oxford Academic](https://academic.oup.com/mind/article-abstract/LX/237/1/941536).
- Kanger, S. "New Foundations for Ethical Theory." 1957; republished in *Deontic Logic: Introductory and Systematic Readings*, ed. Hilpinen. Reidel, 1971.
- Herrestad, H. & Krogh, C. "Obligations directed from bearers to counterparties." *Proc. 5th International Conference on Artificial Intelligence and Law (ICAIL 1995)*. [Springer](https://link.springer.com/chapter/10.1007/3-540-45941-3_10).

**REA Accounting Ontology:**
- McCarthy, W.E. "The REA Accounting Model: A Generalized Framework for Accounting Systems in a Shared Data Environment." *The Accounting Review*, vol. 57, no. 3, July 1982, pp. 554–578. [ResearchGate](https://www.researchgate.net/publication/239064746_The_REA_Accounting_Model_A_Generalized_Framework_for_Accounting_Systems_Shared_Data_Environment).
- Geerts, G. & McCarthy, W.E. "An ontological analysis of the economic primitives of the extended-REA enterprise information architecture." *International Journal of Accounting Information Systems*, vol. 3, 2002, pp. 1–16. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1467089501000203).
- ISO/IEC 15944-4:2007. "Information technology — Business Operational View — Part 4: Business transaction scenarios — Accounting and economic ontology." [ISO](https://www.iso.org/standard/40348.html).

**Declarative Workflow:**
- Pesic, M. & van der Aalst, W.M.P. "A Declarative Approach for Flexible Business Processes Management." *Proc. BPM 2006 Workshops*. [PDF](https://www.vdaalst.com/publications/p419.pdf).

**Event Sourcing and Record Linkage:**
- Fowler, M. "Event Sourcing." martinfowler.com, December 2005. [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html).
- Young, G. "CQRS and Event Sourcing." CodeBetter.com, February 13, 2010. [codebetter.com](http://codebetter.com/gregyoung/2010/02/13/cqrs-and-event-sourcing/).
- Fellegi, I.P. & Sunter, A.B. "A Theory for Record Linkage." *Journal of the American Statistical Association*, vol. 64, 1969, pp. 1183–1210. [Duke Statistics presentation](https://www2.stat.duke.edu/~rcs46/linkage/presentations/01-baiLi_FelleigSunter1969.pdf).

**Multi-Agent Systems:**
- Castelfranchi, C. "Commitments: From individual intentions to groups and organizations." *Proc. 1st International Conference on Multi-Agent Systems (ICMAS 1995)*.
- Singh, M.P. "An ontology for commitments in multiagent systems: Toward a unification of normative concepts." *Artificial Intelligence and Law*, vol. 7, 1999, pp. 97–113. [Springer](https://link.springer.com/article/10.1023/A:1008319631231).
- Yolum, P. & Singh, M.P. "Commitment Machines." *Proc. 8th International Workshop on Agent Theories, Architectures, and Languages (ATAL 2001)*, Springer, 2002, pp. 235–247. [Springer](https://link.springer.com/chapter/10.1007/3-540-45448-9_17).
- Fornara, N. & Colombetti, M. "Operational specification of a commitment-based agent communication language." *Proc. AAMAS 2002*, ACM Press, pp. 535–542. [ACM Digital Library](https://dl.acm.org/doi/10.1145/860575.860659).
- Chopra, A.K. & Singh, M.P. "Cupid: Commitments in Relational Algebra." *Proc. AAAI 2015*, pp. 2052–2059. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/9443).
- Bratman, M.E. *Intention, Plans, and Practical Reason*. Harvard University Press, 1987.
- Rao, A.S. & Georgeff, M.P. "Modelling rational agents within a BDI-architecture." *Proc. 2nd International Conference on Principles of Knowledge Representation and Reasoning (KR-91)*, Morgan Kaufmann, 1991.
- Smith, R.G. "The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver." *IEEE Transactions on Computers*, vol. 29, 1980, pp. 1104–1113. [reidgsmith.com](https://www.reidgsmith.com/The_Contract_Net_Protocol_Dec-1980.pdf).

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
