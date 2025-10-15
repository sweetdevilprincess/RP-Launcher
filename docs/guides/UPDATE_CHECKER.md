# Update Checker Guide

The RP Launcher includes an automatic update checker that notifies you when a new version is available on GitHub.

## How It Works

When you launch the application, it:
1. Checks your current git commit SHA
2. Queries GitHub API for the latest commit on the main branch
3. Compares versions and notifies you if an update is available
4. Caches the result for 24 hours to avoid excessive API calls

## Configuration

Update checking is configured in `config.json`:

```json
{
  "check_for_updates": true,
  "update_check_interval": 86400
}
```

### Settings

- **check_for_updates**: Enable/disable update checking (default: `true`)
- **update_check_interval**: How long to cache results in seconds (default: `86400` = 24 hours)

## Command Line Flags

### Skip Update Check

To skip the update check for a single launch:

```bash
python launch_rp_tui.py --skip-update-check
```

This is useful when:
- You're offline
- You want faster startup
- You're testing something and don't want the notification

## Manual Update Check

You can manually check for updates anytime:

```bash
python src/update_checker.py
```

To force a fresh check (ignore cache):

```bash
python src/update_checker.py --no-cache
```

## Updating the Application

When an update is available, you'll see:

```
============================================================
🔔 UPDATE AVAILABLE!
   Current: 0fa7569
   Latest:  abc1234
   Run 'git pull' to update
============================================================
```

To update:

```bash
git pull
```

This will download the latest changes from GitHub.

## API Rate Limits

The update checker uses GitHub's public API which allows:
- **60 requests per hour** (unauthenticated)

The 24-hour cache ensures you won't hit this limit during normal use.

## Troubleshooting

### Update check fails silently

The update checker is designed to fail gracefully and never block startup. If it can't reach GitHub:
- It will use cached results if available
- Otherwise, it will skip the check silently

### Clear the cache

If you want to force a fresh check, delete the cache file:

```bash
rm .update_check_cache
```

Or use the `--no-cache` flag when running the checker manually.

### Disable update checking

To permanently disable update checking, edit `config.json`:

```json
{
  "check_for_updates": false
}
```

## Version Tracking

The current version is tracked in `src/version.py`. This file stores the commit SHA and is updated when you commit changes.

To see your current version:

```bash
python src/version.py
```

Output:
```
RP Launcher Version
  Full:  0fa756999af4bb61160af4d0454c80ded7b6192f
  Short: 0fa7569
  From git: True
```

## Implementation Details

- **Non-blocking**: Update check has a 3-second timeout
- **Cached**: Results are cached to avoid API rate limits
- **Graceful fallback**: Failures never block startup
- **Commit-based**: Uses git commit SHAs for version tracking
- **GitHub API**: Uses `GET /repos/{owner}/{repo}/commits` endpoint
