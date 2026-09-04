# NER_Chetna API - SIH 2026
* **URL:**
  * Online Server: https://dementia-care-yne7.onrender.com
  * Local Server: https://blazer-roaming-sapling.ngrok-free.dev/
  * *(Online Server resets after 15 mins of inactivity, to store data permanently, use Local Server which runs from directly from my machine, but is running only when my computer is awake.)*
* **Documentation:**
  * Online Server: https://dementia-care-yne7.onrender.com/docs
  * Local Server:  https://blazer-roaming-sapling.ngrok-free.dev/docs
  * *(`/docs` provides you with access to endpoints directly in the browser. You can test out the server there to get an idea about JSON strings. Access token can be pasted on the top-right (Padlock Symbol) after login.)*
  <br>
* **Miscellaneous:**
  * [SIH PPT Link - **DO NOT SHARE, ANYONE CAN EDIT**](https://1drv.ms/p/c/c3d52faaccdd0da3/IQCOI5O-pVHQSIkZ9-ftQqmwAaxSdVtsL0JXLOyf1YbGNxA?e=rZJXHc)
  * [Notion Link](https://silly-hail-f25.notion.site/SIH-2026-3c8b1ece5c6880fb9088f338a17a3a51?source=copy_link)
  * [Hosting Site Dashboard](https://dashboard.render.com/)

---

### 🚨 Found a bug?
*Please report all minor bugs, tweaks, unintentional behaviour, grammatical errors.* <br>
If you see a **500 Internal Server Error**, or any error starting with **5**, please message me since it indicates a server-side issue. Send me:
1. **The endpoint**
2. **The JSON body**
3. **The error message**


---

### Online server limitations:
* The first request takes 30–50 seconds to wake up the server, according to the website.
* The server will automatically reset after 15 minutes of inactivity. If you want to permanently store some data, let me know. I will manually place it in the database.
* Why it's online: So the API is accessible without you having to download this repo and set up the virtual environment for it.
* The local server can store data, but requires my computer is awake and logged in. I will keep it online as much as possible. Data will be available to the Online Server on the next commit.
---

<br>

# Endpoints

## GET ENDPOINTS

### `GET /`
Health check endpoint to verify server status. 
* **Access**: `PUBLIC` *(All users)*.
* **Success**: `200 OK`
* **Client Errors**: None.

---

### `GET /self`
Retrieves account details for the current user.
* **Access**: `ADMIN`, `DOCTOR`or `PATIENT` *(Authenticated users only)*
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing, expired, or invalid bearer token.

---

### `GET /users`
Retrieves a list of all registered users. *(Filters: user_id, role)*
* **Access**: `ADMIN`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: User does not possess ADMIN privileges.

---

### `GET /reminders`
Retrieves all reminders from all patients. *(Filters: patient_id, reminder_id)*
* **Access**: `ADMIN`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: User does not possess ADMIN privileges.

---

### `GET /self/reminders`
Retrieves all reminders for the calling patient. *(Filters: reminder_id)*
* **Access**: `PATIENT`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller is not a registered PATIENT.

---

### `GET /self/patients`
Lists all patients actively assigned under the calling doctor. *(Filters: patient_id)*
* **Access**: `DOCTOR`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller does not hold a DOCTOR profile.

---

### `GET /self/patients/{patient_id}/reminders`
Retrieves all reminders for a specific patient assigned under the calling doctor. *(Filters: reminder_id)*
* **Access**: `DOCTOR`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller does not hold a DOCTOR profile.
  * `404 NOT FOUND`: Target patient_id does not exist, or the patient is not assigned under this doctor.

---

## POST ENDPOINTS

### `POST /login`
Creates an active session key for your account.
* **Access**: `Public`
* **Success**: `200 OK`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Invalid email or incorrect password.

---

### `POST /users`
Creates a new user profile.
* **Access**: `ADMIN`
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: User does not possess ADMIN privileges.
  * `409 CONFLICT`: A user with this email or username already exists.

---

### `POST /reminders`
Creates a reminder record for any specified user. *(Pooled Data)*
* **Access**: `ADMIN`
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: User does not possess ADMIN privileges.
  * `404 NOT FOUND`: Specified target user_id does not exist.

---

### `POST /assign`
Assigns the patient under the doctor's supervision. 
* **Access**: `ADMIN`, `DOCTOR`
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Doctor can only assign patients to themselves.
  * `404 NOT FOUND`: Target doctor_id or patient_id does not exist.
  * `409 CONFLCT`: The patient is already assigned to the doctor.

---

### `POST /self/reminders`
Creates a new reminder for the calling patient. *(Pooled Data)*
* **Access**: `PATIENT`
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller is not a registered PATIENT.

---

### `POST /self/patients`
Creates a new patient profile and automatically binds their care assignment to the calling doctor.
* **Access**: `DOCTOR`
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller is not authorized as a DOCTOR.
  * `409 CONFLICT`: Patient record already exists.

---

### `POST /self/{patient_id}/reminder`
Schedules a new reminder for a specific patient under the doctor's supervision. *(Pooled Data)*
* **Access**: `DOCTOR` 
* **Success**: `201 CREATED`
* **Client Errors**:
  * `401 UNAUTHORIZED`: Missing or invalid authentication token.
  * `403 FORBIDDEN`: Caller does not hold a DOCTOR profile.
  * `404 NOT FOUND`: Target patient_id does not exist, or the patient is not assigned under this doctor.

---

## PATCH ENDPOINTS

## DELETE ENDPOINTS























