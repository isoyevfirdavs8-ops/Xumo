const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// Backenddagi haqiqiy refresh URL bilan mos bo‘lishi kerak.
const REFRESH_URL = "/api/v1/auth/token/refresh/";

let refreshPromise = null;

export function getAccessToken() {
  return sessionStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return sessionStorage.getItem(REFRESH_KEY);
}
export function hasSession() {
  return Boolean(getRefreshToken());
}

export function saveTokens(data) {
  if (data.access) {
    sessionStorage.setItem(ACCESS_KEY, data.access);
  }

  if (data.refresh) {
    sessionStorage.setItem(REFRESH_KEY, data.refresh);
  }

  window.dispatchEvent(new Event("auth-changed"));
}

export function clearTokens() {
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);

  window.dispatchEvent(new Event("auth-changed"));
}

function isTokenExpired(token) {
  if (!token) return true;

  try {
    const payload = JSON.parse(
      atob(
        token.split(".")[1]
          .replace(/-/g, "+")
          .replace(/_/g, "/")
      )
    );

    if (typeof payload.exp !== "number") {
      return true;
    }

    return Date.now() >= (payload.exp - 30) * 1000;
  } catch {
    return true;
  }
}

export async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const refresh = getRefreshToken();

    if (!refresh) {
      return null;
    }

    const response = await fetch(REFRESH_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearTokens();
      }

      return null;
    }

    const data = await response.json();

    if (!data.access) {
      return null;
    }

    saveTokens(data);

    return data.access;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function getValidAccessToken() {
  const access = getAccessToken();

  if (access && !isTokenExpired(access)) {
    return access;
  }

  return refreshAccessToken();
}

export async function authFetch(url, options = {}) {
  const token = await getValidAccessToken();

  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status !== 401 || !getRefreshToken()) {
    return response;
  }

  const newToken = await refreshAccessToken();

  if (!newToken) {
    return response;
  }

  headers.set("Authorization", `Bearer ${newToken}`);

  return fetch(url, {
    ...options,
    headers,
  });
}