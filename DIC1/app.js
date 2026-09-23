'use strict';

// 待補資料集中在這裡。空字串會保留頁面上的「待補充」，不會產生假資料。
const PROFILE = {
  name: 'Sam Wei',
  department: '',
  bio: '',
  focus: 'DFT · Hardware Security',
  contact: '',
};

for (const [field, value] of Object.entries(PROFILE)) {
  const element = document.getElementById(`profile-${field}`);
  if (element && value.trim()) {
    element.textContent = value;
    element.classList.remove('pending');
  }
}

const clock = document.getElementById('live-clock');
const dateLabel = document.getElementById('clock-date');
const period = document.getElementById('clock-period');
const zoneLabel = document.getElementById('time-zone');
const greeting = document.getElementById('greeting');
const message = document.getElementById('clock-message');
const formatButtons = [...document.querySelectorAll('[data-format]')];
const storageKey = 'sam-wei-dic1-clock-format';
let format = '24';
let messageTimer;

try {
  const stored = localStorage.getItem(storageKey);
  if (stored === '12' || stored === '24') format = stored;
} catch {
  // 無痕模式或停用儲存時，時鐘仍可正常運作。
}

const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local time';
zoneLabel.textContent = zone.replaceAll('_', ' ');
const dateFormatter = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit', month: 'short', year: 'numeric',
});
const pad = number => String(number).padStart(2, '0');

function updateClock(now = new Date()) {
  const hours = now.getHours();
  const displayHours = format === '12' ? (hours % 12 || 12) : hours;
  clock.textContent = `${pad(displayHours)}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  clock.dateTime = now.toISOString();
  period.textContent = format === '12' ? (hours < 12 ? 'AM' : 'PM') : '';
  dateLabel.textContent = dateFormatter.format(now).toUpperCase();
  greeting.textContent = hours < 12 ? 'Good morning.'
    : hours < 18 ? 'Good afternoon.'
      : 'Good evening.';
  document.getElementById('year').textContent = String(now.getFullYear());
}

function updateFormat() {
  formatButtons.forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.format === format));
  });
  updateClock();
}

formatButtons.forEach(button => {
  button.addEventListener('click', () => {
    format = button.dataset.format;
    try { localStorage.setItem(storageKey, format); } catch { /* Preference is optional. */ }
    updateFormat();
  });
});

function localTimestamp(now) {
  const offset = -now.getTimezoneOffset();
  const sign = offset >= 0 ? '+' : '-';
  const absolute = Math.abs(offset);
  const utcOffset = `${sign}${pad(Math.floor(absolute / 60))}:${pad(absolute % 60)}`;
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}${utcOffset} [${zone}]`;
}

document.getElementById('copy-time').addEventListener('click', async () => {
  const text = localTimestamp(new Date());
  clearTimeout(messageTimer);
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(text);
    message.textContent = '已複製此刻時間。';
  } catch {
    // 不假報成功；權限不足時提供可選取的文字。
    message.textContent = `無法自動複製，請選取：${text}`;
  }
  messageTimer = setTimeout(() => { message.textContent = ''; }, 12000);
});

updateFormat();
setInterval(updateClock, 1000);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) updateClock();
});
