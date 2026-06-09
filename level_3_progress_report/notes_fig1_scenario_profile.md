# Speaker Notes — Figure 1: Compound Disaster Scenario Profile
**File:** `figures/l3_compound_scenario_profile.png`

## What this graph shows
The *input* disaster model — how the simulated GNSS environment degrades over the
mission. It is the scenario we imposed, not a result. Three things vary together over
mission time: GNSS noise (σ, metres), correction quality (0–1), and correction dropout
windows.

## How to read it
- X-axis: mission elapsed time (s). Five phases are shaded and labelled:
  **Departure → Approach → Search Zone → Landing → Exit**.
- The noise trace rises from open-sky to the collapse site, correction quality falls,
  and dropout bars mark the windows where corrections are lost entirely.

## Key numbers to say out loud
- Departure: noise **1.5 m**, quality **0.95**, no dropouts.
- Search Zone (peak degradation): noise **2.75 m**, quality **0.60**, dropout **37.5 s every 90 s**.
- Recovery in Exit: noise falls back toward **1.5 m**, quality back to **0.90**.

## What to say
"This is the disaster we designed — not one failure, but three co-occurring and
progressive degradations across a full rescue mission. It is deliberately a *compound*
scenario because real disaster zones degrade on multiple axes at once."

## Honest caveat
This is the commanded profile. The phase windows are reconstructed from drone-movement
time and lead the actual error onset by a few tens of seconds — mention only if asked.
