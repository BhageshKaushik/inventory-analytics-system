"""
user_manager.py
===============
Handles user accounts, authentication, and role-based access control (RBAC).

Design decisions
----------------
* Passwords are stored as SHA-256 hashes — never in plain text.
* All credentials live in an in-memory dict (no database or file I/O).
* Two roles are defined: "manager" and "junior_manager".
* A single global session is tracked via _current_user.
* `require_role()` can be called at the top of any restricted function to
  enforce access control — raises PermissionError on failure.
"""

import hashlib


# ── Role constants ────────────────────────────────────────────────────────────
ROLE_MANAGER        = "manager"
ROLE_JUNIOR_MANAGER = "junior_manager"

# Operations each role is allowed to perform
PERMISSIONS = {
    ROLE_MANAGER: {
        "add_order", "edit_order", "delete_order",
        "search_orders", "sort_orders",
        "view_all_orders", "analytics", "view_charts",
    },
    ROLE_JUNIOR_MANAGER: {
        "search_orders", "sort_orders",
        "view_all_orders", "analytics",
    },
}


class User:
    """
    Represents an authenticated system user.

    Attributes
    ----------
    username : str
    role     : str  — ROLE_MANAGER or ROLE_JUNIOR_MANAGER
    """

    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role

    def __str__(self):
        return f"User(username={self.username!r}, role={self.role!r})"

    def can(self, operation: str) -> bool:
        """Return True if this user's role permits the given operation."""
        return operation in PERMISSIONS.get(self.role, set())


class UserManager:
    """
    Manages user accounts and the current login session.

    Internal storage
    ----------------
    _users : dict
        {
          username: {
              "password_hash": str,   # SHA-256 hex digest
              "role": str
          }
        }
    _current_user : User | None   — the currently logged-in user
    """

    def __init__(self):
        self._users = {}
        self._current_user = None

        # Seed default accounts so the project works out of the box
        self._seed_default_users()

    # ──────────────────────────────────────────────────────────────────────
    # Seeding
    # ──────────────────────────────────────────────────────────────────────

    def _seed_default_users(self):
        """Create default accounts for demonstration."""
        self.create_user("admin",  "manager123", ROLE_MANAGER)
        self.create_user("junior", "junior123",  ROLE_JUNIOR_MANAGER)

    # ──────────────────────────────────────────────────────────────────────
    # User management
    # ──────────────────────────────────────────────────────────────────────

    def create_user(self, username: str, password: str, role: str) -> bool:
        """
        Create a new user account.

        Parameters
        ----------
        username : str
        password : str  — stored as SHA-256 hash
        role     : str  — must be ROLE_MANAGER or ROLE_JUNIOR_MANAGER

        Returns True on success, False if username already exists or role
        is invalid.
        """
        username = username.strip().lower()

        if not username or not password:
            print("[UserManager] Username and password cannot be empty.")
            return False

        if role not in (ROLE_MANAGER, ROLE_JUNIOR_MANAGER):
            print(f"[UserManager] Invalid role: {role!r}. "
                  f"Choose '{ROLE_MANAGER}' or '{ROLE_JUNIOR_MANAGER}'.")
            return False

        if username in self._users:
            print(f"[UserManager] Username '{username}' already exists.")
            return False

        self._users[username] = {
            "password_hash": self._hash(password),
            "role": role,
        }
        return True

    def delete_user(self, username: str) -> bool:
        """Remove a user account. Returns True on success."""
        username = username.strip().lower()
        if username not in self._users:
            print(f"[UserManager] User '{username}' not found.")
            return False
        del self._users[username]
        return True

    def list_users(self) -> list:
        """Return a list of (username, role) tuples."""
        return [(uname, info["role"]) for uname, info in self._users.items()]

    # ──────────────────────────────────────────────────────────────────────
    # Authentication
    # ──────────────────────────────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> bool:
        """
        Verify credentials WITHOUT starting a session.
        Returns True if username + password match.
        """
        username = username.strip().lower()
        record = self._users.get(username)
        if record is None:
            return False
        return record["password_hash"] == self._hash(password)

    def login(self, username: str, password: str) -> User | None:
        """
        Authenticate and start a session.

        Returns the User object on success, or None on failure.
        Only one user can be logged in at a time.
        """
        if self._current_user is not None:
            print(f"[UserManager] Already logged in as "
                  f"'{self._current_user.username}'. Please logout first.")
            return None

        username = username.strip().lower()
        if not self.authenticate(username, password):
            return None

        role = self._users[username]["role"]
        self._current_user = User(username, role)
        return self._current_user

    def logout(self):
        """End the current session."""
        if self._current_user:
            uname = self._current_user.username
            self._current_user = None
            print(f"[UserManager] '{uname}' has been logged out.")
        else:
            print("[UserManager] No user is currently logged in.")

    def get_current_user(self) -> User | None:
        """Return the currently logged-in User, or None."""
        return self._current_user

    def is_logged_in(self) -> bool:
        """Return True if a user is currently logged in."""
        return self._current_user is not None

    # ──────────────────────────────────────────────────────────────────────
    # Access control
    # ──────────────────────────────────────────────────────────────────────

    def require_role(self, operation: str):
        """
        Check that the current user is allowed to perform `operation`.

        Raises
        ------
        PermissionError  — if not logged in or role lacks the permission.

        Usage
        -----
            user_manager.require_role("add_order")
        """
        if self._current_user is None:
            raise PermissionError("You must be logged in to perform this action.")

        if not self._current_user.can(operation):
            raise PermissionError(
                f"Access Denied: your role ('{self._current_user.role}') "
                f"does not have permission to perform '{operation}'."
            )

    def check_permission(self, operation: str) -> bool:
        """
        Silent version of require_role — returns True/False instead of
        raising.  Useful for conditionally showing menu options.
        """
        if self._current_user is None:
            return False
        return self._current_user.can(operation)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(password: str) -> str:
        """Return the SHA-256 hex digest of a password string."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
