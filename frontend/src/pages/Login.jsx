import { useRef, useState } from "react";
import * as LottieImport from "lottie-react";
import { Eye, EyeOff, Lock, User, Loader2, Target, TrendingUp, Bot, MessageSquare, BarChart3, Zap } from "lucide-react";

// This Vite setup's CJS/ESM interop double-wraps lottie-react's default export
// (`import Lottie from "lottie-react"` resolves to the package's whole exports object,
// not the component) -- confirmed live via a real console-error render failure, not
// guessed. Unwrap defensively so this survives an interop-behavior change later too.
const Lottie = LottieImport.default?.default || LottieImport.default;
import loginBuddy from "../assets/login-buddy.json";
import { api } from "../api/client";

// Segment timings baked into the animation file itself (fr=100fps, so seconds*100=frames):
// Blinking [0,1]s idle loop, Following [1.2,1.7]s eyes track the username field, Covering
// [1.8,2.3]s hides eyes while the password is focused, Peeking [2.3,2.6]s after it blurs.
const SEGMENTS = {
  blink: [0, 100],
  follow: [120, 170],
  cover: [180, 230],
  peek: [230, 260],
};

// Flat-icon chips echoing what this product actually is (AI + sales), styled in the
// logo's own slate/gray palette -- Target directly mirrors the logo's own bullseye mark.
// Live on the PAGE background around the card (not inside the card itself -- the user
// was explicit about this: the card stays clean, the surrounding canvas gets the theme),
// connected by faint dashed "circuit" lines that echo the logo's own circuit-trace detail.
const ORBIT_CHIPS = [
  { Icon: Target, top: "12%", left: "14%", delay: "0s" },
  { Icon: TrendingUp, top: "18%", right: "16%", delay: "-1.4s" },
  { Icon: Bot, bottom: "16%", left: "10%", delay: "-2.6s" },
  { Icon: MessageSquare, bottom: "14%", right: "12%", delay: "-0.7s" },
  { Icon: BarChart3, top: "50%", left: "5%", delay: "-3.4s" },
  { Icon: Zap, top: "48%", right: "6%", delay: "-2s" },
];

export default function Login({ onLoggedIn }) {
  const lottieRef = useRef(null);
  const peekTimeout = useRef(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  function playSegment(name, loop) {
    const anim = lottieRef.current;
    // `setLoop` lives on the underlying lottie-web AnimationItem, not on lottie-react's
    // own ref wrapper (which only exposes playSegments/play/stop/etc directly) --
    // confirmed against this project's actual installed version's type definitions.
    if (!anim?.animationItem) return;
    clearTimeout(peekTimeout.current);
    anim.animationItem.setLoop(loop);
    anim.playSegments(SEGMENTS[name], true);
  }

  function idle() {
    playSegment("blink", true);
  }

  function handlePasswordFocus() {
    // "Covering" is a one-shot hands-going-up TRANSITION, not a held pose on its own --
    // looping it replayed the motion over and over (found from a real screenshot: looked
    // like the hand kept flinching, never actually stayed covering). loop=false lets
    // playSegments stop and hold on the segment's own last frame instead.
    playSegment("cover", false);
  }

  function handlePasswordBlur() {
    // Peek back out once, then settle into the idle blink loop -- a dead stop on
    // "Covering" would leave the character looking permanently startled.
    playSegment("peek", false);
    peekTimeout.current = setTimeout(idle, 350);
  }

  function toggleShowPassword() {
    setShowPassword((prev) => {
      const next = !prev;
      // Real ask: clicking "show password" should make the mascot peek out to look at
      // it (matches the earlier eye-focus fix -- the button no longer steals input
      // focus, so this has to explicitly drive the reaction itself instead of relying
      // on a blur/focus event that no longer fires here). Hiding it again covers back up.
      playSegment(next ? "peek" : "cover", false);
      return next;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.login(username, password);
      onLoggedIn();
    } catch (err) {
      setError("Username ya password galat hai.");
      setShake(true);
      setTimeout(() => setShake(false), 400);
      playSegment("cover", false);
      peekTimeout.current = setTimeout(idle, 600);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#14161a] p-4">
      {/* Ambient background in the logo's own tones (slate #4e535a / gray #adb0b4) --
         not a generic purple gradient, which read as off-brand against the actual logo.
         The AI-sales flat-icon chips + circuit lines live HERE, on the page canvas
         around the card, not inside the card itself -- explicit user correction after
         the first pass put them inside the left panel instead. */}
      <div className="pointer-events-none absolute inset-0">
        <div
          className="animate-login-orb absolute -left-32 -top-32 h-[32rem] w-[32rem] rounded-full bg-[#4e535a]/40 blur-[110px]"
        />
        <div
          className="animate-login-orb absolute -bottom-40 -right-20 h-[28rem] w-[28rem] rounded-full bg-[#4e535a]/30 blur-[110px]"
          style={{ animationDelay: "-3s" }}
        />
        <div
          className="animate-login-orb absolute bottom-1/3 left-1/4 h-72 w-72 rounded-full bg-[#adb0b4]/10 blur-[90px]"
          style={{ animationDelay: "-6s" }}
        />
        <div className="absolute inset-0 opacity-[0.05]" style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
          backgroundSize: "24px 24px",
        }} />

        {/* Circuit-trace lines drawn loosely toward the card, echoing the logo's own
           circuit detail -- spans the whole viewport, not just the card's bounds. */}
        <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <g stroke="#adb0b4" strokeWidth="0.15" fill="none" opacity="0.3">
            <path className="animate-login-dash" d="M20,20 L38,32" />
            <path className="animate-login-dash" d="M80,24 L64,34" />
            <path className="animate-login-dash" d="M14,80 L32,68" />
            <path className="animate-login-dash" d="M86,82 L66,70" />
            <path className="animate-login-dash" d="M8,52 L26,50" />
            <path className="animate-login-dash" d="M92,50 L74,50" />
          </g>
        </svg>

        {ORBIT_CHIPS.map(({ Icon, delay, ...pos }, i) => (
          <div
            key={i}
            className="animate-login-chip absolute hidden h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-[#c3c5c8] shadow-lg backdrop-blur-sm md:flex"
            style={{ ...pos, animationDelay: delay }}
          >
            <Icon size={18} strokeWidth={1.75} />
          </div>
        ))}
      </div>

      <div
        className={`animate-login-card-in relative grid w-full max-w-4xl grid-cols-1 overflow-hidden rounded-2xl bg-white shadow-[0_20px_70px_-15px_rgba(0,0,0,0.55)] ring-1 ring-white/10 md:grid-cols-2 ${
          shake ? "animate-login-shake" : ""
        }`}
      >
        {/* Left: brand + character, logo-matched slate/charcoal */}
        <div className="relative hidden flex-col items-center justify-center gap-5 overflow-hidden bg-gradient-to-br from-[#3a3e44] via-[#2a2d32] to-[#17181b] p-10 md:flex">
          <div className="absolute inset-0 opacity-[0.06]" style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "22px 22px",
          }} />
          <div className="absolute -bottom-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-[#adb0b4]/15 blur-[80px]" />

          <div className="animate-login-bob relative z-10 w-52 drop-shadow-[0_8px_24px_rgba(0,0,0,0.4)]">
            <Lottie
              lottieRef={lottieRef}
              animationData={loginBuddy}
              loop={false}
              autoplay={false}
              onDOMLoaded={idle}
            />
          </div>
          <div className="relative z-10 text-center">
            <p className="text-xl font-semibold tracking-tight text-white">AI-BOS</p>
            <p className="mt-1.5 text-sm text-[#c3c5c8]">Enterprise AI Business Operating System</p>
          </div>
        </div>

        {/* Right: form */}
        <div className="flex flex-col justify-center p-8 sm:p-10">
          <div className="mb-8 flex items-center gap-2 md:hidden">
            <img src="/logo.png" alt="AI-BOS" className="h-8 w-8" />
            <span className="text-base font-semibold text-slate-900">AI-BOS</span>
          </div>
          <div className="mb-8">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Welcome back</h1>
            <p className="mt-1.5 text-sm text-slate-500">Sign in to access the sales dashboard.</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="username" className="text-sm font-medium text-slate-700">Username</label>
              <div className="relative">
                <User size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => playSegment("follow", false)}
                  onBlur={idle}
                  className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3.5 text-sm text-slate-900 outline-none transition-all focus:border-[#4e535a] focus:ring-4 focus:ring-[#4e535a]/10"
                  placeholder="admin"
                  required
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-sm font-medium text-slate-700">Password</label>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={handlePasswordFocus}
                  onBlur={handlePasswordBlur}
                  className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-10 text-sm text-slate-900 outline-none transition-all focus:border-[#4e535a] focus:ring-4 focus:ring-[#4e535a]/10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={toggleShowPassword}
                  // Real bug, found from a screenshot: this button was stealing focus
                  // away from the password field on click (confirmed live --
                  // document.activeElement became the button), which fired the field's
                  // onBlur handler and made the mascot's covering-eyes pose drop
                  // instantly the moment "show password" was clicked -- looked like the
                  // animation was glitching/breaking, not an intentional reaction.
                  // preventDefault on mousedown (not click) stops a button from ever
                  // taking focus, so the password field -- and the animation state tied
                  // to its focus -- is now completely undisturbed by this click.
                  onMouseDown={(e) => e.preventDefault()}
                  tabIndex={-1}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-inset ring-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#3a3e44] to-[#565c64] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#4e535a]/25 transition-all hover:shadow-xl hover:shadow-[#4e535a]/35 hover:brightness-110 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : <Lock size={15} />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">Secured session · IVinfotech</p>
        </div>
      </div>
    </div>
  );
}
