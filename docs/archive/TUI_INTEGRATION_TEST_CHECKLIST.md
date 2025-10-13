# TUI + Claude Code Integration Test Checklist

## Pre-Test Setup

**Before starting tests:**
1. Make sure Claude Code is installed and `claude` command works
2. Have the Example RP folder ready
3. Launch the TUI and Bridge

---

## Test 1: Basic Message Flow ✅/❌

**Goal**: Verify messages go through and responses come back

**Steps:**
1. Launch TUI: `python rp_client_tui.py "Example RP"`
2. Launch Bridge (separate terminal): `python tui_bridge.py "Example RP"`
3. Type a simple message in TUI: "Hello, testing the system"
4. Press Ctrl+Enter
5. Wait for response

**Expected Results:**
- ✅ Bridge terminal shows: "📨 Received input from TUI"
- ✅ Bridge terminal shows: "🤖 Sending to Claude Code..."
- ✅ Bridge terminal shows: "✅ Response received"
- ✅ TUI shows Claude's response
- ✅ No errors in either terminal

**Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
_________________________________________________________________

---

## Test 2: Response Counter ✅/❌

**Goal**: Verify hook increments response counter

**Steps:**
1. Before test: Check `Example RP/state/response_counter.txt`
   - Note the current number: _______
2. Send a message through TUI
3. After response: Check `response_counter.txt` again
   - New number should be +1: _______

**Expected Results:**
- ✅ Counter increased by 1
- ✅ File exists and is readable

**Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
_________________________________________________________________

---

## Test 3: Hook Execution ✅/❌

**Goal**: Verify hook runs and logs activity

**Steps:**
1. Check `Example RP/state/hook.log`
   - Note timestamp of last entry: _______
2. Send a message through TUI
3. Check `hook.log` again
   - Should have new entries with current timestamp

**Expected Results:**
- ✅ New log entries added
- ✅ Log shows hook execution steps
- ✅ Timestamp is current

**Result:** ⬜ PASS  ⬜ FAIL

**Log snippet:**
_________________________________________________________________

---

## Test 4: CURRENT_STATUS.md Update ✅/❌

**Goal**: Verify status file updates automatically

**Steps:**
1. Open `Example RP/CURRENT_STATUS.md` in a text editor
2. Note the "Last Updated" timestamp: _______
3. Send a message through TUI
4. Refresh/reopen `CURRENT_STATUS.md`
5. Check if "Last Updated" changed

**Expected Results:**
- ✅ File updates with new timestamp
- ✅ Response count increases
- ✅ Shows current automation status

**Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
_________________________________________________________________

---

## Test 5: Commands Work ✅/❌

**Goal**: Verify slash commands execute through TUI

**Steps:**
1. In TUI, type: `/status`
2. Press Ctrl+Enter
3. Wait for response

**Expected Results:**
- ✅ Claude responds with formatted status report
- ✅ Shows current state, progress, entities, automation
- ✅ No errors

**Result:** ⬜ PASS  ⬜ FAIL

**Response preview:**
_________________________________________________________________

---

## Test 6: Entity Tracking ✅/❌

**Goal**: Verify entity mention tracking works

**Steps:**
1. Check `Example RP/state/entity_tracker.json`
   - Note entities and mention counts: _______
2. Send message mentioning a NEW entity name twice:
   - "I met [NewName] today. [NewName] was friendly."
3. Check `entity_tracker.json` again

**Expected Results:**
- ✅ NewName appears in entity_tracker.json
- ✅ Mention count = 2
- ✅ If threshold is 2, card_created should be true or pending

**Result:** ⬜ PASS  ⬜ FAIL

**entity_tracker.json snippet:**
_________________________________________________________________

---

## Test 7: Auto-Entity Card Generation ✅/❌

**Goal**: Verify entity cards auto-generate at threshold

**Steps:**
1. If Test 6 triggered card generation (2+ mentions):
   - Check `Example RP/entities/` folder
   - Look for `[CHAR] NewName.md` or similar
2. If card was created:
   - Open it and verify it has content
   - Check if it follows template format

**Expected Results:**
- ✅ Card file created in entities/ folder
- ✅ Card has proper format (triggers, description, etc.)
- ✅ Hook log shows "Auto-generated entity card: NewName"

**Result:** ⬜ PASS  ⬜ FAIL

**Card filename:** _______________________________

---

## Test 8: Time Tracking ✅/❌

**Goal**: Verify hook suggests time elapsed

**Steps:**
1. Send message with time-consuming activity:
   - "We had a long conversation about the plan."
2. Look at Claude's response
3. Check if time suggestion appears (in response or injected)

**Expected Results:**
- ✅ Hook calculates time based on activities
- ✅ Either appears in Claude response or in hook log
- ✅ Time makes sense for activity

**Result:** ⬜ PASS  ⬜ FAIL

**Time suggested:** _______________________________

---

## Test 9: /continue Command ✅/❌

**Goal**: Verify session start command works

**Steps:**
1. In TUI, type: `/continue`
2. Press Ctrl+Enter
3. Wait for response

**Expected Results:**
- ✅ Loads session context (chapter, time, location)
- ✅ Shows active plot threads
- ✅ Displays last RP response
- ✅ Ready to continue story

**Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
_________________________________________________________________

---

## Test 10: Bridge Error Handling ✅/❌

**Goal**: Verify bridge handles errors gracefully

**Steps:**
1. Send a very long message (2000+ characters)
2. OR: Send a message while bridge is processing another
3. Check bridge terminal for error messages

**Expected Results:**
- ✅ Bridge doesn't crash
- ✅ Error messages are clear
- ✅ TUI shows error or waits appropriately

**Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
_________________________________________________________________

---

## Summary

**Tests Passed:** _____ / 10

**Critical Issues Found:**
-
-
-

**Minor Issues Found:**
-
-
-

**Overall Status:** ⬜ READY FOR FEATURES  ⬜ NEEDS FIXES

---

## Next Steps Based on Results

### If ALL PASS (or mostly pass):
✅ Proceed to **Phase 2: Add Status Display**
- Integration works!
- Add UI polish

### If SOME FAIL:
⚠️ Fix issues before proceeding:
- If Test 1 fails: Check bridge connection
- If Test 2-4 fail: Check hook execution
- If Test 5 fails: Check command routing
- If Test 6-7 fail: Check entity tracking logic
- If Test 8 fails: Check time calculation
- If Test 9 fails: Check command files
- If Test 10 fails: Add error handling

### If MOST/ALL FAIL:
🛑 Debug integration:
- Is Claude Code installed?
- Is `claude` command in PATH?
- Are hooks executable (chmod +x)?
- Is working directory correct?
- Check bridge terminal for errors

---

**Test Date:** _______________________________

**Tester:** _______________________________

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
