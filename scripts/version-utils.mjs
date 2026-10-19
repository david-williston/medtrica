export const VERSION_TAG = /^v\d{4}\.\d{2}\.\d{2}(\.\d+)?$/;
export const TIME_ZONE = 'America/Mexico_City';
export function compareVersions(a, b) {
    const left = a.slice(1).split('.').map(Number);
    const right = b.slice(1).split('.').map(Number);
    for (let i = 0; i < Math.max(left.length, right.length); i++) {
        const difference = (left[i] ?? 0) - (right[i] ?? 0);
        if (difference) return difference;
    }
    return 0;
}
export function calendarDay(date = new Date()) {
    const parts = new Intl.DateTimeFormat('en', {
        timeZone: TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(date);
    const part = (name) => parts.find((item) => item.type === name).value;
    return `${part('year')}.${part('month')}.${part('day')}`;
}
export function nextVersion(tags, date = new Date()) {
    const base = `v${calendarDay(date)}`;
    const sameDay = tags.filter((tag) => VERSION_TAG.test(tag) && (tag === base || tag.startsWith(`${base}.`)));
    return sameDay.length ? `${base}.${Math.max(...sameDay.map((tag) => Number(tag.split('.')[3] ?? 0))) + 1}` : base;
}
