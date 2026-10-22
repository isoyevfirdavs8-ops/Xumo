import { authFetch } from "../utils/auth";

const BASE = "/api/v1/hostel";

async function parseResponse(response) {
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : JSON.stringify(data || { error: "Server xatosi" });

    throw new Error(detail);
  }

  return data;
}

export async function getHostelRooms() {
  const response = await authFetch(`${BASE}/dashboard/rooms/`);
  return parseResponse(response);
}

export async function createHostelRoom(payload) {
  const response = await authFetch(`${BASE}/dashboard/rooms/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse(response);
}

export async function updateHostelRoom(id, payload) {
  const response = await authFetch(`${BASE}/dashboard/rooms/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse(response);
}

export async function uploadHostelRoomImage(id, file, isPrimary = false) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("is_primary", String(isPrimary));

  const response = await authFetch(
    `${BASE}/dashboard/rooms/${id}/images/`,
    {
      method: "POST",
      body: formData,
    }
  );

  return parseResponse(response);
}

export async function deleteHostelRoomImage(roomId, imageId) {
  const response = await authFetch(
    `${BASE}/dashboard/rooms/${roomId}/images/${imageId}/`,
    { method: "DELETE" }
  );

  return parseResponse(response);
}

export async function setPrimaryHostelRoomImage(roomId, imageId) {
  const response = await authFetch(
    `${BASE}/dashboard/rooms/${roomId}/images/${imageId}/primary/`,
    { method: "POST" }
  );

  return parseResponse(response);
}


export async function getHostelAvailability({
  checkIn,
  checkOut,
  capacity,
  signal,
}) {
  const params = new URLSearchParams({
    check_in: checkIn,
    check_out: checkOut,
  });

  if (capacity !== undefined && capacity !== null) {
    params.set("capacity", String(capacity));
  }

  const response = await fetch(
    `${BASE}/availability/?${params.toString()}`,
    { signal }
  );

  return parseResponse(response);
}

export async function createHostelBooking(
  { checkIn, checkOut, capacity, roomCount },
  idempotencyKey
) {
  if (!idempotencyKey) {
    throw new Error("Idempotency-Key majburiy.");
  }

  const response = await authFetch(`${BASE}/bookings/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({
      check_in: checkIn,
      check_out: checkOut,
      capacity: Number(capacity),
      room_count: Number(roomCount),
    }),
  });

  return parseResponse(response);
}

export async function getMyHostelBookings() {
  const response = await authFetch(`${BASE}/my-bookings/`);
  return parseResponse(response);
}

export async function getMyHostelBooking(id) {
  const response = await authFetch(
    `${BASE}/my-bookings/${encodeURIComponent(id)}/`
  );

  return parseResponse(response);
}
