---
name: gbt11-standard-review
description: Hard-review and revise Chinese standard drafts against GB/T 1.1—2020 and the local 标准文本审查工作手册. Use when the user asks to 审查/硬审/逐项对照/修改/润色/完善 国家标准、行业标准、地方标准、团体标准、标准草案、编制说明、征求意见稿、送审稿、报批稿, especially with phrases like “按 GB/T 1.1”, “标准文本审查工作手册”, “标准起草规则”, “标准草案模板”, “帮我改成规范标准文本”, or “政府/正式标准文件要严谨”.
---

# GB/T 1.1 Standard Review

## Core Reference

Before reviewing or revising a standard text, read the local reference when available:

- `references/GB_T_1_1_2020_标准文本审查工作手册.md`

Use it as the working checklist. If the user's workspace contains a newer review handbook or template, prefer the user-provided file and cite that assumption in the work notes.

## Operating Mode

Treat the task as a formal standardization review, not ordinary polishing. Default to implementing revisions when the user provides editable files. Preserve user content that is technically correct; change structure, wording, numbering, and formatting only to improve compliance, clarity, consistency, and formal style.

For `.docx` or Word deliverables, also use the `documents` skill workflow: preserve or apply the supplied template, edit a copy, render/export for visual QA when possible, inspect page images/PDF, and iterate before delivery.

## Intake

Collect and identify these inputs:

1. Draft standard text or related formal document.
2. Applicable template, if provided.
3. Project proposal, approval form, prior drafts, expert comments, or teacher comments.
4. The target stage: 草案、征求意见稿、送审稿、报批稿, or 编制说明.
5. The file category: 国家标准、行业标准、地方标准、团体标准, or association/internal template.

If plan numbers, approval dates, standard numbers, or publication dates are unknown, do not invent them. Use cautious wording such as “以正式立项文件为准” only where appropriate, or leave template placeholders if the user explicitly needs blanks.

## Review Workflow

### 1. Classify The Document

Decide and record the working classification:

- Standardization object: product/system, process, service, terminology, symbol, classification, test, evaluation method, procedure, or guideline.
- Intended users: drafting bodies, evaluation institutions, testing bodies, regulators, producers, service providers, researchers, public users, etc.
- Purpose: mutual understanding, quality/usefulness, compatibility, safety, environmental protection, resource use, technical exchange, implementation evaluation, or management support.
- Functional type: 术语、符号、分类、试验、规范、规程、指南, or a method/procedure hybrid.

Then check whether title, scope, core technical elements, and modal verbs match that functional type.

### 2. Hard-Review Structure

Audit the element order and necessity:

- Cover, foreword, scope, normative references, terms and definitions, and core technical elements are critical.
- Normative references are required as an element; if none, state “本文件没有规范性引用文件。”
- Terms and definitions are a foundational element; if none, state “本文件没有需要界定的术语和定义。” unless the applicable association template explicitly omits it.
- Place optional elements in GB/T 1.1 order: preface/foreword, introduction, scope, normative references, terms, symbols, general principles/requirements, core technical elements, annexes, references, index.
- Ensure chapter numbering starts at “范围” as chapter 1 and runs continuously before annexes.
- Remove hanging paragraphs between a chapter title and first subclause unless allowed introductory text is necessary.
- Ensure same-level clauses are consistently titled or untitled.

### 3. Review Each Element

Apply these element-level checks:

- **Title**: concise, distinguishes the document, avoids unnecessary “标准/国家标准/行业标准” wording, and reflects the functional type when needed.
- **Foreword**: no requirements, recommendations, figures, tables, or formulas; includes GB/T 1.1 drafting statement, patent note if applicable, proposer, jurisdiction, drafting units, drafters, and version history as required by template.
- **Introduction**: explains background and rationale; contains no requirement clauses.
- **Scope**: factual, concise, no requirements/recommendations/instructions; states what the file规定/确立/描述/给出/界定 and what it applies to or excludes.
- **Normative references**: include only indispensable normative documents; do not normatively cite laws, administrative regulations, policy documents, replaced/obsolete documents, or inaccessible documents.
- **Terms and definitions**: include only necessary terms used at least twice and likely to be misunderstood; definitions use declarative language, not requirements.
- **Core technical elements**: match the functional type. Requirements must be verifiable; procedures need actionable steps and traceability; guidelines use recommendations and considerations rather than mandatory rules.
- **Annexes**: identify normative vs informative correctly; ensure body references match annex nature; annexes do not contain their own “范围/规范性引用文件/术语和定义”.
- **References**: list informative citations after annexes and separate them from normative references.

### 4. Review Clause Language

Enforce GB/T 1.1 modal-verb discipline:

- Requirements: “应/不应”.
- Recommendations: “宜/不宜”.
- Permissions: “可/不必”.
- Capability: “能/不能”.
- Possibility: “可能/不可能”.
- General statements: declarative wording such as “是、为、由、给出”.

Fix common errors:

- Replace “必须” with “应” unless referring to an external legal obligation.
- Replace “不得、禁止、不可” with “不应” in standard clauses.
- Do not use “可” for capability or possibility.
- Avoid “应尽可能、应避免、原则上应、通常应”; convert to verifiable requirements or recommendations.
- Use “符合” for objects/processes/services meeting requirements; use “遵守” for persons or organizations taking action.
- Rewrite vague requirements such as “应合理、应充分、应便捷、应有效” into objective and verifiable wording.

### 5. Review References, Tables, Figures, Formulas, Notes

Check these details explicitly:

- Use “本文件” to refer to the document itself.
- Refer to clauses, tables, figures, formulas, and annexes by number, not by page or “上文/下文”.
- Use “见” for informative cross-references.
- Ensure every figure/table is introduced in the text with clear clause force.
- Number tables and figures continuously in the body; restart as 表 A.1/图 A.1 in annexes.
- Avoid split tables, nested tables, slash-separated table headings, “同上/同左”, and unexplained blank cells.
- Use formulas only when clearer than prose; define all symbols after formulas and avoid descriptive words inside formulas.
- Ensure notes and examples contain only additional information, not hidden requirements or recommendations.

### 6. Edit The Draft

When revising, prefer direct, formal Chinese standard language:

- Keep sentences short and unambiguous.
- Use “本文件规定了……”“本文件适用于……”“……应……”“……宜……”“……可……” patterns appropriately.
- Remove background, policy explanation, and argumentative prose from normative chapters; move necessary background to introduction or compilation explanation.
- Move evaluation objects, application boundaries, and exclusions into scope where appropriate.
- Put methods, procedures, scoring, reporting, and data collection in logical implementation order.
- Put detailed examples, lists, scoring tables, templates, and report styles into informative annexes unless they are essential normative requirements.
- Preserve technically necessary content from project materials, but do not overclaim beyond evidence or approval documents.

## Output Expectations

For review-only requests, lead with findings:

1. A/B/C severity classification.
2. Location: chapter, clause, table, annex, or exact text.
3. Problem.
4. GB/T 1.1 or handbook basis.
5. Impact.
6. Suggested replacement or action.

For modification requests, deliver:

1. Revised Word file or Markdown/text draft as requested.
2. A concise change summary by user comment or by document part.
3. A remaining-risk list, including any unknown official data such as plan number, standard number, dates, or approval wording.
4. Verification notes: placeholder scan, modal-verb scan, structure check, and rendering/PDF check if a Word file was produced.

For high-stakes formal drafts, iterate until the document is internally consistent and template-compliant enough to send to a teacher, standards committee, or government-facing reviewer.

## Quality Gate

Before final delivery, check:

- No leftover placeholders unless intentionally retained.
- No invented official numbers or dates.
- Title, scope, chapter structure, annex order, and references are mutually consistent.
- Modal verbs match clause types.
- Normative references and informative references are separated.
- Terminology is necessary and consistently used.
- Tables/annexes are cited and numbered correctly.
- The final file opens and renders cleanly when rendering tools are available.
