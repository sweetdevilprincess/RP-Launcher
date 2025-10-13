# Time Tracking Guide

## Purpose
Maintain realistic time progression throughout the story by calculating accurate activity durations and advancing timestamps appropriately.

---

## Timestamp Format Standard

**Required Format:**
```
[Weekday, Month Day, Year - HH:MM AM/PM, Current Location]
```

**Examples:**
- `[Saturday, November 5th, 2024 - 7:20 PM, Bruno's Italian Restaurant]`
- `[Friday, November 4th, 2024 - 11:35 PM, Lilith's Apartment]`

---

## Activity Duration Procedure

### Step-by-Step Process

1. **Scan user actions**: Identify all activities mentioned in user input
2. **Lookup base durations**: Reference exact minute values from Timing.txt for each activity
3. **Detect modifiers**: Identify speed/intensity descriptors (fast, slow, relaxed, rushed)
4. **Apply modifier calculations**: Adjust base time accordingly
5. **Calculate compound activities**: Sum durations for multiple sequential actions
6. **Estimate unlisted activities**: Use closest analogous activity from Timing.txt
7. **Advance timestamp**: Add calculated total minutes to previous timestamp
8. **Update location context**: Note any location changes during elapsed time

---

## Base Activity Times

Reference **Timing.txt** for complete list. Common activities:

### Social Interactions
- **chat**: 15 minutes
- **talk**: 10 minutes
- **argue**: 12 minutes
- **comfort**: 8 minutes
- **confess**: 8 minutes

### Physical Intimacy
- **kiss**: 2 minutes
- **cuddle**: 6 minutes
- **hug**: 3 minutes

### Daily Activities
- **eat**: 10 minutes
- **drink**: 3 minutes
- **cook**: 20 minutes
- **bathe**: 15 minutes
- **dress**: 5 minutes
- **groom**: 7 minutes

### Travel & Movement
- **walk**: 10 minutes
- **run**: 4 minutes
- **ride**: 15 minutes (motorcycle, car, etc.)

### Work & Study
- **work**: 60 minutes
- **study**: 30 minutes
- **read**: 15 minutes
- **write**: 20 minutes

### Entertainment
- **watch**: 10 minutes (TV show scene, etc.)
- **game**: 15 minutes
- **dance**: 12 minutes
- **listenmusic**: 8 minutes

---

## Modifier Calculations

### Speed/Intensity Modifiers

**Fast**: Reduce base time by 25%
- Formula: `base_time × 0.75`
- Example: "quick kiss" = 2 × 0.75 = 1.5 minutes

**Slow**: Increase base time by 50%
- Formula: `base_time × 1.5`
- Example: "slow passionate encounter" = 20 × 1.5 = 30 minutes

**Relaxed**: Increase base time by 25%
- Formula: `base_time × 1.25`
- Example: "relaxed dinner" = 10 × 1.25 = 12.5 minutes

**Rushed**: Reduce base time by 40%
- Formula: `base_time × 0.6`
- Example: "rushed intimacy" = 15 × 0.6 = 9 minutes

---

## Activity Matching Rules

### Direct Match
Use exact Timing.txt entry when available.

**Example:**
- "They eat dinner" → eat (10 minutes)

### Compound Intimacy
Sum multiple related activities.

**Examples:**
- "kiss + cuddle + intimate contact" = kiss(2) + cuddle(6) + estimated_intimate_time(8-15) = 16-23 minutes
- "making out" = kiss(2) + cuddle(6) = 8 minutes minimum
- "passionate encounter" = multiple kiss + cuddle + intimate activities = 15-25 minutes

### Analogous Matching
Match to closest similar activity when exact match isn't available.

**Examples:**
- "brief conversation" → chat(15) or talk(10)
- "heated argument" → argue(12)
- "quick examination" → study(30) with "fast" modifier = 22 minutes
- "passionate intimacy" → estimate 15-25 minutes based on intensity

### Estimation Fallback
Base on closest activity type. **Never default to 1 minute** unless it's truly a minor action (Timing.txt has "minor: 1").

---

## Compound Activity Examples

### Multiple Sequential Actions
Sum the durations:

**Example 1:**
- "They talk then eat dinner" = talk(10) + eat(10) = **20 minutes**

**Example 2:**
- "She bathes, dresses, then goes to work" = bathe(15) + dress(5) + work(60) = **80 minutes**

**Example 3:**
- "Intimate cuddle session with kissing" = cuddle(6) + kiss(2) + additional_intimacy(10) = **18 minutes minimum**

**Example 4:**
- "Brief argument followed by making up" = argue(12) + comfort(8) + kiss(2) = **22 minutes**

---

## Intimacy Duration Specifics

### Physical Intimacy Base Times

- **kiss**: 2 minutes
- **cuddle**: 6 minutes
- **hug**: 3 minutes
- **intimate exploration**: 8-15 minutes (estimate based on intensity)
- **passionate intimacy**: 15-25 minutes (multiple activities combined)
- **sexual encounter**: 20-40 minutes (estimate based on description)

### With Modifiers

**Slow passionate encounter:**
- base_intimacy(20) × 1.5 = **30 minutes**

**Quick kiss:**
- kiss(2) × 0.75 = **1.5 minutes**

**Rushed intimacy:**
- base_intimacy(15) × 0.6 = **9 minutes**

---

## Validation Requirements

### Critical Rules

1. **No default fallback**: Never use 1 minute as default - always calculate or estimate
2. **Minimum duration enforcement**: Most activities require at least their base Timing.txt duration
3. **Logical consistency**: Ensure calculated time makes sense for described activity intensity
4. **Modifier logic**: Confirm speed modifications align with activity description

### Sanity Checks

- Does the time feel realistic for what was described?
- Are modifiers applied correctly (fast = shorter, slow = longer)?
- Have all sequential activities been summed?
- Is the location update consistent with time elapsed?

---

## Special Situations

### Travel Time
Account for realistic travel distances:
- **Walk across town**: 30-40 minutes
- **Short motorcycle ride**: 10-15 minutes
- **Drive to restaurant**: 15-20 minutes
- **Walk to nearby location**: 5-10 minutes

### Conversations During Activities
If talking happens during another activity (like eating), use the longer duration:
- "They eat and chat" = eat(10), not eat(10) + chat(15)

### Interrupted Activities
If an activity is interrupted partway through, estimate partial time:
- "Started cooking but got interrupted" = cook(20) × 0.5 = 10 minutes

---

## Timestamp Advancement Examples

### Example 1: Simple Activity
**Previous timestamp:** Saturday, November 5th, 2024 - 7:20 PM, Bruno's Italian Restaurant
**User action:** "They finish dinner and talk"
**Calculation:** eat(10) + talk(10) = 20 minutes
**New timestamp:** Saturday, November 5th, 2024 - 7:40 PM, Bruno's Italian Restaurant

### Example 2: With Modifiers
**Previous timestamp:** Friday, November 4th, 2024 - 11:00 PM, Lilith's Apartment
**User action:** "She takes a quick shower and gets dressed"
**Calculation:** bathe(15) × 0.75 (fast) + dress(5) = 11.25 + 5 = 16.25 minutes (~16 minutes)
**New timestamp:** Friday, November 4th, 2024 - 11:16 PM, Lilith's Apartment

### Example 3: Travel + Activity
**Previous timestamp:** Saturday, November 5th, 2024 - 6:30 PM, Lilith's Apartment
**User action:** "They ride his motorcycle to the restaurant"
**Calculation:** ride(15) = 15 minutes
**New timestamp:** Saturday, November 5th, 2024 - 6:45 PM, Bruno's Italian Restaurant
**Note:** Location changed from apartment to restaurant

### Example 4: Compound Intimacy
**Previous timestamp:** Friday, November 4th, 2024 - 10:45 PM, Parking Lot
**User action:** "Slow passionate kissing and touching on the motorcycle"
**Calculation:** kiss(2) + cuddle(6) + intimate_exploration(10) × 1.5 (slow) = 27 minutes
**New timestamp:** Friday, November 4th, 2024 - 11:12 PM, Parking Lot

---

## Integration with Story

### Include in Response
After calculating time, update:
1. **Timestamp** at the beginning of response
2. **Location** if it changed
3. **Time-sensitive context** (e.g., "late night," "dinner rush," "closing time")

### Track Continuity
Consider time-of-day implications:
- Work schedules (Lilith works Tuesday-Saturday mornings)
- Business hours (coffee shop, restaurant, bar)
- Realistic fatigue (late night activities)
- Environmental changes (daylight, temperature, crowds)

---

## Quick Reference Checklist

Before finalizing each response:

- [ ] Identified all activities in user input
- [ ] Looked up base times from Timing.txt
- [ ] Applied any speed/intensity modifiers
- [ ] Summed compound/sequential activities
- [ ] Advanced timestamp by calculated minutes
- [ ] Updated location if travel occurred
- [ ] Verified time feels realistic for described action
- [ ] Considered time-of-day implications

---

## Error Prevention

### Common Mistakes to Avoid
❌ Defaulting to 1 minute for everything
❌ Forgetting to sum sequential activities
❌ Ignoring modifiers when user specifies speed
❌ Using unrealistic travel times
❌ Not updating location after travel
❌ Making intimate scenes too short (2 minutes of kissing is not a "passionate encounter")

### When in Doubt
- Use the **longer** estimate for intimate/emotional scenes
- Use the **base** time if no modifier is specified
- **Ask yourself**: "Does this feel realistic?"
- **Check** if the timestamp makes sense with story context (work schedules, business hours, etc.)