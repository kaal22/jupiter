\# product.md — Jupiter OS: Local Agentic Desktop Copilot (Phase 1)



\## Product Name

\*\*Jupiter OS\*\*



A privacy-centric, local-first AI companion built into a desktop Linux experience.



---



\## 1. Vision



Jupiter OS is a \*\*desktop operating system experience\*\* that ships with a local AI agent deeply integrated into:



\- system maintenance

\- user workflows

\- terminal assistance

\- everyday tasks (email, scheduling, planning)



All inference and memory stay \*\*fully local\*\* on the user’s machine, with user-controlled permissions and clear auditability.



---



\## 2. Target Users



\### Everyday

\- Desktop users seeking intelligent assistance

\- Non-technical users who want guidance and safety



\### Power

\- Developers and sysadmins who want deep AI-assisted CLI workflows



---



\## 3. Platform (Phase 1)



\*\*Base:\*\* Ubuntu Desktop LTS (24.04+)  

\*\*Goal:\*\* Provide Jupiter OS as a layered experience on standard Ubuntu installs with first-boot provisioning.



---



\## 4. Core Requirements



\### Must-have Phase 1

\- Local LLM execution (no cloud reliance)

\- First-boot provisioning on Ubuntu Desktop

\- Welcome Wizard explaining AI, privacy, and hardware prep

\- Automatic GPU detection and appropriate model selection

\- Agent CLI + local API

\- Terminal assistant and system tools

\- Long-term memory with consent

\- Safe, auditable actions



\### Must-not

\- Destructive actions without confirmation

\- Implicit data upload

\- Cloud inference by default



---



\## 5. Architecture



┌───────────────────────────────────────────┐

│ Welcome Wizard (GUI, one-time) │

├───────────────────────────────────────────┤

│ Local API (localhost only) │

├───────────────────────────────────────────┤

│ Jupiter Agent Daemon (executor + planner) │

├───────────────────────────────────────────┤

│ Tool Safety Broker │

├───────────────────────────────────────────┤

│ Local LLM Runtime (Ollama) │

├───────────────────────────────────────────┤

│ Memory \& Audit Storage (SQLite) │

├───────────────────────────────────────────┤

│ Ubuntu Desktop Base (GNOME, systemd) │

└───────────────────────────────────────────┘





---



\## 6. First-Boot Provisioning



\### Trigger

\- `jupiter-firstboot.service` (systemd)

\- Runs once on first login

\- Disables itself after provisioning



\### Steps

1\. \*\*Hardware detection\*\*

&nbsp;  - GPU VRAM, CPU, memory, drivers

2\. \*\*Install runtime\*\*

&nbsp;  - Ollama install and base config

3\. \*\*Model selection\*\*

&nbsp;  - Policy based on GPU/CPU

4\. \*\*DB init\*\*

&nbsp;  - Local SQLite

&nbsp;  - Store baseline snapshot

5\. \*\*Activate services\*\*

&nbsp;  - `jupiter-agent.service`

6\. \*\*Wizard completion\*\*

&nbsp;  - “Ready” state with usage hints



---



\## 7. Welcome Wizard (GUI)



\### Screens

\- \*\*Intro:\*\* explain AI \& local

\- \*\*Privacy \& Controls:\*\* user consent

\- \*\*Hardware Check:\*\* show GPU/CPU

\- \*\*Performance Settings:\*\* speed vs quality

\- \*\*Optional Connectors:\*\* e.g., IMAP

\- \*\*Progress:\*\* model download + config

\- \*\*Done:\*\* usage tips



---



\## 8. Local LLM Runtime



\- Uses \*\*Ollama\*\* locally with GPU fallback

\- Service binds to `localhost`

\- Model policy driven by hardware



---



\## 9. Model Selection Policy



\*\*VRAM-based mapping (example)\*\*

\- No GPU → 7B Q4 CPU

\- 4–6 GB VRAM → 3B–7B Q4

\- 8 GB → 7B Q4/Q5

\- 12 GB → 7B–13B Q4/Q5 (balanced)

\- 16 GB → 13B Q4/Q5  

\*(configurable via policy)\*



---



\## 10. Jupiter Agent



\### Responsibilities

\- Plan actions

\- Execute tools safely

\- Verify outputs

\- Long-term context

\- Local API + CLI



---



\## 11. Tools



\#### System

\- status/logs

\- basic diagnostics

\- safe installs (confirmed)



\#### Terminal

\- read-only explanations

\- restricted exec (confirmed)



\#### Extensions

\- email IMAP helper

\- calendar (optional)



---



\## 12. Safety \& Permissions



\- Scoped permissions (system.read/write, email.read/write)

\- Explicit confirmation flows

\- Audit logs captured locally



---



\## 13. Memory



\### Types

\- Session (ephemeral)

\- Episodic (summaries)

\- Explicit preferences



\### Rules

\- Ask before remembering

\- User can view/edit/remove



---



\## 14. Interfaces



\### CLI

\- `jupiter` command

\- interactive chat

\- plans and executions



\### Local API

\- only on `localhost`



\### GUI (Phase 1)

\- Welcome Wizard

\- Basic notifications



---



\## 15. Data \& Privacy



\- All data local

\- No remote inference by default

\- No telemetry



---



\## 16. Milestones



\*\*Phase 1\*\*

1\. Skeleton services

2\. First-boot wizard

3\. Model policy + runtime

4\. CLI + agent

5\. Basic tools + safety

6\. Memory store



---



\## 17. Success Criteria (v1)



\- Ubuntu Desktop install → AI provisioning

\- Appropriate local model selected

\- CLI usage available immediately

\- System actions safe \& logged

\- Memory features operational



---



\## 18. Legal \& Branding Notes



\- “Jupiter OS” name is available but requires \*\*proper trademark checks\*\* before commercial distribution. (Earlier use as codename in elementary OS 0.1 does exist historically.) :contentReference\[oaicite:3]{index=3}



---



\*\*End of product.md\*\*

