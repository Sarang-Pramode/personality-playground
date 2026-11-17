import { useEffect, useMemo, useState } from "react";
import { AdminPanel } from "./components/AdminPanel";
import {
  AuthScreens,
  DeniedScreen,
  PendingScreen,
} from "./components/AuthScreens";
import { ChatPanel } from "./components/ChatPanel";
import { ConfigurePanel } from "./components/ConfigurePanel";
import { DeveloperInspector } from "./components/DeveloperInspector";
import { Header } from "./components/Header";
import { VisualizePanel } from "./components/VisualizePanel";
import {
  ApiError,
  getAuthConfig,
  getFixtures,
  getHealth,
  getMe,
  logout as apiLogout,
  previewPersonality,
  sendChat,
  type AuthUser,
} from "./lib/api";
import {
  deleteSavedProfile,
  exportProfilesJson,
  loadSavedProfiles,
  saveProfile,
} from "./lib/storage";
import {
  PRESETS,
  type ChatMessage,
  type ChatMetadata,
  type FixtureCustomer,
  type ModelInfo,
  type PresetName,
  type SavedProfile,
  type Scenario,
  type TraitKey,
  type TraitProfile,
} from "./types";

function profilesEqual(a: TraitProfile, b: TraitProfile) {
  return (Object.keys(a) as TraitKey[]).every((k) => a[k] === b[k]);
}

function detectPreset(profile: TraitProfile): PresetName | "custom" {
  for (const name of Object.keys(PRESETS) as PresetName[]) {
    if (profilesEqual(profile, PRESETS[name])) return name;
  }
  return "custom";
}

function Studio({
  user,
  onLogout,
  showAdmin,
  onToggleAdmin,
}: {
  user: AuthUser;
  onLogout: () => void;
  showAdmin: boolean;
  onToggleAdmin: () => void;
}) {
  const [profile, setProfile] = useState<TraitProfile>({ ...PRESETS.balanced });
  const [activePreset, setActivePreset] = useState<PresetName | "custom">(
    "balanced",
  );
  const [behaviorSummary, setBehaviorSummary] = useState("");
  const [previewPrompt, setPreviewPrompt] = useState("");
  const [saved, setSaved] = useState<SavedProfile[]>([]);
  const [saveName, setSaveName] = useState("");

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [provider, setProvider] = useState("demo");
  const [modelId, setModelId] = useState<string | null>("scripted-demo");
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [llmLive, setLlmLive] = useState(false);

  const [customers, setCustomers] = useState<FixtureCustomer[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [customerId, setCustomerId] = useState("customer_A");
  const [scenarioId, setScenarioId] = useState("balance_check");

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [latestMeta, setLatestMeta] = useState<ChatMetadata | null>(null);

  useEffect(() => {
    setSaved(loadSavedProfiles());
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [health, fixtures] = await Promise.all([
          getHealth(),
          getFixtures(),
        ]);
        if (cancelled) return;
        setHealthOk(true);
        setLlmLive(health.llm.any_live);
        setModels(health.models);
        setCustomers(fixtures.customers);
        setScenarios(fixtures.scenarios);
        if (fixtures.scenarios[0]) {
          setScenarioId(fixtures.scenarios[0].scenario_id);
        }
        const live =
          health.models.find((m) => m.available && m.provider !== "demo") ||
          health.models.find((m) => m.provider === "demo");
        if (live) {
          setProvider(live.provider);
          setModelId(live.model_id);
        }
      } catch {
        if (!cancelled) {
          setHealthOk(false);
          setModels([
            {
              provider: "demo",
              model_id: "scripted-demo",
              label: "Scripted demo mode (no LLM)",
              available: true,
            },
          ]);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const handle = window.setTimeout(async () => {
      try {
        const preview = await previewPersonality({
          profile,
          preset: activePreset === "custom" ? undefined : activePreset,
        });
        if (cancelled) return;
        setBehaviorSummary(preview.behavior_summary);
        setPreviewPrompt(preview.system_prompt);
      } catch {
        if (!cancelled) {
          setBehaviorSummary(
            "Could not reach /api/personality/preview — check auth/backend.",
          );
        }
      }
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [profile, activePreset]);

  const modeInfo = useMemo(() => {
    if (!latestMeta)
      return { label: null as string | null, tone: "neutral" as const };
    if (latestMeta.mode === "scripted_demo")
      return { label: "Scripted demo mode", tone: "warn" as const };
    if (latestMeta.mode === "error")
      return { label: "LLM error", tone: "danger" as const };
    return { label: latestMeta.model_label || "Live", tone: "ok" as const };
  }, [latestMeta]);

  function onTraitChange(key: TraitKey, value: number) {
    setProfile((prev) => {
      const next = { ...prev, [key]: value };
      setActivePreset(detectPreset(next));
      return next;
    });
  }

  function onPreset(name: PresetName) {
    setProfile({ ...PRESETS[name] });
    setActivePreset(name);
  }

  async function onSend() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((m) => [...m, userMsg]);
    try {
      const res = await sendChat({
        message: text,
        customer_id: customerId,
        scenario_id: scenarioId,
        session_id: sessionId,
        personality: profile,
        preset: activePreset === "custom" ? null : activePreset,
        provider,
        model_id: modelId,
      });
      setSessionId(res.session_id);
      setLatestMeta(res.metadata);
      setMessages((m) => [
        ...m,
        {
          id: res.run_id,
          role: "assistant",
          content: res.reply,
          metadata: res.metadata,
        },
      ]);
      if (res.error) {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "system",
            content: res.error || "LLM unavailable",
          },
        ]);
      }
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "system",
          content:
            err instanceof Error
              ? err.message
              : "Chat request failed — check backend.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onReset() {
    setMessages([]);
    setSessionId(null);
    setLatestMeta(null);
  }

  return (
    <div className="flex min-h-full flex-col">
      <Header
        models={models}
        provider={provider}
        modelId={modelId}
        onProviderChange={(p, m) => {
          setProvider(p);
          setModelId(m);
        }}
        healthOk={healthOk}
        llmLive={llmLive}
        user={user}
        onLogout={onLogout}
        showAdminToggle={user.role === "admin"}
        adminOpen={showAdmin}
        onToggleAdmin={onToggleAdmin}
      />

      {showAdmin && user.role === "admin" ? (
        <div className="mx-auto w-full max-w-[1600px] p-3">
          <AdminPanel />
        </div>
      ) : (
        <>
          <main className="mx-auto grid w-full max-w-[1600px] flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[27%_32%_41%]">
            <ConfigurePanel
              profile={profile}
              activePreset={activePreset}
              saved={saved}
              saveName={saveName}
              onSaveNameChange={setSaveName}
              onTraitChange={onTraitChange}
              onPreset={onPreset}
              onSave={() => {
                const next = saveProfile(
                  saveName.trim(),
                  profile,
                  activePreset,
                );
                setSaved(next);
                setSaveName("");
              }}
              onLoad={(id) => {
                const found = saved.find((p) => p.id === id);
                if (!found) return;
                setProfile({ ...found.profile });
                setActivePreset(found.preset);
              }}
              onDelete={(id) => setSaved(deleteSavedProfile(id))}
              onExport={() => {
                const blob = new Blob([exportProfilesJson(saved)], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "personality-profiles.json";
                a.click();
                URL.revokeObjectURL(url);
              }}
            />
            <VisualizePanel
              profile={profile}
              behaviorSummary={behaviorSummary}
            />
            <ChatPanel
              customers={customers}
              scenarios={scenarios}
              customerId={customerId}
              scenarioId={scenarioId}
              messages={messages}
              input={input}
              busy={busy}
              modeLabel={modeInfo.label}
              modeTone={modeInfo.tone}
              onCustomerChange={(id) => {
                setCustomerId(id);
                onReset();
              }}
              onScenarioChange={setScenarioId}
              onInputChange={setInput}
              onSend={onSend}
              onReset={onReset}
              onUseSuggested={() => {
                const s = scenarios.find((x) => x.scenario_id === scenarioId);
                if (s) setInput(s.suggested_prompt);
              }}
            />
          </main>
          <div className="mx-auto w-full max-w-[1600px] px-3 pb-4">
            <DeveloperInspector
              latest={latestMeta}
              previewPrompt={previewPrompt}
            />
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [boot, setBoot] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [me, cfg] = await Promise.all([getMe(), getAuthConfig()]);
        if (cancelled) return;
        setGoogleEnabled(cfg.google_oauth);
        setUser(me.authenticated ? me.user : null);
      } catch (err) {
        if (!cancelled) {
          setBootError(
            err instanceof ApiError
              ? err.detail
              : "Could not reach auth API",
          );
        }
      } finally {
        if (!cancelled) setBoot(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleLogout() {
    try {
      await apiLogout();
    } catch {
      /* ignore */
    }
    setUser(null);
    setShowAdmin(false);
  }

  if (boot) {
    return (
      <div className="flex min-h-full items-center justify-center text-sm text-slate-500">
        Loading…
      </div>
    );
  }

  if (bootError) {
    return (
      <div className="flex min-h-full items-center justify-center px-4 text-sm text-red-700">
        {bootError}
      </div>
    );
  }

  if (!user) {
    return (
      <AuthScreens
        googleEnabled={googleEnabled}
        onAuthed={(u) => setUser(u)}
      />
    );
  }

  if (user.status === "pending") {
    return <PendingScreen user={user} onLogout={() => void handleLogout()} />;
  }

  if (user.status === "denied" || user.status === "revoked") {
    return <DeniedScreen user={user} onLogout={() => void handleLogout()} />;
  }

  return (
    <Studio
      user={user}
      onLogout={() => void handleLogout()}
      showAdmin={showAdmin}
      onToggleAdmin={() => setShowAdmin((v) => !v)}
    />
  );
}
