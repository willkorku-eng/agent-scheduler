import dayjs from "dayjs";

export const SKILL_COLOR: Record<string, string> = {
  chat: "#3f51b5",
  email: "#ff9800",
  both: "#9c27b0",
  unknown: "#9e9e9e"
};

export function toDateTime(dateStr: string, timeStr: string) {
  return dayjs(`${dateStr}T${timeStr}`);
}

export function eventIdFor(a: any) {
  return `${a.agent_id}-${a.shift_id}-${a.date}`;
}
