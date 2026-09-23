'use strict';

const el = id => document.getElementById(id);
const controls = { city: el('city-select'), period: el('period-select'), sort: el('sort-select'), refresh: el('refresh-button') };
let snapshot = null;
let selectedCity = '';
let selectedStart = '';
const dateTime = new Intl.DateTimeFormat('zh-TW', { timeZone:'Asia/Taipei', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hourCycle:'h23' });
const numeric = value => typeof value === 'number' && Number.isFinite(value);
const number = value => numeric(value) ? String(value) : '—';
const formatDate = value => {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? '時間未提供' : dateTime.format(date);
};
const periodLabel = row => `${formatDate(row.start)} — ${formatDate(row.end)}`;
const weatherIcon = weather => /雨|雷/.test(weather || '') ? '☂' : /晴/.test(weather || '') ? '☀' : '☁';
const cities = () => [...new Set(snapshot.rows.map(row => row.city))];
const cityRows = () => snapshot.rows.filter(row => row.city === selectedCity).sort((a,b) => a.start.localeCompare(b.start));
const create = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
};

function validateSnapshot(data) {
  if (!data || !['demo','cwa'].includes(data.source) || !Array.isArray(data.rows) || data.rows.length === 0) throw new Error('無法使用這份預報資料。');
  for (const row of data.rows) {
    if (typeof row.city !== 'string' || !row.city || !Number.isFinite(Date.parse(row.start)) || !Number.isFinite(Date.parse(row.end)) || Date.parse(row.end) <= Date.parse(row.start)) throw new Error('預報資料的格式不完整。');
  }
  return data;
}

function renderStatus() {
  const demo = snapshot.source === 'demo';
  const stale = Math.max(...snapshot.rows.map(row => Date.parse(row.end))) <= Date.now();
  el('source-label').textContent = demo ? '示範資料' : stale ? '已過期的氣象署預報' : '中央氣象署預報';
  el('updated-at').textContent = `${demo ? '示範資料建立' : '資料擷取'}：${formatDate(snapshot.fetched_at)}`;
  const notice = el('data-notice');
  notice.className = demo ? 'notice' : stale ? 'notice stale' : 'notice live';
  notice.textContent = demo
    ? '目前使用合成示範資料，並非即時天氣預報。介面可切換 22 縣市與各預報時段。'
    : stale ? '此份預報的時段已全部結束。下方保留最後一次資料，等待下一次更新。'
      : '顯示中央氣象署最近發布的 36 小時預報。溫度為各預報時段的範圍，非即時觀測值。';
  el('detail-source').textContent = demo ? '離線示範（合成資料）' : '中央氣象署 API';
  el('detail-updated').textContent = formatDate(snapshot.fetched_at);
  const history = el('history-list'); history.replaceChildren();
  const records = Array.isArray(snapshot.history) ? snapshot.history.slice(0,5) : [];
  if (records.length) {
    history.append(create('p','最近更新紀錄'));
    records.forEach(item => history.append(create('p',`${formatDate(item.fetched_at)} · ${item.source === 'cwa' ? '中央氣象署' : '示範資料'} · ${number(item.row_count)} 筆預報`)));
  }
}

function renderControls() {
  const options = cities();
  if (!options.includes(selectedCity)) selectedCity = options.includes('臺北市') ? '臺北市' : options[0];
  controls.city.replaceChildren(...options.map(city => new Option(city, city, false, city === selectedCity)));
  const rows = cityRows();
  if (!rows.some(row => row.start === selectedStart)) selectedStart = (rows.find(row => Date.parse(row.end) > Date.now()) || rows[0]).start;
  controls.period.replaceChildren(...rows.map(row => new Option(periodLabel(row), row.start, false, row.start === selectedStart)));
  controls.city.disabled = false; controls.period.disabled = false;
}

function renderForecast() {
  const rows = cityRows();
  const selected = rows.find(row => row.start === selectedStart) || rows[0];
  el('city-name').textContent = selectedCity;
  el('weather-icon').textContent = weatherIcon(selected.weather);
  el('weather-description').textContent = selected.weather || '天氣概況未提供';
  el('period-caption').textContent = periodLabel(selected);
  el('min-temp').textContent = number(selected.min_temp);
  el('max-temp').textContent = number(selected.max_temp);
  el('comfort').textContent = selected.comfort || '舒適度資料未提供';
  el('rain-value').textContent = number(selected.rain_probability);
  el('rain-fill').style.width = `${numeric(selected.rain_probability) ? Math.min(100,Math.max(0,selected.rain_probability)) : 0}%`;
  const cards = el('period-cards'); cards.replaceChildren();
  rows.forEach(row => {
    const button = create('button', undefined, 'period-card'); button.type = 'button';
    button.setAttribute('aria-pressed', String(row.start === selected.start));
    button.setAttribute('aria-label',`${selectedCity} ${periodLabel(row)}：${row.weather || '天氣未提供'}，${number(row.min_temp)} 到 ${number(row.max_temp)} 度，降雨機率 ${number(row.rain_probability)}%`);
    button.append(create('p', periodLabel(row), 'card-time'));
    const weather = create('p', undefined, 'card-weather');
    const icon = create('span', weatherIcon(row.weather)); icon.setAttribute('aria-hidden','true');
    weather.append(icon, document.createTextNode(row.weather || '概況未提供'));button.append(weather);
    const metrics = create('div', undefined, 'card-metrics');
    metrics.append(create('span',`${number(row.min_temp)}–${number(row.max_temp)}°C`,'card-temp'), create('span',`降雨 ${number(row.rain_probability)}%`,'card-rain'));button.append(metrics);
    button.addEventListener('click',() => { selectedStart = row.start; controls.period.value = selectedStart; renderForecast(); renderComparison(); });
    cards.append(button);
  });
}

function renderComparison() {
  const selected = cityRows().find(row => row.start === selectedStart) || cityRows()[0];
  el('comparison-time').textContent = periodLabel(selected);
  const rows = snapshot.rows.filter(row => row.start === selected.start && row.end === selected.end);
  const sort = controls.sort.value;
  rows.sort((a,b) => sort === 'name' ? a.city.localeCompare(b.city,'zh-Hant') : (numeric(b[sort === 'rain' ? 'rain_probability' : 'max_temp']) ? b[sort === 'rain' ? 'rain_probability' : 'max_temp'] : -Infinity) - (numeric(a[sort === 'rain' ? 'rain_probability' : 'max_temp']) ? a[sort === 'rain' ? 'rain_probability' : 'max_temp'] : -Infinity) || a.city.localeCompare(b.city,'zh-Hant'));
  const body = el('comparison-body'); body.replaceChildren();
  rows.forEach(row => {
    const tr = create('tr'); if(row.city === selectedCity) tr.className = 'selected';
    const cityCell = create('td'); const button = create('button',row.city);button.type='button';
    button.addEventListener('click',() => { selectedCity=row.city;renderControls();renderForecast();renderComparison();el('city-name').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto':'smooth',block:'center'}); });cityCell.append(button);tr.append(cityCell);
    tr.append(create('td',row.weather || '未提供'),create('td',`${number(row.min_temp)}°C`),create('td',`${number(row.max_temp)}°C`));
    const rain = create('td');const rainWrapper = create('div',undefined,'table-rain');rainWrapper.append(create('span',`${number(row.rain_probability)}%`));
    const track = create('span',undefined,'table-rain-track');track.setAttribute('aria-hidden','true');const fill=create('span');fill.style.width=`${numeric(row.rain_probability) ? Math.min(100,Math.max(0,row.rain_probability)) : 0}%`;track.append(fill);rainWrapper.append(track);rain.append(rainWrapper);tr.append(rain);body.append(tr);
  });
}

async function loadData() {
  controls.refresh.disabled = true;
  controls.refresh.textContent = '讀取中…';
  el('error-message').hidden = true;
  try {
    const response = await fetch(`data/forecast.json?v=${Date.now()}`, { cache:'no-store' });
    if (!response.ok) throw new Error('讀取預報失敗，請稍後再試。');
    snapshot = validateSnapshot(await response.json());
    renderStatus();renderControls();renderForecast();renderComparison();
    el('forecast-content').hidden = false;
  } catch {
    el('error-message').textContent = snapshot ? '無法讀取最新版本，仍顯示先前載入的資料。' : '目前無法讀取預報資料，請檢查連線後按「重新讀取」。';
    el('error-message').hidden = false;
    if (!snapshot) {el('data-notice').textContent='預報資料尚未載入。';el('source-label').textContent='資料無法讀取';}
  } finally {
    controls.refresh.disabled=false;controls.refresh.textContent='重新讀取 ↻';
  }
}
controls.city.addEventListener('change',() => {selectedCity=controls.city.value;renderControls();renderForecast();renderComparison();});
controls.period.addEventListener('change',() => {selectedStart=controls.period.value;renderForecast();renderComparison();});
controls.sort.addEventListener('change',() => {if(snapshot)renderComparison();});
controls.refresh.addEventListener('click',loadData);
loadData();
