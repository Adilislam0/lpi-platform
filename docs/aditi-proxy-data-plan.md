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
- Goal 1: From "3-year goal" field → priority 9, smile_phase "sense"
- Goal 2: From "interests" → priority 6, smile_phase "sense"
### Signals
For each intern, create Signal objects from their skills:
- Each skill → signal with event_type "skill_demonstrated"
- Each interest → signal with event_type "interest_identified"
## Example
Intern: Aditi Mehta
- Goals: ["Build a startup", "Become a lead AI Engineer"]
- Skills: ["python", "tensorflow", "deeplearning"]
- Signals: 3 signals (one per skill)
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
