# Dementia Care API - SIH 2026
* **URL:**
  * Online Server: (Available 24/7, Temporary Memory) <br>
    https://dementia-care-yne7.onrender.com
  * Local Server: (Running from my machine, Permanent Memory) <br>
    https://blazer-roaming-sapling.ngrok-free.dev/
* **Documentation:** https://dementia-care-yne7.onrender.com/docs  
  *(`/docs` provides you with access to endpoints directly in the browser. You can test out the server there to get an idea about JSON strings.)*
  <br>
* **Miscellaneous:**
  * [SIH Official PPT Link - **DO NOT SHARE**](https://1drv.ms/p/c/c3d52faaccdd0da3/IQCOI5O-pVHQSIkZ9-ftQqmwAaxSdVtsL0JXLOyf1YbGNxA?e=rZJXHc)
  * [Notion Link](https://silly-hail-f25.notion.site/SIH-2026-3c8b1ece5c6880fb9088f338a17a3a51?source=copy_link)
  * [Hosting Site Dashboard](https://dashboard.render.com/)

---

### 🚨 Found a bug?
Report all minor bugs, tweaks, unintentional behaviour, grammatical errors. <br>
If you see a **500 Internal Server Error**, or any error starting with **5**, please message me since it indicates a server-side issue. Send me:
1. **The endpoint**
2. **The JSON body**
3. **The error message**


---

### Free server limitations:
* The first request takes 30–50 seconds to wake up the server, according to the website.
* The server will automatically reset after 15 minutes of inactivity. If you want to permanently store some data, let me know. I will manually place it in the database.
* Why it's online: So the API is accessible without you having to download this repo and set up the virtual environment for it.
* The local server stores data, but only available when my computer is running and connected to internet. Data will be available to the Online Server on the next commit.
---

<br>

# Endpoints & Schemas

### `GET /`
To verify if the server is awake and responding.
* **Parameters:** None
* **Success:** `200_OK`

---

### `POST /api/auth/register`
Registers a new user account across any role (`PATIENT`, `DOCTOR`, or `ADMIN`).
* **Parameters:** None
   <br> *(will require admin account to access in future)*
* **Success:** `201_CREATED`
* **Client Errors:** 
  * `HTTP_409_CONFLICT`: EMAIL_ALREADY_EXISTS
  * `422_UNPROCESSABLE_CONTENT`: ASSIGNED_DOCTOR_NOT_FOUND 

**JSON Body:**
* `email` *(string, required)*: Must be unique.
* `password` *(string, required)*: Plain text password. Simple strings allowed for testing.
* `role` *(string, required)*: `PATIENT`, `DOCTOR`, or `ADMIN`.
* `full_name` *(string, required)*: Display name.
* `specialization` *(string, optional)*: Used only when role is `DOCTOR`.
* `stage_of_care` *(string, required for patients)*: `MILD`, `MODERATE`, or `SEVERE`.
* `assigned_doctor_id` *(integer, optional)*: Must match a valid doctor's `user_id`.

**Example:**
``` json
{
  "email": "patient1@gmail.com",
  "password": "qwerty123",
  "role": "PATIENT",
  "full_name": "John Denver",
  "stage_of_care": "MILD",
  "assigned_doctor_id": 1
} 
```

---
<br>

# Database Schema

Might change if I find some fields unnecessary. However, I have begun to use some of them so there is little chance the following tables will change now:
 - Users
 - Doctor Profiles
 - Patient Profiles

```mermaid
flowchart TB
    %% Modern Slate & Teal Palette with High Contrast
    classDef root fill:#1e293b,stroke:#38bdf8,stroke-width:2.5px,color:#f8fafc;
    classDef profiles fill:#042f2e,stroke:#2dd4bf,stroke-width:2px,color:#f0fdfa;
    classDef features fill:#2e1065,stroke:#c084fc,stroke-width:2px,color:#faf5ff;
    classDef configs fill:#1c1917,stroke:#fbbf24,stroke-width:2px,color:#fffbeb;

    U["<b>USERS</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>📧 username / email<br/>🔒 hashed_password<br/>🏷️ role<br/><i>(ADMIN / DOCTOR / PATIENT)</i><br/>⚡ is_active"]:::root

    D["<b>DOCTOR PROFILES</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🔗 user_id (FK)<br/>👤 full_name<br/>🩺 specialization"]:::profiles

    P["<b>PATIENT PROFILES</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🔗 user_id (FK)<br/>👤 full_name<br/>📊 stage_of_care<br/><i>(MILD / MOD / SEVERE)</i><br/>🔗 assigned_doctor_id (FK)"]:::profiles

    GS["<b>GAME SESSIONS</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🔗 patient_id (FK)<br/>🔗 game_id (FK)<br/>📦 session_data<br/>📅 session_date"]:::features

    GT["<b>GAME TYPES</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🏷️ name / code<br/>⚙️ schema_config<br/>⚡ is_active"]:::configs

    PR["<b>PATIENT REMINDERS</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🔗 patient_id (FK)<br/>🔗 template_id (FK)<br/>⏰ custom_time"]:::features

    RT["<b>REMINDER TEMPLATES</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>📝 title / task<br/>⏰ default_time<br/>⚡ is_active"]:::configs

    RL["<b>REMINDER LOGS</b><br/>━━━━━━━━━━━━━<br/>🔑 id (PK)<br/>🔗 reminder_id (FK)<br/>📅 log_date<br/>✅ is_done"]:::features

    %% Flow Arrows
    U -->|1:1 per role| D
    U -->|1:1 per role| P
    D -->|1:N Assigns| P

    P -->|1:N Plays| GS
    GT -->|1:N Defines| GS

    P -->|1:N Schedules| PR
    RT -->|1:N Template| PR
    PR -->|1:N Logs| RL
```
---

