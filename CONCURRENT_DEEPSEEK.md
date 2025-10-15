# Concurrent DeepSeek Agent System

Your background task queue now supports **concurrent DeepSeek agents** with automatic retry and low-balance protection.

## ✨ New Features

### 1. **Concurrent Workers (ThreadPoolExecutor)**
- **Default**: 4 concurrent DeepSeek workers
- **Benefit**: 4 entity cards generate in ~15s instead of 60s (4×15s sequential)
- **Configurable**: Can be adjusted via `get_task_queue(max_workers=N)`

### 2. **Automatic Retry with Exponential Backoff**
- Tasks automatically retry on failure (default: 3 attempts)
- Wait time doubles each retry: 1s → 2s → 4s (capped at 60s)
- **Exception**: Low balance errors (402) do NOT retry

### 3. **Low Balance Protection**
- Detects OpenRouter 402 errors (insufficient balance)
- **Does NOT retry** on low balance (prevents wasting attempts)
- Logs clear warning: `[LOW BALANCE] Entity card generation for X failed`
- Tells you exactly what to do: Add credits to OpenRouter

### 4. **Task Persistence**
- Pending tasks saved to disk every operation
- **Location**: `%TEMP%\rp_claude_code_tasks.json`
- **Survives**: Crashes, Ctrl+C interruptions
- **Tracks**: Task IDs, queue times, retry counts

## 📊 How It Works

### OpenRouter Rate Limits

**Your concurrent capacity = Account balance in dollars**

| Balance | Max Concurrent | Example |
|---------|----------------|---------|
| $5 | 5 workers | 5 cards in 15s instead of 75s |
| $10 | 10 workers | 10 cards in 15s instead of 150s |
| $25 | 25 workers | More than you'll ever need |

**Minimum**: 1 RPS even with < $1
**Maximum**: 500 RPS (default cap)

### Example Timeline

**Without concurrency** (old):
```
Card 1: [████████████████] 15s
Card 2: [████████████████] 15s
Card 3: [████████████████] 15s
Card 4: [████████████████] 15s
Total: 60 seconds
```

**With 4 concurrent workers** (new):
```
Card 1: [████████████████] 15s
Card 2: [████████████████] 15s  ← All running simultaneously
Card 3: [████████████████] 15s
Card 4: [████████████████] 15s
Total: 15 seconds (4x faster!)
```

## 🛡️ Failure Handling

### Scenario 1: Temporary Network Error
```
Attempt 1: Network timeout (wait 1s)
Attempt 2: Network timeout (wait 2s)
Attempt 3: Success! ✓
```

### Scenario 2: Low Balance (402 Error)
```
Attempt 1: 402 Insufficient Balance
⚠️  [LOW BALANCE] Entity card for "Marcus" failed
   Please add credits to https://openrouter.ai/credits

Task marked as FAILED (no retry)
```

### Scenario 3: All Retries Exhausted
```
Attempt 1: API error (wait 1s)
Attempt 2: API error (wait 2s)
Attempt 3: API error (wait 4s)
Task marked as FAILED after 3 attempts
```

## 📝 Configuration

### Option 1: Use Defaults (Recommended)
```python
# Automatically uses 4 workers, saves to temp dir
from src.automation.background_tasks import queue_entity_card_generation

task_id = queue_entity_card_generation(
    "Marcus",
    generate_func,
    arg1, arg2,
    log_file=log_file
)
```

### Option 2: Custom Worker Count
```python
from src.automation.background_tasks import get_task_queue

# Initialize with 8 workers (requires $8+ OpenRouter balance)
queue = get_task_queue(max_workers=8)

queue.queue_task(some_function, arg1, arg2, max_retries=5)
```

### Option 3: Custom Persistence Location
```python
from pathlib import Path
from src.automation.background_tasks import get_task_queue

persistence_file = Path("C:/MyRP/state/background_tasks.json")
queue = get_task_queue(max_workers=4, persistence_file=persistence_file)
```

## 📈 Monitoring

### Check Queue Stats
```python
from src.automation.background_tasks import get_task_queue

queue = get_task_queue()
stats = queue.get_stats()

print(stats)
# {
#     'pending': 2,      # Tasks waiting in queue
#     'running': 4,      # Tasks currently executing
#     'completed': 15,   # Successfully completed
#     'failed': 1,       # Failed after all retries
#     'retried': 3,      # Number of retry attempts
#     'total': 16,       # Total tasks processed
#     'workers': 4       # Number of workers
# }
```

### Check Logs
Entity card generation logs to your automation log:
```
[BACKGROUND] Queued task entity_card_Marcus_1234567890 for Marcus
[BACKGROUND] Entity card generation COMPLETED for Marcus

[BACKGROUND] ⚠️ LOW BALANCE: Entity card generation for Sarah failed - please add credits to OpenRouter
```

### Check Persistence File
Location: `%TEMP%\rp_claude_code_tasks.json`

```json
{
  "timestamp": "2025-10-14T15:30:45",
  "pending": [
    {
      "task_id": "entity_card_Sarah_1234567890",
      "queued_at": "2025-10-14T15:30:40",
      "retry_count": 2
    }
  ],
  "stats": {
    "pending": 1,
    "running": 3,
    "completed": 12,
    "failed": 0
  }
}
```

## ⚠️ Important Notes

### Balance Management
- **Monitor your OpenRouter balance**: https://openrouter.ai/credits
- **Concurrent workers = dollars in account**
- Keep at least $5-10 for smooth operation
- System will warn you but WON'T retry on 402 errors

### Task Persistence
- Tasks persist to disk automatically
- **Note**: Only task metadata is saved (ID, timestamp, retries)
- Actual function references can't be persisted
- On restart, app would need to re-queue any incomplete tasks

### Worker Count
- Default: 4 workers (good for most use cases)
- Increase if you have high balance and many entities
- Decrease if you want to be conservative
- **Max useful**: ~10 workers (unless you have 100+ entities)

## 🚀 Performance Impact

### Entity Card Generation

**Before**:
- 1 entity: ~15 seconds
- 4 entities: ~60 seconds (sequential)
- 10 entities: ~150 seconds (2.5 minutes!)

**After (4 workers)**:
- 1 entity: ~15 seconds (same)
- 4 entities: ~15 seconds (4x faster!)
- 10 entities: ~38 seconds (3 batches: 4+4+2)

**After (8 workers, requires $8+ balance)**:
- 10 entities: ~30 seconds (2 batches: 8+2)

### Overall Response Times

Your 15-45 second response time won't change much (that's mostly Claude processing), BUT:
- ✅ Entity cards won't block responses anymore
- ✅ Multiple entities trigger simultaneously in background
- ✅ No more 10-20 second freezes when hitting mention threshold

## 🧪 Testing

After brainstorming, test by mentioning 3-4 new entities in one message:

```
User: "I met Marcus at the cafe. He introduced me to Sarah and David."
```

Watch the logs:
```
[AUTO-GEN] Queuing entity card generation for: Marcus
[AUTO-GEN] Queued task entity_card_Marcus_1234567890 for Marcus
[AUTO-GEN] Queuing entity card generation for: Sarah
[AUTO-GEN] Queued task entity_card_Sarah_1234567891 for Sarah
[AUTO-GEN] Queuing entity card generation for: David
[AUTO-GEN] Queued task entity_card_David_1234567892 for David

(All 3 generate simultaneously in ~15 seconds instead of 45 seconds)

[BACKGROUND] Entity card generation COMPLETED for Marcus
[BACKGROUND] Entity card generation COMPLETED for David
[BACKGROUND] Entity card generation COMPLETED for Sarah
```

## 📞 Support

If you see low balance errors:
1. Go to https://openrouter.ai/credits
2. Add $5-10 to your account
3. Tasks will automatically work again

No code changes needed - the system handles everything automatically!
