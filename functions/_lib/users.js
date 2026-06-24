export function getUsers(env) {
  return {
    joel: {
      password: env.JOEL_PASSWORD || "changeme",
      role: "owner",
      display_name: "Joel",
    },
    valerie: {
      password: env.VALERIE_PASSWORD || "changeme",
      role: "guest",
      display_name: "Valerie",
    },
  };
}

export function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return result === 0;
}
