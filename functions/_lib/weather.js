const WEATHER_CODES = {
  0: "clear sky",
  1: "mostly clear",
  2: "partly cloudy",
  3: "overcast",
  45: "fog",
  48: "freezing fog",
  51: "light drizzle",
  53: "drizzle",
  55: "heavy drizzle",
  61: "light rain",
  63: "rain",
  65: "heavy rain",
  71: "light snow",
  73: "snow",
  75: "heavy snow",
  80: "rain showers",
  81: "rain showers",
  82: "violent rain showers",
  95: "thunderstorm",
  96: "thunderstorm with hail",
  99: "thunderstorm with heavy hail",
};

export async function getWeather(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&temperature_unit=fahrenheit`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("weather lookup failed");
  const data = await res.json();
  const current = data.current_weather;
  if (!current) throw new Error("no weather data returned");
  return {
    temperatureF: current.temperature,
    windSpeedMph: current.windspeed,
    condition: WEATHER_CODES[current.weathercode] || "unknown",
  };
}
