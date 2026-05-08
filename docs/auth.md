# Authentication Protocol

BudgetWise implements session-based authentication to manage secure user sessions and protect sensitive financial data.

## Authentication Workflow

1.  **Identity Verification**: Clients transmit a `POST` request to `/api/auth/login/` with valid credentials.
2.  **Session Establishment**: Upon verification, the server issues a unique session identifier (`sessionid`) via a secure cookie.
3.  **Authorized Access**: Subsequent requests must include this session identifier to access protected resources.

## Integration Requirements

For frontend applications, it is mandatory to configure the network client with `credentials: "include"`. This ensures the browser appropriately manages and transmits session cookies.

## API Endpoints

| Endpoint | Method | Functional Description |
|----------|--------|------------------------|
| `/api/auth/login/` | `POST` | Authenticates user and initializes session |
| `/api/auth/logout/` | `POST` | Invalidates current session |
| `/api/auth/` | `POST` | User registration |
| `/api/auth/me/` | `GET` | Retrieves authenticated profile data |

### Example Payloads

**Authentication Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Registration Request:**
```json
{
  "email": "user@example.com",
  "first_name": "Firstname",
  "last_name": "Lastname",
  "password": "secure_password"
}
```

## CSRF Token Management

To simplify cross-domain integration, the backend provides the `csrf_token` in the response body for the following actions:
*   **Registration** (`POST /api/auth/`)
*   **Login** (`POST /api/auth/login/`)
*   **Get Profile** (`GET /api/auth/me/`)

### Frontend Implementation
1.  **Capture**: Extract the `csrf_token` from the response JSON.
2.  **Transmit**: Include this token in the `X-CSRFToken` header for all state-changing requests (POST, PUT, PATCH, DELETE).
3.  **Persistence**: If the page is refreshed, call `/api/auth/me/` to retrieve a fresh token along with the user profile.

## Security & Cross-Domain Controls

The application enforces Cross-Site Request Forgery (CSRF) protection for all state-changing operations. 

### Production Cookie Policy (Vercel)
When hosted on Vercel, the backend implements a strict cookie policy to support cross-domain frontend communication:
*   **SameSite=None**: Allows cookies to be sent from different frontend domains (e.g., Localhost or Vercel Frontend).
*   **Secure**: Cookies are only transmitted over HTTPS (Mandatory for Vercel).
*   **HttpOnly**: Session cookies are inaccessible to client-side scripts to prevent XSS.

> [!IMPORTANT]
> Ensure your frontend is calling the backend over **HTTPS** in production, otherwise the browser will reject the authentication cookies.
