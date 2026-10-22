const API_BASE = "/api/v1/attendance";

const ALLOWED_SPORTS = ["boxing", "tennis", "football"];

function getToken() {
  return sessionStorage.getItem("access_token");
}

function validateSport(sport) {
  if (!ALLOWED_SPORTS.includes(sport)) {
    throw new Error("Noto'g'ri sport turi.");
  }

  return sport;
}

async function apiRequest(path, options = {}) {
  const token = getToken();

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      data ||
      `Server xatosi: ${response.status}`;

    throw new Error(
      typeof message === "string"
        ? message
        : JSON.stringify(message)
    );
  }

  return data;
}

export function getAttendanceStudents(sport, month) {
  validateSport(sport);

  return apiRequest(
    `/${sport}/?month=${encodeURIComponent(month)}`
  );
}

export function getAttendanceStudent(sport, id) {
  validateSport(sport);

  return apiRequest(`/${sport}/${encodeURIComponent(id)}/`);
}

export function getAttendanceHistory(sport, id) {
  validateSport(sport);

  return apiRequest(
    `/history/${sport}/${encodeURIComponent(id)}/`
  );
}

export function markAttendance(payload) {
  validateSport(payload.sport);

  return apiRequest("/records/", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}