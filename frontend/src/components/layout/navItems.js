import {
  CalmIcon,
  InsightsIcon,
  JournalIcon,
  MoodIcon,
  PeopleIcon,
  SelfCareIcon,
  SettingsIcon,
  TodayIcon,
} from "../icons";

export const primaryNav = [
  { to: "/app", label: "Today", icon: TodayIcon, end: true },
  { to: "/app/mood", label: "Mood", icon: MoodIcon },
  { to: "/app/journal", label: "Journal", icon: JournalIcon },
  { to: "/app/selfcare", label: "Self-care", icon: SelfCareIcon },
  { to: "/app/people", label: "People", icon: PeopleIcon },
  { to: "/app/calm", label: "Calm", icon: CalmIcon },
  { to: "/app/insights", label: "Insights", icon: InsightsIcon },
];

export const settingsNav = {
  to: "/app/settings",
  label: "Settings",
  icon: SettingsIcon,
};

export const bottomNav = [
  { to: "/app", label: "Today", icon: TodayIcon, end: true },
  { to: "/app/mood", label: "Mood", icon: MoodIcon },
  { to: "/app/journal", label: "Journal", icon: JournalIcon },
  { to: "/app/people", label: "People", icon: PeopleIcon },
];

export const moreNav = [
  { to: "/app/selfcare", label: "Self-care", icon: SelfCareIcon },
  { to: "/app/calm", label: "Calm", icon: CalmIcon },
  { to: "/app/insights", label: "Insights", icon: InsightsIcon },
  { to: "/app/settings", label: "Settings", icon: SettingsIcon },
];
