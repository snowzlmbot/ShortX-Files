# ShortX Agent Skill

This repository contains the portable `shortx-rule-creator` Agent Skill. It
turns a natural-language Android automation request into a ShortX-importable
`.txt` file.

## Layout

```text
skills/shortx-rule-creator/
├── SKILL.md
└── references/
    ├── actions.md
    ├── advanced.md
    ├── conditions.md
    ├── examples.md
    ├── triggers.md
    └── variables.md
```

The skill package is intentionally runtime-neutral. Agents that implement the
Agent Skills convention can load the directory as-is; agents with a
platform-specific skill directory can copy the complete directory into that
location without changing its internal relative paths.

Examples of common project-local locations are:

- `.agents/skills/shortx-rule-creator/`
- `.claude/skills/shortx-rule-creator/`
- `.cursor/skills/shortx-rule-creator/`
- `.gemini/skills/shortx-rule-creator/`
- `.opencode/skills/shortx-rule-creator/`

Use the location documented by the active agent. Do not install the same
skill under multiple locations unless that agent explicitly requires it.

## Source and adaptation

- Source repository: <https://github.com/ShortX-Repo/ShortX-Files>
- Source skill: `skills/SKILL.md`
- Source revision imported: `e9895632c22034ee430bdb2d6507f1aca4e79fc5`
- Adapted package: `skills/shortx-rule-creator/`
- License: no license declaration was found in the inspected source; verify
  licensing before redistributing outside this repository.

The adaptation keeps the ShortX schema references and adds a portable
Agent-Skills workflow, relative-reference rules, deterministic artifact
validation, cross-agent tool mapping, and explicit non-execution/safety
boundaries. It does not execute generated Shell, JavaScript, MVEL, network, or
Android actions.

## Local installation in Hermes

The adapted package is already installed for the active Hermes profile when
this repository is prepared by the project workflow. For a manual install,
copy the complete directory into the profile's local-skill directory:

```bash
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/skills"
cp -a skills/shortx-rule-creator "${HERMES_HOME:-$HOME/.hermes}/skills/shortx-rule-creator"
```

The observed Hermes CLI accepts registry or HTTP identifiers for
`hermes skills install`; it does not treat a local directory as a supported
install identifier. For that reason, local profile installation uses the
copy above, followed by a fresh profile read-back:

```bash
hermes skills list --source local --enabled-only
hermes config check
```

For a project-local install, copy the same directory to the active agent's
supported project skill directory (for example `.agents/skills/`) and follow
that agent's trust or enablement step. A loader that caches skills may require
a new agent session before the skill is available in prompts.

## ShortX AI instructions

The AI-specific import files are documented in [`AI-SHORTX-使用说明.md`](../AI-SHORTX-使用说明.md):

- `da/ShortX-AI首次初始化与密钥设置.txt`
- `da/ShortX-AI回合制会话与模型切换.txt`
- `rule/ShortX-AI回合制会话自动指令.txt`

The package supports a single active provider/model configuration, provider-specific
secret global variables, round-based text interaction, and the documented OpenAI
Responses, OpenAI-compatible Chat, and Anthropic Messages request branches. The
README also records the capabilities that ShortX's published action schema does not
currently expose, including true streaming, recursive skills-directory fetching,
and application-layer encryption.

## Scope

This skill validates the structure of generated files. It does not prove that
a rule works on a particular Android device, ROM, ShortX version, permission
set, or root environment.
