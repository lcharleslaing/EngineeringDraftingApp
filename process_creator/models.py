from django.db import models


class Process(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    summary = models.TextField(blank=True, help_text="Generated summary of the process")
    summary_instructions = models.TextField(
        blank=True,
        default="You are given a list of steps, bullet points, or fragmented notes. Your task is to transform them into a single professional, coherent paragraph. Do not repeat the steps as a list. Instead, weave them into smooth, natural prose that reads as if written by a skilled professional writer. Maintain accuracy, logical flow, and clarity. The output must always be a polished paragraph summary, never a bullet list.",
        help_text="Instructions for summary generation"
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    analysis = models.TextField(blank=True, help_text="Generated analysis and improvement suggestions")
    analysis_instructions = models.TextField(
        blank=True, 
        default="You are a senior operations analyst. You will receive a business process as input (steps, notes, and context). Produce a professional report titled \"Training Analysis\" that managers and frontline staff can act on.\nFollow these rules:\n- Write clearly and concisely; avoid jargon. Use confident, direct language.\n- Do NOT restate the steps as bullets. Summarize the process in flowing prose.\n- Use Markdown headings exactly as specified below.\n- Give specific, actionable recommendations with clear benefits and effort levels.\n- Where details are missing, make reasonable assumptions and state them briefly.\n=== INPUT START ===\n{PASTE PROCESS STEPS / NOTES / CONTEXT HERE}\n=== INPUT END ===\n=== OUTPUT FORMAT (Markdown) ===\n# Training Analysis\n## Executive Summary\nA 4–6 sentence overview of the process, the primary objective, the current state, and the most important recommended changes and expected benefits.\n## Process Narrative (Plain-Language Summary)\n6–10 sentences that narrate how the process works from start to finish. Use paragraph form only (no bullets). Emphasize flow, handoffs, tools used, approvals, and timing.\n## Assumptions\n- 2–5 short bullets listing key assumptions you made due to missing information.\n## Strengths\n- 4–8 bullets. Each bullet: what works well + why it matters (impact on quality, speed, cost, compliance, safety, or CX).\n## Weaknesses\n- 4–8 bullets. Each bullet: the issue + consequence (e.g., rework, delays, risk, cost).\n## Improvement Opportunities — Current System (No new software)\nProvide 5–10 specific, low-friction changes using existing tools, roles, and policies. For each item, use this format in one bullet:\n- **[Title]** — What to change (1–2 sentences). **Benefit:** expected outcome with a measurable indicator (e.g., \"reduce cycle time by ~15%\"). **Effort:** Low/Med/High. **Owner:** role. **Risk/Mitigation:** brief.\n## Immediate Application-Level Enhancements (Quick to implement in an app/workflow)\nProvide 3–7 changes that can be implemented quickly via simple configuration, scripts, forms, validations, templates, or notifications. For each item, use the same format:\n- **[Title]** — What to implement (1–2 sentences). **Benefit:** measurable. **Effort:** Low/Med/High. **Owner:** role. **Risk/Mitigation:** brief.\n## Implementation Roadmap\nOrganize recommendations into phases with rationale:\n- **Now (0–30 days):** 3–6 highest-ROI, low-effort actions.\n- **Next (30–90 days):** 3–6 medium-effort actions that compound earlier gains.\n- **Later (90+ days):** 2–4 higher-effort changes that deliver strategic value.\n## Metrics & Monitoring\nList 4–8 KPIs with target direction and cadence. For each KPI: **Name**, **Target/Direction**, **Data Source**, **Review Cadence** (e.g., weekly), **Owner**.\n## Risks & Mitigations\n3–6 material risks across people/process/tech/compliance and how to mitigate each.\n## Final Recommendation\nA 4–6 sentence closing paragraph summarizing the case for change, expected benefits, and the immediate next steps.\n=== STYLE GUARDRAILS ===\n- Professional tone. Tight sentences. No filler, no hype.\n- Use paragraph form for the narrative sections; bullets only where specified.\n- Quantify benefits or ranges when plausible. Avoid vague claims.\n- Do not include meta-commentary or instructions in the output.",
        help_text="Instructions for process analysis"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_ai_update = models.DateTimeField(null=True, blank=True, help_text="Last time summary or analysis was updated")

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Step(models.Model):
    process = models.ForeignKey(Process, related_name="steps", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("process", "order")

    def __str__(self) -> str:
        return f"{self.order}. {self.title}"


class StepImage(models.Model):
    step = models.ForeignKey(Step, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="process_screenshots/")
    order = models.PositiveIntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]


class AIInteraction(models.Model):
    INTERACTION_TYPES = [
        ('summary', 'Summary Generation'),
        ('analysis', 'Process Analysis'),
        ('custom', 'Custom Analysis'),
    ]
    
    process = models.ForeignKey(Process, related_name="ai_interactions", on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    prompt_sent = models.TextField(help_text="The prompt/instructions sent")
    response_received = models.TextField(help_text="The response received")
    tokens_used = models.PositiveIntegerField(null=True, blank=True, help_text="Number of tokens used")
    cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="Cost of this interaction")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.process.name} - {self.get_interaction_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# Create your models here.
