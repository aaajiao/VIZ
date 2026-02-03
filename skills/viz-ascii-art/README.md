# VIZ ASCII Art Skill

AgentSkills-compatible skill for VIZ - ASCII art visualization generator.

## What is this?

This skill teaches AI assistants (Claude, OpenClaw, etc.) how to use VIZ to generate emotion-driven ASCII art visualizations. When installed, AI can automatically:

1. Understand user requests for visualizations
2. Construct proper JSON input
3. Execute VIZ commands
4. Parse and present results

## Installation

### For OpenClaw / OpenCode

**Option 1: Workspace skill (project-specific)**

The skill is already in `skills/viz-ascii-art/` within this repo. If you're working in the VIZ directory, OpenClaw will auto-discover it.

**Option 2: Global skill (all projects)**

```bash
# Copy to managed skills directory
cp -r skills/viz-ascii-art ~/.openclaw/skills/
```

**Option 3: Extra dirs config**

Add to `~/.openclaw/openclaw.json`:
```json
{
  "skills": {
    "load": {
      "extraDirs": ["/path/to/VIZ/skills"]
    }
  }
}
```

### For Claude Code / Claude.ai

Upload the `skills/viz-ascii-art/` folder as a skill in Claude settings.

### For Other AgentSkills-Compatible Agents

Copy `skills/viz-ascii-art/` to your agent's skills directory. The skill follows the standard AgentSkills format.

## Skill Structure

```
viz-ascii-art/
├── SKILL.md              # Main skill instructions (loaded when activated)
├── README.md             # This file (not loaded by AI)
└── references/           # Detailed docs (loaded on-demand)
    ├── EMOTIONS.md       # Full VAD values for 25 emotions
    ├── EFFECTS.md        # All 7 effects with parameters
    └── EXAMPLES.md       # Complete usage examples
```

## How AI Uses This Skill

1. **Trigger**: User mentions "visualization", "ASCII art", "kaomoji", "emotion image", etc.
2. **Load**: AI loads `SKILL.md` (~230 lines)
3. **Check**: AI verifies VIZ is installed (or installs it)
4. **Execute**: AI constructs JSON and pipes to `viz.py generate`
5. **Return**: AI parses stdout JSON and presents result path

## Example Interaction

**User**: "Create a euphoric market visualization for BTC hitting $100K"

**AI** (with skill loaded):
```bash
echo '{"source":"market","headline":"BTC $100K","emotion":"euphoria","metrics":["Volume: $89B"]}' | python3 viz.py generate
```

**Result**: `media/viz_20260203_120000.png`

## Customization

### Modify Triggers

Edit `description` field in `SKILL.md` frontmatter to change when AI activates this skill.

### Add More References

Create new `.md` files in `references/` for domain-specific knowledge. AI can read these on-demand when more detail is needed.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `VIZ_PATH` | Custom VIZ installation path |
| `VIZ_OUTPUT_DIR` | Override default `./media/` output |

## Requirements

- Python 3.7+
- Pillow (PIL) >= 9.0.0

No NumPy or other heavy dependencies.

## License

Same as VIZ project - see root LICENSE file.

## Links

- [VIZ Repository](https://github.com/aaajiao/VIZ)
- [AgentSkills Specification](https://agentskills.io/specification)
- [OpenClaw Skills Documentation](https://docs.openclaw.ai/tools/skills)
