export function formatWeather(raw) {
  if (!raw) return { text: '', temp: null }
  const text = raw.replace(/^[^\s]+今日天气[：:]\s*/, '')
  const tempMatch = text.match(/(\d{1,2})°/)
  return { text: text || raw, temp: tempMatch ? parseInt(tempMatch[1], 10) : null }
}

export function deriveWeatherType(conditionText) {
  if (!conditionText) return 'sunny'
  if (conditionText.includes('雪')) return 'snowy'
  if (conditionText.includes('雨')) return 'rainy'
  if (conditionText.includes('云') || conditionText.includes('阴')) return 'cloudy'
  if (conditionText.includes('晴')) return 'sunny'
  return 'sunny'
}
