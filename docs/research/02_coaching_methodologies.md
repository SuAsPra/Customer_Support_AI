# Research Summary: Coaching Methodologies

## Definitions
- **Coaching (customer support)**: structured guidance to improve an agent's communication, problem-solving, and adherence to policy and process.
- **Real-time coaching**: in-the-moment prompts or suggestions delivered during a live interaction to influence the next response.
- **Micro-coaching**: short, focused feedback targeting a specific behavior or moment rather than broad critique.
- **Actionable feedback**: feedback that is specific, explains impact, and clearly states what to do differently.

## Important Terminologies
- **Empathy**: recognizing and acknowledging the customer's feelings and situation.
- **Tone**: the emotional quality conveyed in writing (calm, respectful, reassuring, confident).
- **Clarity**: how easily the customer can understand the message (plain language, structure, explicit steps/timelines).
- **Ownership**: taking responsibility for helping resolve the issue ("I can help with this") rather than deflecting.
- **Accuracy**: correctness of information based on product details, policies, and the knowledge base.
- **De-escalation**: techniques used to reduce frustration/anger and prevent escalation.
- **GROW model**: Goal, Reality, Options, Will — a framework for structuring coaching conversations/guidance.

## Explanations
### What good agent communication looks like
- **Empathy**: acknowledge feelings and impact sincerely without being dismissive.
- **Clarity**: use plain language, organize information, confirm understanding, and provide concrete next steps and timelines.
- **Ownership**: commit to helping, set expectations, and follow through.
- **Accuracy**: verify details and align with KB/policy; avoid guessing.
- **Appropriate tone**: professional and adapted to context—reassuring for upset customers, concise and precise for technical issues.

### How feedback is framed to be actionable
- **Specific and observable**: reference concrete behaviors or phrases.
- **Timely**: real-time cues can prevent escalation; post-interaction reviews reinforce learning.
- **Balanced**: highlight strengths and improvements.
- **Behavior–Impact–Alternative**: describe what happened, why it mattered, and what to do instead.
- **Prioritized**: focus on 1–3 high-impact changes.
- **Measurable where possible**: connect to outcomes (reduced frustration, faster resolution, adherence).

### Relevant coaching approaches
- **Micro-coaching** for in-the-moment tips; **GROW-style prompts** to structure options and next actions; **positive reinforcement** to encourage effective behaviors.

## Real-World Examples
- **Empathy + ownership**: "I'm sorry you were charged twice—that's understandably frustrating. I can check this now and help you get it resolved."
- **Clarity with timeline**: "I've submitted the refund. It will reach your original payment method in 5–7 business days; your reference ID is 12345."
- **Actionable feedback**: "When the customer reported a duplicate charge, acknowledging the impact before asking for verification details would likely reduce frustration and escalation risk."

## How This Applies to Our Project
- The **Coaching & Response Suggestion Agent** generates a suggested reply, alternative replies, and scores for **tone/clarity/empathy**, plus concise, prioritized tips and risk flags.
- The **Real-time coaching feed (UI, Milestone 3)** presents micro-coaching per turn so agents can adjust immediately.
- The **Escalation Risk Monitor Agent** recommends de-escalation actions grounded in ownership, empathy, and clear options/timelines.
- The **Post-Interaction Summary Agent** provides a balanced, actionable report (strengths, improvements, personalized coaching) and sentiment journey to support post-session learning.
- Using **structured JSON outputs** for scores/tips/replies ensures coaching is consistent, explainable, and easy to display and store.
