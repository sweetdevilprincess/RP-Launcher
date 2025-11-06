# Scene Marker & Bookmark System - Design Document

## Overview

A two-tier system for organizing and marking important content in RP conversations:
- **Scene Markers** 🎬: Formal story segments that span multiple messages
- **Bookmarks** 📌: Quick marks for knowledge, threads, favorites within or outside scenes

---

## Scene Markers 🎬

### Concept
Scenes are **story segments** with a defined start and end point, encompassing multiple messages. They represent major narrative moments, locations, or events.

### Features

#### Scene Boundaries
- **Scene Start** (🎬 scene_start): Marks where a scene begins
- **Scene End** (🎬 scene_end): Marks where a scene ends
- Scenes span all messages between start and end markers

#### Scene Properties
- **Title**: Required - descriptive name ("Forest Encounter", "Dragon's Lair")
- **Importance**: Optional flag marking critical scenes (⭐ Important Scene)
- **Description**: Optional - brief summary or notes about the scene
- **Message Range**: Start message index → End message index

#### Scene Types (Future)
- **Location**: Setting-based scenes ("The Tavern", "Mountain Pass")
- **Event**: Action-based scenes ("Battle with Goblins", "Royal Feast")
- **Character**: Character-focused scenes ("Meeting the Wizard", "Emotional Moment")
- **Chapter**: Major structural divisions

### Visual Representation

```
┌─────────────────────────────────────────┐
│ System                                  │
│ Welcome to the adventure!               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐ 🎬 scene_start: "Forest Encounter" ⭐
│ DM                                      │
│ You enter the dark forest...       📚  │
└─────────────────────────────────────────┘
  🌿 📌 ✏️ 📋 ⋯

┌─────────────────────────────────────────┐
│                                You      │
│ I approach cautiously...                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ DM                                 🧵   │
│ Strange sounds echo...         📚      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐ 🎬 scene_end: "Forest Encounter"
│ DM                                      │
│ You escape the forest safely.           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐ 🎬 scene_start: "Village"
│ DM                                 ⭐   │
│ You arrive at the peaceful village.     │
└─────────────────────────────────────────┘
```

### UI/UX

#### Creating Scene Markers
1. **Scene Start:**
   - Hover over message → Click 🎬 button (in More menu)
   - Dialog opens: "Start New Scene"
     - Title: [text input]
     - Mark as Important: [checkbox] ⭐
     - Description: [optional textarea]
   - Creates scene_start marker at this message

2. **Scene End:**
   - When inside an open scene, 🎬 button shows "End Current Scene"
   - Click to mark current message as scene_end
   - Scene is now complete and spans start → end range

#### Scene Indicators
- **Start marker**: Shows `🎬 scene_start: "Title" [⭐]` above message
- **End marker**: Shows `🎬 scene_end: "Title"` above message
- **Within scene**: Subtle left border or background tint showing you're in a scene
- **Important scenes**: Show ⭐ badge on scene_start marker

---

## Bookmarks 📌

### Concept
Quick, lightweight marks for flagging individual messages for different purposes. Can exist anywhere - inside scenes or outside.

### Bookmark Types

#### 📚 Knowledge
**Purpose:** Important facts, world-building details, lore, character info
**Examples:**
- "Dragon lives in northern mountains"
- "The artifact was forged 1000 years ago"
- "Character X's secret motivation"

#### 🧵 Thread
**Purpose:** Plot threads, things to follow up on, unresolved questions
**Examples:**
- "Need to investigate the mysterious stranger"
- "Follow up on the stolen artifact"
- "Character mentioned prophecy - track this"

#### ⭐ Favorite
**Purpose:** Moments you loved, great writing, emotional beats
**Examples:**
- "Amazing dramatic moment"
- "Loved this character interaction"
- "Epic battle description"

#### 📝 Note (Default)
**Purpose:** General bookmark, catch-all for other reasons
**Examples:**
- "Remember this for later"
- "Check continuity here"
- "Possible branch point"

### Features
- **Quick Toggle**: Click 📌 to bookmark with default type (📝 Note)
- **Choose Type**: Right-click or long-press to select bookmark type
- **Multiple per Message**: Same message can have multiple bookmark types
- **Optional Notes**: Add text note to any bookmark (future feature)
- **Scene Association**: Bookmarks know which scene (if any) they're in

### Visual Representation
- Small icon badge in corner of message (📚, 🧵, ⭐, 📝)
- Multiple bookmarks stack: 📚🧵 (Knowledge + Thread)
- Hover over bookmark icon shows type and note (if any)

---

## Data Structure

### Session State Storage

```json
{
  "scene_markers": [
    {
      "id": "scene-001",
      "title": "Forest Encounter",
      "start_message_index": 5,
      "end_message_index": 12,
      "important": true,
      "description": "First encounter with the dark forest creatures",
      "created_at": "2025-11-03T20:00:00Z"
    },
    {
      "id": "scene-002",
      "title": "Village",
      "start_message_index": 13,
      "end_message_index": null,  // Open scene (not ended yet)
      "important": false,
      "description": "",
      "created_at": "2025-11-03T20:15:00Z"
    }
  ],
  "bookmarks": [
    {
      "id": "bookmark-001",
      "message_index": 7,
      "type": "knowledge",  // "knowledge", "thread", "favorite", "note"
      "note": "Dragon lives in northern mountains",
      "scene_id": "scene-001",  // Associated scene (null if outside scenes)
      "created_at": "2025-11-03T20:05:00Z"
    },
    {
      "id": "bookmark-002",
      "message_index": 7,
      "type": "thread",
      "note": "Follow up on dragon's lair location",
      "scene_id": "scene-001",
      "created_at": "2025-11-03T20:06:00Z"
    },
    {
      "id": "bookmark-003",
      "message_index": 14,
      "type": "favorite",
      "note": "",
      "scene_id": "scene-002",
      "created_at": "2025-11-03T20:16:00Z"
    }
  ]
}
```

---

## Integration with Branch Page

### New Section: Scene Navigator

**Location:** Branch page (alongside timeline browser)

**Features:**
1. **Scene List View**
   ```
   📋 Scenes (3)

   ⭐ Forest Encounter           [5-12]  🎬
      📚 2 bookmarks  🧵 1 thread

   Village (ongoing)             [13-?]  🎬
      ⭐ 1 favorite

   Dragon's Lair                [18-25]  🎬
      📚 3 bookmarks
   ```

2. **Scene Details Panel**
   - Click scene to see:
     - Title and description
     - Message range
     - All bookmarks within scene
     - Quick jump to scene start/end
     - Edit scene properties

3. **Filter/Sort Options**
   - Show only important scenes (⭐)
   - Sort by: Date, Title, Length
   - Filter by bookmark content (scenes with knowledge, threads, etc.)

4. **Quick Actions**
   - Jump to scene start
   - Jump to scene end
   - Create branch from scene start
   - Export scene text
   - Edit scene properties

### Navigation Flow

```
Branch Page
├── Timeline Browser (existing)
│   └── View branches and messages by timestamp
│
├── Scene Navigator (new)
│   ├── Scene List (all scenes across all branches)
│   ├── Scene Details (when scene selected)
│   └── Quick Jump (click to go to scene in chat)
│
└── Bookmark Browser (new)
    ├── Filter by type (📚 🧵 ⭐ 📝)
    ├── Filter by scene (bookmarks in specific scene)
    └── Quick Jump (click to go to message)
```

---

## Implementation Phases

### Phase 1: Foundation (Current)
- [x] Basic bookmark button (📌) - quick toggle
- [ ] Scene marker button (🎬) - in More menu
- [ ] Scene start dialog (title, important flag)
- [ ] Scene end functionality
- [ ] Visual indicators for scene boundaries
- [ ] Store scenes and bookmarks in session state

### Phase 2: Bookmark Types
- [ ] Add bookmark type selection UI
- [ ] Visual indicators for different bookmark types
- [ ] Multiple bookmarks per message
- [ ] Bookmark notes (optional text)

### Phase 3: Scene Navigator
- [ ] Add Scene Navigator to Branch Page
- [ ] Scene list view with filtering
- [ ] Scene details panel
- [ ] Jump to scene functionality
- [ ] Edit scene properties

### Phase 4: Bookmark Browser
- [ ] Bookmark panel/view
- [ ] Filter bookmarks by type
- [ ] Filter bookmarks by scene
- [ ] Search bookmarks by note text
- [ ] Jump to bookmarked message

### Phase 5: Advanced Features
- [ ] Scene types (location, event, character, chapter)
- [ ] Auto-suggest scene names from content
- [ ] Scene statistics (length, bookmark count)
- [ ] Export scenes as separate files
- [ ] Scene templates
- [ ] Bookmark collections/tags

---

## UI Components Needed

### New Components
1. **SceneMarkerDialog** - Create/edit scene properties
2. **SceneIndicator** - Visual marker for scene boundaries
3. **BookmarkTypeSelector** - Choose bookmark type
4. **SceneNavigator** - Scene list and navigation (Branch Page)
5. **BookmarkBrowser** - Bookmark filtering and navigation (Branch Page)

### Modified Components
1. **SimpleMessage** - Add scene boundary indicators
2. **BranchesPage** - Add Scene Navigator and Bookmark Browser
3. **SessionStateService** - Add scene/bookmark management methods

---

## User Stories

### Scene Markers
- As a user, I want to **mark the start of a scene** so I can organize my story into segments
- As a user, I want to **mark the end of a scene** to complete the segment
- As a user, I want to **mark important scenes** so I can quickly find pivotal moments
- As a user, I want to **view all scenes** in a list to navigate my story
- As a user, I want to **jump to a scene** to quickly read that segment

### Bookmarks
- As a user, I want to **bookmark important knowledge** so I can reference it later
- As a user, I want to **mark plot threads** to track unresolved story elements
- As a user, I want to **favorite great moments** to revisit them
- As a user, I want to **filter bookmarks by type** to see all knowledge or all threads
- As a user, I want to **see which scene a bookmark is in** for context

### Integration
- As a user, I want to **see bookmarks within scenes** in the scene navigator
- As a user, I want to **create branches from scene starts** to explore alternate paths
- As a user, I want to **export a scene** with all its bookmarks

---

## Technical Considerations

### Session State
- Scenes and bookmarks stored in session state file
- Persist across sessions
- Branch-specific (each branch has its own scenes/bookmarks)

### Performance
- Efficient lookup: message_index → scenes containing it
- Cache scene ranges for quick "am I in a scene?" checks
- Lazy load bookmark notes (only when viewing bookmark browser)

### Conflicts
- What if scene_start is deleted or moved? Mark scene as "broken"
- What if bookmark points to deleted message? Remove bookmark
- What if scene spans branch point? Scene exists only in that branch

### UI Updates
- Real-time updates when scene/bookmark added
- Visual feedback showing scene boundaries in chat
- Smooth transitions when navigating to scenes

---

## Future Enhancements

### Auto-Detection
- Detect chapter transitions (existing system) → auto-create scenes
- Detect location changes (from scene context) → suggest scenes
- Detect important moments (based on content) → suggest marking as important

### AI Integration
- Summarize scenes automatically
- Suggest bookmark types based on content
- Generate scene titles from content
- Extract knowledge bookmarks from lore-heavy messages

### Export/Sharing
- Export scene as standalone story file
- Export bookmarks as notes document
- Share scenes with others
- Import scenes from other RPs

### Analytics
- Scene length distribution
- Most bookmarked scenes
- Bookmark type distribution
- Scene complexity (based on bookmark count)

---

## Open Questions

1. **Should scenes be hierarchical?** (e.g., Chapter → Scene → Subscene)
2. **Should bookmarks have tags** in addition to types?
3. **Should there be keyboard shortcuts** for quick bookmarking?
4. **Should bookmarks sync across branches** or stay branch-specific?
5. **Should we limit the number of open scenes** (force closing before opening new one)?

---

## Notes

- Scenes provide **structure** and **navigation**
- Bookmarks provide **detail** and **reference**
- Together they create a powerful **story organization system**
- Start simple (Phase 1), expand based on usage patterns
- User feedback will guide feature priorities
