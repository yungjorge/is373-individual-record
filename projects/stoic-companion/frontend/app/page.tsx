"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import {
  ArrowUp,
  ArrowUpRight,
  BookOpen,
  Bookmark,
  Check,
  ChevronDown,
  Copy,
  Feather,
  Library,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Sun,
  Trash2,
  X,
  PanelLeftClose,
  LoaderCircle,
  LogIn,
} from "lucide-react";
import { Button } from "@/components/ui/button";

type Citation = {
  passage_id: string;
  quote_text: string;
  surrounding_passage: string;
  author: string;
  title: string;
  translator: string;
  edition: string;
  reference: string;
  source_url: string;
};
type Result = {
  summary: string;
  explanations: { passage_id: string; interpretation: string }[];
  practical_applications: string[];
  reflection_question?: string;
  citations: Citation[];
  mode: string;
  debug?: unknown;
};
type Message = { role: string; content: string; result?: Result };
type Conversation = { id: string; title: string };
type Passage = {
  id: string;
  quote_text: string;
  author: string;
  title: string;
  translator: string;
  edition: string;
  reference: string;
  source_url: string;
};
const starters = [
  ["01", "A quieter mind", "I feel anxious about things outside my control."],
  ["02", "Your own measure", "I'm constantly comparing myself to others."],
  ["03", "A different path", "I was passed over for a promotion."],
  ["04", "Room to begin again", "I keep procrastinating on important goals."],
];
const authors = ["Marcus Aurelius", "Epictetus", "Seneca"];
const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;

export default function Page() {
  return domain && clientId ? (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri:
          typeof window !== "undefined" ? window.location.origin : undefined,
        audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
      }}
    >
      <Authenticated />
    </Auth0Provider>
  ) : (
    <Companion />
  );
}
function Authenticated() {
  const auth = useAuth0();
  const getToken = useCallback(
    () => auth.getAccessTokenSilently(),
    [auth.getAccessTokenSilently],
  );
  return (
    <Companion
      token={auth.isAuthenticated ? getToken : undefined}
      login={() => void auth.loginWithRedirect()}
      logout={() =>
        auth.logout({ logoutParams: { returnTo: window.location.origin } })
      }
      signedIn={auth.isAuthenticated}
    />
  );
}

function Companion({
  token,
  login,
  logout,
  signedIn = false,
}: {
  token?: () => Promise<string | undefined>;
  login?: () => void;
  logout?: () => void;
  signedIn?: boolean;
}) {
  const [sidebar, setSidebar] = useState(true),
    [view, setView] = useState("chat"),
    [chats, setChats] = useState<Conversation[]>([]),
    [cid, setCid] = useState<string | null>(null),
    [messages, setMessages] = useState<Message[]>([]),
    [draft, setDraft] = useState(""),
    [busy, setBusy] = useState(false),
    [status, setStatus] = useState(""),
    [error, setError] = useState(""),
    [last, setLast] = useState(""),
    [author, setAuthor] = useState(""),
    [work, setWork] = useState(""),
    [selected, setSelected] = useState<Citation | null>(null),
    [saved, setSaved] = useState<string[]>([]),
    [passages, setPassages] = useState<Passage[]>([]),
    [search, setSearch] = useState(""),
    [light, setLight] = useState(false),
    [demo, setDemo] = useState(true),
    [ready, setReady] = useState(false),
    [copied, setCopied] = useState<number | null>(null);
  useEffect(() => {
    if (window.matchMedia("(max-width: 760px)").matches) setSidebar(false);
  }, []);
  const bottom = useRef<HTMLDivElement>(null),
    input = useRef<HTMLTextAreaElement>(null);
  const api = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const headers = new Headers(init.headers);
      headers.set("Content-Type", "application/json");
      if (token) {
        const accessToken = await token();
        if (!accessToken) throw new Error("Sign in is required");
        headers.set("Authorization", `Bearer ${accessToken}`);
      }
      const r = await fetch("/api/v1" + path, {
        ...init,
        headers,
        credentials: "include",
      });
      if (!r.ok) {
        const body = await r.json().catch(() => null);
        throw new Error(body?.error?.message || `Request failed (${r.status})`);
      }
      return r;
    },
    [token],
  );
  const history = useCallback(
    async () => setChats(await (await api("/conversations")).json()),
    [api],
  );
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const h = await (await api("/health")).json();
        if (alive) setDemo(h.generation_provider !== 'openai');
        if (!signedIn && h.demo_mode)
          await api("/demo-session", { method: "POST" });
        if (signedIn || h.demo_mode) {
          await history();
          const b = await (await api("/bookmarks")).json();
          if (alive) setSaved(b.map((p: Passage) => p.id));
        }
        if (alive) setReady(signedIn || h.demo_mode);
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    })();
    return () => {
      alive = false;
    };
  }, [api, history, signedIn]);
  useEffect(() => {
    if (messages.length) bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);
  useEffect(() => {
    if (view === "chat") return;
    const timer = setTimeout(() => {
      api(
        view === "saved"
          ? "/bookmarks"
          : `/sources?q=${encodeURIComponent(search)}&author=${encodeURIComponent(author)}&work=${encodeURIComponent(work)}`,
      )
        .then((r) => r.json())
        .then((data) => setPassages(view === "saved" ? data : data.passages))
        .catch((e) => setError(e.message));
    }, 200);
    return () => clearTimeout(timer);
  }, [view, search, author, work, api]);
  function fresh() {
    if (busy) return;
    setCid(null);
    setMessages([]);
    setError("");
    setView("chat");
    input.current?.focus();
  }
  async function openChat(id: string) {
    if (busy) return;
    try {
      const c = await (await api("/conversations/" + id)).json();
      setCid(id);
      setMessages(c.messages);
      setView("chat");
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function remove(id: string) {
    try {
      await api("/conversations/" + id, { method: "DELETE" });
      if (cid === id) fresh();
      await history();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function bookmark(p: Citation) {
    try {
      const exists = saved.includes(p.passage_id);
      await api("/bookmarks/" + encodeURIComponent(p.passage_id), {
        method: exists ? "DELETE" : "POST",
      });
      setSaved((prev) =>
        exists
          ? prev.filter((x) => x !== p.passage_id)
          : [...prev, p.passage_id],
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function send(text = draft) {
    if (!text.trim() || busy || !ready) return;
    setDraft("");
    setError("");
    setLast(text);
    setBusy(true);
    setView("chat");
    setMessages((m) => [
      ...m,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    let id = cid;
    try {
      if (!id) {
        const c = await (
          await api("/conversations", { method: "POST" })
        ).json();
        id = c.id;
        setCid(id);
      }
      const r = await api(`/conversations/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({
          message: text,
          author: author || null,
          work: work || null,
        }),
      });
      const reader = r.body!.getReader(),
        decoder = new TextDecoder();
      let buffer = "",
        finished = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let end;
        while ((end = buffer.indexOf("\n\n")) !== -1) {
          const frame = buffer.slice(0, end);
          buffer = buffer.slice(end + 2);
          const kind = frame.match(/^event: (.+)$/m)?.[1],
            raw = frame.match(/^data: (.+)$/m)?.[1];
          if (!raw) continue;
          const data = JSON.parse(raw);
          if (kind === "status") setStatus(data.message);
          if (kind === "delta")
            setMessages((m) =>
              m.map((x, i) =>
                i === m.length - 1
                  ? { ...x, content: x.content + data.text }
                  : x,
              ),
            );
          if (kind === "result") {
            finished = true;
            setMessages((m) =>
              m.map((x, i) =>
                i === m.length - 1
                  ? { ...x, content: data.summary, result: data }
                  : x,
              ),
            );
          }
          if (kind === "error") throw new Error(data.message);
        }
      }
      if (!finished)
        throw new Error(
          "The connection ended before the reply was complete. Please retry.",
        );
      await history();
    } catch (e) {
      setError((e as Error).message);
      setMessages((m) => m.filter((_, i) => i < m.length - 2));
    } finally {
      setBusy(false);
      setStatus("");
    }
  }
  async function copy(m: Message, i: number) {
    try {
      await navigator.clipboard.writeText(
        [m.content, ...(m.result?.practical_applications || [])].join("\n\n"),
      );
      setCopied(i);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      setError("Clipboard access is unavailable in this browser.");
    }
  }
  const card = (c: Citation, i: number) => (
    <article className="citation" key={c.passage_id}>
      <button className="citation-main" onClick={() => setSelected(c)}>
        <span className="citation-number">
          {String(i + 1).padStart(2, "0")}
        </span>
        <span>
          <span className="citation-author">
            {c.author}
            <ArrowUpRight size={14} />
          </span>
          <span className="citation-title">
            {c.title} · {c.reference}
          </span>
          <span className="quote-preview">{c.quote_text}</span>
        </span>
      </button>
      <button
        className={
          saved.includes(c.passage_id) ? "bookmark active" : "bookmark"
        }
        aria-label={
          saved.includes(c.passage_id) ? "Remove bookmark" : "Bookmark passage"
        }
        onClick={() => void bookmark(c)}
      >
        <Bookmark size={15} />
      </button>
    </article>
  );
  return (
    <div className={`shell ${light ? "light" : ""}`}>
      <aside
        inert={selected ? true : undefined}
        className={sidebar ? "sidebar" : "sidebar collapsed"}
        aria-label="Main navigation"
      >
        <div className="brand">
          <span className="brand-mark">
            <Feather size={22} />
          </span>
          <span>
            stoic companion
            <span className="brand-sub">PERSPECTIVE, PRACTICED.</span>
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebar(false)}
            aria-label="Close sidebar"
          >
            <PanelLeftClose size={17} />
          </Button>
        </div>
        <Button
          variant="outline"
          className="new-chat"
          onClick={fresh}
          disabled={busy}
        >
          <Plus size={16} />
          New reflection<span>↗</span>
        </Button>
        <nav>
          <button
            className={view === "chat" ? "nav-item current" : "nav-item"}
            onClick={() => setView("chat")}
          >
            <MessageSquare size={17} />
            Reflections
          </button>
          <button
            className={view === "library" ? "nav-item current" : "nav-item"}
            onClick={() => setView("library")}
          >
            <Library size={17} />
            Source library<span className="small-tag">6</span>
          </button>
          <button
            className={view === "saved" ? "nav-item current" : "nav-item"}
            onClick={() => setView("saved")}
          >
            <Bookmark size={17} />
            Saved passages<span className="small-tag">{saved.length}</span>
          </button>
        </nav>
        <div className="history">
          <div className="eyebrow">YOUR REFLECTIONS</div>
          {chats.length === 0 ? (
            <p className="empty-history">
              A little space for what’s on your mind.
            </p>
          ) : (
            chats.map((c) => (
              <div
                className={`history-row ${cid === c.id ? "chosen" : ""}`}
                key={c.id}
              >
                <button onClick={() => void openChat(c.id)} disabled={busy}>
                  {c.title}
                </button>
                <button
                  onClick={() => void remove(c.id)}
                  disabled={busy}
                  aria-label={`Delete ${c.title}`}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="daily">
            <span className="eyebrow">AN ANCIENT PRACTICE</span>
            <p>
              Pause. Examine.
              <br />
              Begin again.
            </p>
            <span>One reflection at a time.</span>
          </div>
          <button
            className="profile"
            onClick={signedIn ? logout : login}
            disabled={!login}
          >
            <span className="avatar">{signedIn ? "S" : "G"}</span>
            <span>
              {signedIn ? "Your account" : "Guest explorer"}
              <small>
                {demo ? "Local demo · 30 messages" : "Private reflections"}
              </small>
            </span>
            {login ? (
              <LogIn size={16} />
            ) : (
              <span className="demo-pill">DEMO</span>
            )}
          </button>
        </div>
      </aside>
      <main className="main" inert={selected ? true : undefined}>
        <header className="topbar">
          <div className="topbar-left">
            {!sidebar && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebar(true)}
                aria-label="Open sidebar"
              >
                <Menu size={18} />
              </Button>
            )}
            <span>
              {view === "chat"
                ? "A space to reflect"
                : view === "library"
                  ? "The source library"
                  : "Your saved passages"}
            </span>
            <ChevronDown size={12} />
          </div>
          <div className="topbar-right">
            {!signedIn && login && (
              <Button variant="ghost" onClick={login}>
                <LogIn size={14} />
                Sign in
              </Button>
            )}
            <span className="grounded">
              <i />
              {demo ? "Offline demo" : "Grounded in original texts"}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setLight(!light)}
              aria-label="Toggle light mode"
            >
              <Sun size={17} />
            </Button>
          </div>
        </header>
        {view === "chat" ? (
          <>
            <div
              className={`chat-scroll ${messages.length ? "has-messages" : ""}`}
            >
              {!messages.length ? (
                <section className="welcome">
                  <div className="intro-icon">
                    <Feather size={30} strokeWidth={1} />
                  </div>
                  <span className="eyebrow accent">
                    ANCIENT WISDOM. YOUR EVERYDAY LIFE.
                  </span>
                  <h1>
                    A little distance.
                    <br />
                    <em>A clearer perspective.</em>
                  </h1>
                  <p>
                    You don’t have to figure it all out at once.
                    <br />
                    Bring what’s on your mind. Explore it with the Stoics.
                  </p>
                  <div className="starters">
                    {starters.map(([num, title, text]) => (
                      <button
                        key={num}
                        onClick={() => void send(text)}
                        disabled={!ready || busy}
                      >
                        <span className="starter-num">{num}</span>
                        <span>
                          <strong>{title}</strong>
                          <small>{text}</small>
                        </span>
                        <ArrowUpRight size={16} />
                      </button>
                    ))}
                  </div>
                  <div className="authors">
                    <span>IN CONVERSATION WITH</span>
                    <span>Marcus Aurelius</span>
                    <i /> <span>Epictetus</span>
                    <i />
                    <span>Seneca</span>
                  </div>
                </section>
              ) : (
                <section className="messages" aria-live="polite">
                  {messages.map((m, i) =>
                    m.role === "user" ? (
                      <div className="user-message" key={i}>
                        {m.content}
                      </div>
                    ) : (
                      <article className="assistant-message" key={i}>
                        <div className="assistant-label">
                          <Feather size={16} />
                          STOIC COMPANION{" "}
                          {m.result?.mode === "demo" && (
                            <span>OFFLINE DEMO</span>
                          )}
                        </div>
                        <p className="summary">{m.content || status}</p>
                        {m.result && (
                          <>
                            <div className="evidence-heading">
                              <BookOpen size={14} />
                              FROM THE TEXTS <span>Verified excerpts</span>
                            </div>
                            <div className="citations">
                              {m.result.citations.map(card)}
                            </div>
                            {m.result.explanations.map((x, j) => (
                              <p className="interpretation" key={j}>
                                <span>
                                  Reading {j + 1} · Modern interpretation
                                </span>
                                {x.interpretation}
                              </p>
                            ))}
                            <div className="practice">
                              <span className="eyebrow accent">
                                PUT IT INTO PRACTICE
                              </span>
                              <ol>
                                {m.result.practical_applications.map((x, j) => (
                                  <li key={j}>{x}</li>
                                ))}
                              </ol>
                              {m.result.reflection_question && (
                                <p>{m.result.reflection_question}</p>
                              )}
                            </div>
                            <div className="response-actions">
                              <button onClick={() => void copy(m, i)}>
                                {copied === i ? (
                                  <Check size={14} />
                                ) : (
                                  <Copy size={14} />
                                )}{" "}
                                {copied === i ? "Copied" : "Copy reflection"}
                              </button>
                              {m.result.debug !== undefined && (
                                <details>
                                  <summary>Developer details</summary>
                                  <pre>
                                    {JSON.stringify(m.result.debug, null, 2)}
                                  </pre>
                                </details>
                              )}
                            </div>
                          </>
                        )}
                      </article>
                    ),
                  )}
                </section>
              )}
              <div ref={bottom} />
            </div>
            <div className="composer-wrap">
              {error && (
                <div className="error" role="alert">
                  {error}
                  {last && (
                    <button onClick={() => void send(last)} disabled={busy}>
                      Retry
                    </button>
                  )}
                </div>
              )}
              {busy && (
                <div className="loading">
                  <LoaderCircle size={13} className="spin" />
                  {status}
                </div>
              )}
              <form
                className="composer"
                onSubmit={(e) => {
                  e.preventDefault();
                  void send();
                }}
              >
                <textarea
                  ref={input}
                  aria-label="Your reflection"
                  placeholder="What’s on your mind today?"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  maxLength={6000}
                  rows={2}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      !e.shiftKey &&
                      !e.nativeEvent.isComposing
                    ) {
                      e.preventDefault();
                      void send();
                    }
                  }}
                />
                <div className="composer-bottom">
                  <div className="filters">
                    <BookOpen size={14} />
                    <select
                      aria-label="Author filter"
                      value={author}
                      onChange={(e) => {
                        setAuthor(e.target.value);
                        setWork("");
                      }}
                    >
                      <option value="">All philosophers</option>
                      {authors.map((a) => (
                        <option key={a}>{a}</option>
                      ))}
                    </select>
                    <select
                      aria-label="Work filter"
                      value={work}
                      onChange={(e) => setWork(e.target.value)}
                    >
                      <option value="">All works</option>
                      {[
                        ["meditations", "Meditations"],
                        ["enchiridion", "Encheiridion"],
                        ["discourses", "Discourses"],
                        ["letters", "Moral Letters"],
                      ].map(([v, l]) => (
                        <option key={v} value={v}>
                          {l}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    size="icon"
                    type="submit"
                    aria-label="Send reflection"
                    disabled={!draft.trim() || busy || !ready}
                  >
                    <ArrowUp size={19} />
                  </Button>
                </div>
              </form>
              <p className="disclaimer">
                {demo
                  ? "Demo uses real passages with a fixed reflection template. Connect OpenAI for personalized guidance."
                  : "Philosophical reflection, not professional care. Always read passages in context."}
              </p>
            </div>
          </>
        ) : (
          <section className="library-view">
            <span className="eyebrow accent">WISDOM WITH A PAPER TRAIL</span>
            <h1>
              {view === "saved"
                ? "Keep what stays with you."
                : "Go back to the source."}
            </h1>
            <p>
              Original passages. Named translators. References you can follow.
            </p>
            {view === "library" && (
              <div className="library-search">
                <Search size={18} />
                <input
                  placeholder="Search the source texts…"
                  aria-label="Search source library"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select
                  aria-label="Library author"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                >
                  <option value="">All philosophers</option>
                  {authors.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>
            )}
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <div className="library-grid">
              {passages.map((p, i) =>
                card(
                  { ...p, passage_id: p.id, surrounding_passage: p.quote_text },
                  i,
                ),
              )}
            </div>
            {!passages.length && (
              <p className="empty-state">
                {view === "saved"
                  ? "Bookmark a passage from a reflection to keep it here."
                  : "No passages found. Try a different search, or run source ingestion."}
              </p>
            )}
            <p className="library-note">
              US public-domain editions. Copyright rules differ by country.
              Currently showing up to 30 matching passages.
            </p>
          </section>
        )}
      </main>
      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <section
            className="source-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Original passage"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setSelected(null);
              if (e.key === "Tab") {
                const items = Array.from(
                  e.currentTarget.querySelectorAll<HTMLElement>(
                    'button, a[href], summary, [tabindex="0"]',
                  ),
                );
                const first = items[0],
                  last = items[items.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last?.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <div className="modal-top">
              <span className="eyebrow accent">THE ORIGINAL PASSAGE</span>
              <Button
                autoFocus
                variant="ghost"
                size="icon"
                onClick={() => setSelected(null)}
                aria-label="Close passage"
              >
                <X size={19} />
              </Button>
            </div>
            <h2>{selected.title}</h2>
            <p className="source-byline">
              {selected.author} · {selected.reference}
            </p>
            <blockquote>{selected.quote_text}</blockquote>
            <details>
              <summary>Read the surrounding passage</summary>
              <p className="full-passage">{selected.surrounding_passage}</p>
            </details>
            <dl>
              <dt>TRANSLATION</dt>
              <dd>{selected.translator}</dd>
              <dt>EDITION</dt>
              <dd>{selected.edition}</dd>
              <dt>VERIFICATION</dt>
              <dd>Exact source excerpt; whitespace normalization only.</dd>
            </dl>
            <div className="modal-actions">
              <a href={selected.source_url} target="_blank" rel="noreferrer">
                Read the original source <ArrowUpRight size={15} />
              </a>
              <Button variant="outline" onClick={() => void bookmark(selected)}>
                <Bookmark size={15} />
                {saved.includes(selected.passage_id) ? "Saved" : "Save passage"}
              </Button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
