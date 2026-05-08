# Authentication Protocol

BudgetWise uses **Token-Based Authentication** for maximum simplicity and frontend compatibility. This eliminates CSRF issues and session management overhead.

## 🔑 How to Authenticate

1.  **Obtain Token**: Send your email and password to the `/api/auth/login/` endpoint.
2.  **Use Token**: Include the received token in the `Authorization` header for all subsequent requests.

### 1. Login (Obtaining the Token)
**Endpoint**: `POST /api/auth/login/`
**Body**:
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```
**Response**:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": { ... }
}
```

### 2. Authenticating Requests
Include the token in every request header:
`Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

### Example (Javascript/Axios)
```javascript
const token = "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b";

axios.get('https://budget-wise-back-end.vercel.app/api/auth/me/', {
    headers: {
        'Authorization': `Token ${token}`
    }
});
```

## 🚀 Key Advantages

*   **No CSRF**: Since we don't use cookies for authentication, CSRF protection is not required.
*   **Persistent**: The token remains valid until the user manually logs out or it is deleted from the server.
*   **Simple**: Frontend only needs to store one string (the token).

## 🛠 Developer Notes

*   **Base URL**: `https://budget-wise-back-end.vercel.app/`
*   **Testing**: You can use the "Authorize" button in Swagger and enter your token (prefix with `Token `) to test endpoints.
