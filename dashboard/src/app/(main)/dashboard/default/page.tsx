import { Activity, Brain, Clock, HeartPulse, Users, Waves } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDatasetInfo } from "@/lib/api/seed-v";

import { ChannelTopomap } from "./_components/channel-topomap";
import { TrialDurationChart } from "./_components/trial-duration-chart";

const EMOTION_STYLES: Record<string, string> = {
  Disgust: "bg-violet-500/15 text-violet-700 dark:text-violet-300 [&_span]:bg-violet-500",
  Fear: "bg-red-500/15 text-red-700 dark:text-red-300 [&_span]:bg-red-500",
  Sad: "bg-blue-500/15 text-blue-700 dark:text-blue-300 [&_span]:bg-blue-500",
  Neutral: "bg-slate-500/15 text-slate-700 dark:text-slate-300 [&_span]:bg-slate-500",
  Happy: "bg-amber-500/15 text-amber-700 dark:text-amber-300 [&_span]:bg-amber-500",
};

export default async function Page() {
  const info = await getDatasetInfo();
  const { dataset, paths, channels, label_names, trial_timestamps, scores, participants } = info;

  const emotions = Object.entries(label_names)
    .map(([idx, name]) => ({ idx, name }))
    .sort((a, b) => Number(a.idx) - Number(b.idx));

  const stats = [
    { icon: Users, label: "Subjects", value: dataset.n_subjects },
    { icon: Activity, label: "Sessions", value: dataset.n_sessions },
    { icon: Clock, label: "Trials / session", value: dataset.n_trials_per_session },
    { icon: Brain, label: "EEG channels", value: dataset.n_eeg_channels },
    { icon: Waves, label: "Sample rate", value: `${dataset.sample_rate} Hz` },
    { icon: HeartPulse, label: "Emotions", value: dataset.n_emotions },
  ];

  const sexTotal = participants.sex_counts.F + participants.sex_counts.M;
  const femalePct = Math.round((participants.sex_counts.F / sexTotal) * 100);

  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="font-semibold text-2xl tracking-tight">SEED-V Dataset Overview</h1>
        <p className="text-muted-foreground text-sm">
          {dataset.n_subjects} subjects × {dataset.n_sessions} sessions · {dataset.n_emotions}-class emotion recognition
          · {dataset.n_eeg_channels} EEG channels @ {dataset.sample_rate} Hz
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {stats.map(({ icon: Icon, label, value }) => (
          <Card key={label} className="gap-0">
            <CardContent className="flex flex-col gap-1.5">
              <div className="flex items-center gap-1.5 text-muted-foreground text-xs">
                <Icon className="size-3.5" />
                {label}
              </div>
              <span className="font-semibold text-2xl tabular-nums">{value}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Topomap + Emotions */}
      <div className="grid gap-4 md:gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Channel layout</CardTitle>
            <CardDescription>{channels.length} electrodes · 10-20 system</CardDescription>
          </CardHeader>
          <CardContent>
            <ChannelTopomap channels={channels} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Emotion labels</CardTitle>
            <CardDescription>Per-trial target class index mapping</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {emotions.map(({ idx, name }) => (
              <span
                key={idx}
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium text-sm ${EMOTION_STYLES[name] ?? "bg-muted text-muted-foreground"}`}
              >
                <span className="size-2 rounded-full" />
                {name}
                <span className="opacity-60">= {idx}</span>
              </span>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Trial durations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Trial durations</CardTitle>
          <CardDescription>
            {dataset.n_sessions * dataset.n_trials_per_session} trials across {dataset.n_sessions} sessions ·
            color-coded by session
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TrialDurationChart trials={trial_timestamps} />
        </CardContent>
      </Card>

      {/* Participants + Scores */}
      <div className="grid gap-4 md:gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Participants</CardTitle>
            <CardDescription>{participants.n} subjects</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Sex distribution</span>
                <span className="tabular-nums">
                  F {participants.sex_counts.F} · M {participants.sex_counts.M}
                </span>
              </div>
              <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
                <div className="bg-chart-1" style={{ width: `${femalePct}%` }} />
                <div className="flex-1 bg-chart-2" />
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Age range</span>
              <span className="tabular-nums">
                {participants.age_min}–{participants.age_max} years
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Self-rating scores</CardTitle>
            <CardDescription>{scores.n_rows} subject×session rows · 0–5 scale</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-muted-foreground text-xs">Mean</div>
              <div className="font-semibold text-xl tabular-nums">{scores.trial_mean.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-muted-foreground text-xs">Min</div>
              <div className="font-semibold text-xl tabular-nums">{scores.trial_min.toFixed(1)}</div>
            </div>
            <div>
              <div className="text-muted-foreground text-xs">Max</div>
              <div className="font-semibold text-xl tabular-nums">{scores.trial_max.toFixed(1)}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Paths */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Data paths</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground text-xs">Raw</span>
            <code className="block truncate rounded bg-muted px-2 py-1 font-mono text-xs">{paths.raw_dir}</code>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground text-xs">Processed</span>
            <code className="block truncate rounded bg-muted px-2 py-1 font-mono text-xs">{paths.processed_dir}</code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
