# Azure AD App Registration - Permission Summary

**App Name**: Patient Explorer
**Registration Date**: December 4, 2025
**Tenant**: southviewteam.com / greenclinicteam.com (multi-domain single tenant)
**Account Type**: Single tenant (organization only)
**Redirect URI**: http://localhost:8501
**Authentication Flow**: OAuth 2.0 with PKCE (no client secret required)

---

## Permission Summary

**Total Permissions Granted**: 43 delegated permissions
**Security Note**: Mail.Send and Mail.ReadWrite were intentionally excluded as a security precaution.

---

## Permissions by Category

### Bookings (4 permissions)
| Permission | Description |
|------------|-------------|
| `Bookings.Manage.All` | Full management of booking businesses |
| `Bookings.Read.All` | Read booking businesses and appointments |
| `Bookings.ReadWrite.All` | Read and write booking businesses |
| `BookingsAppointment.ReadWrite.All` | Read and write booking appointments |

**Use Cases**: Employee scheduling, appointment management, booking page integration

---

### Calendars (2 permissions)
| Permission | Description |
|------------|-------------|
| `Calendars.ReadWrite` | Read and write user calendars |
| `Calendars.ReadWrite.Shared` | Read and write shared calendars |

**Use Cases**: Scheduling, availability management, team coordination

---

### Chat / Teams (6 permissions)
| Permission | Description |
|------------|-------------|
| `Chat.Create` | Create new chat conversations |
| `Chat.Read` | Read user chat messages |
| `Chat.ReadBasic` | Read basic chat properties |
| `Chat.ReadWrite` | Read and write chat messages |
| `ChatMessage.Read` | Read chat messages |
| `ChatMessage.Send` | Send chat messages |

**Use Cases**: Teams integration, internal communication, AI-assisted messaging

---

### Contacts (1 permission)
| Permission | Description |
|------------|-------------|
| `Contacts.ReadWrite` | Read and write user contacts |

**Use Cases**: Contact management, address book synchronization

---

### Directory (1 permission)
| Permission | Description |
|------------|-------------|
| `Directory.AccessAsUser.All` | Access directory as signed-in user |

**Use Cases**: Organization structure access, user lookup, team member discovery

---

### Files / OneDrive (4 permissions)
| Permission | Description |
|------------|-------------|
| `Files.ReadWrite.All` | Full access to user files |
| `Files.ReadWrite.AppFolder` | Read/write app's folder |
| `Files.ReadWrite.Selected` | Read/write files user selects |
| `SelectedOperations.Selected` | Selected file operations |

**Use Cases**: Document storage, file sync, attachment handling

---

### Groups (1 permission)
| Permission | Description |
|------------|-------------|
| `Group.ReadWrite.All` | Read and write all groups |

**Use Cases**: Team management, group membership, collaborative workspaces

---

### Mail (1 permission)
| Permission | Description |
|------------|-------------|
| `Mail.Read` | Read user mail |

**Security Note**: Mail.Send and Mail.ReadWrite were intentionally excluded. App can read but not send or modify emails.

**Use Cases**: Email viewing, message search, notification awareness

---

### Notes / OneNote (6 permissions)
| Permission | Description |
|------------|-------------|
| `Notes.Create` | Create OneNote notebooks |
| `Notes.Read` | Read OneNote notebooks |
| `Notes.Read.All` | Read all notebooks user can access |
| `Notes.ReadWrite` | Read and write OneNote notebooks |
| `Notes.ReadWrite.All` | Read and write all accessible notebooks |
| `Notes.ReadWrite.CreatedByApp` | App-created notebook access |

**Use Cases**: Chart Builder integration, clinical notes, patient documentation (future feature)

---

### People / Presence (5 permissions)
| Permission | Description |
|------------|-------------|
| `People.Read` | Read user's relevant people |
| `People.Read.All` | Read all relevant people |
| `PeopleSettings.Read.All` | Read people settings |
| `Presence.Read` | Read user presence |
| `Presence.ReadWrite` | Read and write presence |

**Use Cases**: Team availability, scheduling intelligence, collaboration features

---

### Short Notes / Sticky Notes (2 permissions)
| Permission | Description |
|------------|-------------|
| `ShortNotes.Read` | Read user's sticky notes |
| `ShortNotes.ReadWrite` | Read and write sticky notes |

**Use Cases**: Quick note capture, reminder integration

---

### SharePoint / Sites (5 permissions)
| Permission | Description |
|------------|-------------|
| `Sites.Manage.All` | Full management of all site collections |
| `Sites.Read.All` | Read items in all site collections |
| `Sites.ReadWrite.All` | Read and write all site collections |
| `Sites.Selected` | Access selected sites |
| `Sites.FullControl.All` | Full control of all site collections |

**Use Cases**: Database sync, document libraries, SharePoint list management

---

### Tasks / Planner (4 permissions)
| Permission | Description |
|------------|-------------|
| `Tasks.Read` | Read user tasks |
| `Tasks.Read.Shared` | Read shared tasks |
| `Tasks.ReadWrite` | Read and write user tasks |
| `Tasks.ReadWrite.Shared` | Read and write shared tasks |

**Use Cases**: Task management hub, Planner integration, To-Do synchronization

---

### Teams (1 permission)
| Permission | Description |
|------------|-------------|
| `Team.ReadBasic.All` | Read basic team properties |

**Use Cases**: Team discovery, membership awareness

---

### User (1 permission)
| Permission | Description |
|------------|-------------|
| `User.Read` | Read signed-in user profile |

**Use Cases**: Authentication, profile display, user identification

---

## Architecture Notes

### Why App-Mediated vs MCP

This app uses **direct Graph API integration** rather than MCP (Model Context Protocol) for the following reasons:

1. **HIPAA Control**: All API calls go through app code where logging, auditing, and data filtering can be enforced
2. **Credential Security**: OAuth tokens stay within app runtime, never exposed to external processes
3. **Consistent Behavior**: Graph API calls behave identically across all user contexts
4. **Audit Trail**: Complete control over what gets logged and when

### Multi-Domain Tenant Support

Both `greenclinicteam.com` and `southviewteam.com` domains are part of the same Azure AD tenant. The "Single tenant" registration option supports all users from both domains automatically.

### PKCE Flow (No Client Secret)

Using PKCE (Proof Key for Code Exchange) eliminates the need for a client secret, which is ideal for:
- Desktop/mobile applications
- Single-page applications
- Environments where secrets cannot be safely stored

---

## Pending Code Updates

The `app/ms_oauth.py` module needs to be updated to include these expanded scopes. Current scopes are limited to:
- User.Read
- Files.ReadWrite.All
- Sites.Read.All
- Notes.Read.All
- Notes.ReadWrite.All

**Full scope list for ms_oauth.py update**:
```python
SCOPES = [
    # User
    "User.Read",

    # Bookings
    "Bookings.Manage.All",
    "Bookings.Read.All",
    "Bookings.ReadWrite.All",
    "BookingsAppointment.ReadWrite.All",

    # Calendars
    "Calendars.ReadWrite",
    "Calendars.ReadWrite.Shared",

    # Chat/Teams
    "Chat.Create",
    "Chat.Read",
    "Chat.ReadBasic",
    "Chat.ReadWrite",
    "ChatMessage.Read",
    "ChatMessage.Send",
    "Team.ReadBasic.All",

    # Contacts
    "Contacts.ReadWrite",

    # Directory
    "Directory.AccessAsUser.All",

    # Files
    "Files.ReadWrite.All",
    "Files.ReadWrite.AppFolder",
    "Files.ReadWrite.Selected",

    # Groups
    "Group.ReadWrite.All",

    # Mail (read only)
    "Mail.Read",

    # Notes/OneNote
    "Notes.Create",
    "Notes.Read",
    "Notes.Read.All",
    "Notes.ReadWrite",
    "Notes.ReadWrite.All",
    "Notes.ReadWrite.CreatedByApp",

    # People/Presence
    "People.Read",
    "People.Read.All",
    "PeopleSettings.Read.All",
    "Presence.Read",
    "Presence.ReadWrite",

    # Short Notes
    "ShortNotes.Read",
    "ShortNotes.ReadWrite",

    # Sites/SharePoint
    "Sites.Manage.All",
    "Sites.Read.All",
    "Sites.ReadWrite.All",
    "Sites.Selected",
    "Sites.FullControl.All",

    # Tasks/Planner
    "Tasks.Read",
    "Tasks.Read.Shared",
    "Tasks.ReadWrite",
    "Tasks.ReadWrite.Shared",
]
```

---

## Copilot API Note

Microsoft Copilot does not currently have a public API for programmatic interaction. Users can access Copilot through:
- Microsoft 365 apps (Word, Excel, Teams, etc.)
- Copilot chat in Teams
- Windows Copilot

Future API availability would require additional permissions when released.

---

*Document created: December 4, 2025*
