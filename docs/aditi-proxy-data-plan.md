# Aditi's Proxy Data Plan

## What is Proxy Data?
Real Deri data is blocked. We can't access real user data yet.
So we use INTERN PROFILES as fake data.

## Intern Profiles
Each intern has:
- Name
- Goals (3-year aspirations)
- Interests
- Skills

## How to Convert to Test Data

### Goals
For each intern, create Goal objects from their stated goals:
- Goal 1: From "3-year goal" field → priority 9, smile_phase "reality-emulation"
- Goal 2: From "interests" array → combine all interests into a single goal description, priority 6, smile_phase "reality-emulation"

### Signals
For each intern, create Signal objects from their skills and interests:
- Each skill → signal with stream "intern_proxy", event_type "skill_demonstrated", and payload {"skill": "<skill_name>"}
- Each interest → signal with stream "intern_proxy", event_type "interest_identified", and payload {"interest": "<interest_name>"}

## Example
Intern: Aditi Mehta
- Goals: ["Build a startup", "Become a lead AI Engineer"]
- Skills: ["python", "tensorflow", "deeplearning"]
- Signals: 3 signals (one per skill, with stream "intern_proxy" and payload)

## Output Format
JSON file with:
{
  "goals": [...],
  "signals": [...],
  "metadata": {
    "generated_at": "...",
    "interns_count": 7,
    "goals_count": 14,
    "signals_count": 40
  }
}
