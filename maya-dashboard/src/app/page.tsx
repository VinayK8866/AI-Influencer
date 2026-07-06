"use client";

import { useState, useEffect } from "react";
import { 
  Camera, 
  Film, 
  MapPin, 
  Play, 
  Settings, 
  Sparkles, 
  ShoppingBag, 
  MessageSquare, 
  Send, 
  RefreshCw, 
  Globe, 
  Tag,
  Coins
} from "lucide-react";

interface CatalogItem {
  id: string;
  name: string;
  category: string;
  brand: string;
  visual_description: string;
  affiliate_link: string;
  price: string;
}

interface LastPost {
  post_type: string;
  location: string;
  subtype: string;
  products: string[];
  timestamp: number;
  caption: string;
  media_url?: string;
}

interface BudgetState {
  daily_spend_limit: number;
  per_action_limit: number;
  today_spend: number;
  total_spend: number;
  last_reset_date: string;
}

export default function Home() {
  const [status, setStatus] = useState("Offline");
  const [location, setLocation] = useState("Milan");
  const [loading, setLoading] = useState(false);
  const [storyboard, setStoryboard] = useState("");
  const [metadata, setMetadata] = useState("");
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [lastPost, setLastPost] = useState<LastPost | null>(null);
  const [budget, setBudget] = useState<BudgetState | null>(null);

  // Strategy Memory & Analytics States
  const [analyticsBrief, setAnalyticsBrief] = useState("");
  const [history, setHistory] = useState<any[]>([]);

  // Active Background Run State
  interface ActiveRun {
    status: string;
    post_type: string | null;
    current_step: string;
    logs: string[];
  }
  const [activeRun, setActiveRun] = useState<ActiveRun | null>(null);

  // Webhook Simulator State
  const [simUsername, setSimUsername] = useState("riya_sharma");
  const [simComment, setSimComment] = useState("OMG I love this look! What is the STYLE?");
  const [webhookResult, setWebhookResult] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  // Fetch status, catalog, and state
  const loadData = () => {
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        if (data.status) {
          setStatus("Online");
          setLocation(data.state?.current_location || "Milan");
          if (data.state?.last_post) {
            setLastPost(data.state.last_post);
          }
          if (data.state?.active_run) {
            setActiveRun(data.state.active_run);
          }
          if (data.state?.budget) {
            setBudget(data.state.budget);
          }
        }
      })
      .catch((err) => {
        console.error("API not available", err);
        setStatus("Offline");
      });

    // Fetch live Strategy & Analytics database
    fetch("/api/analytics")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setAnalyticsBrief(data.brief);
          setHistory(data.history);
        }
      })
      .catch((err) => console.error("Strategy API not reachable", err));
  };

  useEffect(() => {
    loadData();

    // Setup polling every 2.5 seconds to track background generation logs
    const poller = setInterval(() => {
      fetch("/api/status")
        .then((res) => res.json())
        .then((data) => {
          if (data.status) {
            setStatus("Online");
            setLocation(data.state?.current_location || "Milan");
            if (data.state?.last_post) {
              setLastPost(data.state.last_post);
            }
            if (data.state?.budget) {
              setBudget(data.state.budget);
            }
            if (data.state?.active_run) {
              const run = data.state.active_run;
              setActiveRun(run);
              
              // If a run just transitioned to completed/failed, refresh analytics!
              if (run.status === 'idle' || run.status === 'failed') {
                fetch("/api/analytics")
                  .then((res) => res.json())
                  .then((adata) => {
                    if (adata.success) {
                      setAnalyticsBrief(adata.brief);
                      setHistory(adata.history);
                    }
                  })
                  .catch(() => {});
              }
            }
          }
        })
        .catch((err) => console.error("Polling status offline", err));
    }, 2500);

    return () => clearInterval(poller);
  }, []);
  useEffect(() => {
    // We can fetch static JSON catalog or construct local one
    setCatalog([
      {
        id: "espresso_trench_coat",
        name: "Classic Espresso Double-Breasted Trench Coat",
        category: "outerwear",
        brand: "Zara Style",
        visual_description: "classic double-breasted coffee-brown trench coat with belt",
        affiliate_link: "https://www.amazon.com/s?k=womens+espresso+trench+coat",
        price: "$89.90"
      },
      {
        id: "slate_grey_blazer",
        name: "Oversized Tailored Slate Grey Blazer",
        category: "outerwear",
        brand: "Zara Style",
        visual_description: "oversized structured slate grey tailored wool blazer",
        affiliate_link: "https://www.amazon.com/s?k=womens+oversized+grey+blazer",
        price: "$79.90"
      },
      {
        id: "cream_silk_scarf",
        name: "Crema Mulberry Silk Square Scarf",
        category: "accessories",
        brand: "Mango Style",
        visual_description: "light cream-colored silk scarf tied loosely around her neck",
        affiliate_link: "https://www.amazon.com/s?k=cream+silk+scarf",
        price: "$28.00"
      },
      {
        id: "tan_leather_handbag",
        name: "Structured Pebbled Tan Leather Handbag",
        category: "bag",
        brand: "Polene Style",
        visual_description: "structured minimalist tan pebbled-leather handbag with gold clasps",
        affiliate_link: "https://www.amazon.com/s?k=tan+pebbled+leather+handbag",
        price: "$120.00"
      },
      {
        id: "black_knit_dress",
        name: "Ribbed Knit High-Neck Bodycon Dress",
        category: "dress",
        brand: "Massimo Dutti Style",
        visual_description: "form-fitting ribbed black knit high-neck midi dress",
        affiliate_link: "https://www.amazon.com/s?k=womens+black+ribbed+knit+dress",
        price: "$95.00"
      },
      {
        id: "gold_chunky_hoops",
        name: "18k Gold Plated Chunky Teardrop Hoops",
        category: "accessories",
        brand: "Bottega Style",
        visual_description: "chunky teardrop gold plated statement earrings",
        affiliate_link: "https://www.amazon.com/s?k=chunky+gold+teardrop+hoops",
        price: "$35.00"
      }
    ]);
  }, []);

  const generateStoryboard = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/generate-reel-storyboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location }),
      });
      const data = await res.json();
      if (data.success) {
        setStoryboard(data.storyboard);
        setMetadata(data.metadata);
        loadData(); // Reload status to get new active products if any
      } else {
        alert("Error: " + data.error);
      }
    } catch (err) {
      alert("Failed to connect to backend");
    }
    setLoading(false);
  };

  const triggerPost = async (type: string) => {
    setLoading(true);
    try {
      const res = await fetch("/api/trigger-cycle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_type: type, location }),
      });
      const data = await res.json();
      if (data.success) {
        // Optimistically set active run state to processing
        setActiveRun({
          status: "processing",
          post_type: type,
          current_step: "Step 1/5: Booting Autopilot & Storyboard Engines",
          logs: ["Triggered background task thread successfully.", "Connecting to Gemini agency cockpit..."]
        });
      } else {
        alert("Error: " + data.message);
      }
    } catch (err) {
      alert("Failed to connect to backend. Please make sure Flask is running.");
    }
    setLoading(false);
  };

  const runWebhookSimulation = async () => {
    setSimulating(true);
    try {
      const res = await fetch("/api/webhook/instagram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: simUsername,
          comment_text: simComment
        }),
      });
      const data = await res.json();
      setWebhookResult(data);
    } catch (err) {
      alert("Failed to reach webhook simulation server.");
    }
    setSimulating(false);
  };

  return (
    <div className="min-h-screen bg-[#0d0d11] text-[#e4e4e9] font-sans p-6 md:p-12 selection:bg-emerald-500/30">
      
      {/* Background visual styling glow elements */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-8 relative z-10">

        {/* Brand Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-neutral-800/80 pb-6 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-1 rounded-full border border-emerald-500/20 font-mono tracking-wider uppercase">
                Agency Cockpit
              </span>
            </div>
            <h1 className="text-4xl font-extralight tracking-tight text-white mt-2">
              MAYA <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400">ROSSI</span>
            </h1>
            <p className="text-neutral-400 text-sm mt-1 tracking-wider uppercase">
              Virtual Influencer Growth & Monetization Hub
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={loadData}
              className="p-2.5 bg-neutral-900 hover:bg-neutral-800 rounded-full border border-neutral-800 text-neutral-400 transition"
              title="Refresh State"
            >
              <RefreshCw size={18} />
            </button>
            <div className="flex items-center gap-3 text-sm bg-neutral-900/90 px-5 py-2.5 rounded-full border border-neutral-850 shadow-lg">
              <span className={`w-2.5 h-2.5 rounded-full ${status === 'Online' ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`}></span>
              <span className="font-mono text-xs tracking-wider text-neutral-300">System: {status}</span>
            </div>
          </div>
        </header>

        {/* Key States Hub */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          {/* Target Location Card */}
          {/* Interactive Travel Planner Card */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition duration-500" />
            <h2 className="text-xs uppercase tracking-widest text-neutral-500 mb-3 flex items-center gap-2 font-mono">
              <Globe size={14} className="text-emerald-400" /> Real Itinerary Settings
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] uppercase font-mono text-neutral-500 block mb-1">Current Active Location</label>
                <select
                  value={location}
                  onChange={async (e) => {
                    const newLoc = e.target.value;
                    setLocation(newLoc);
                    try {
                      await fetch("/api/update-settings", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ location: newLoc }),
                      });
                    } catch (err) {
                      console.error("Failed to update settings", err);
                    }
                  }}
                  className="w-full bg-neutral-950 border border-neutral-850 text-white rounded-lg p-2.5 text-xs font-mono focus:outline-none focus:border-emerald-500 transition"
                >
                  <option value="Milan">Milan, Italy 🇮🇹</option>
                  <option value="Tuscany">Tuscany, Italy 🇮🇹</option>
                  <option value="Rome">Rome, Italy 🇮🇹</option>
                  <option value="Amalfi Coast">Amalfi Coast 🇮🇹</option>
                  <option value="Venice">Venice, Italy 🇮🇹</option>
                  <option value="Mumbai">Mumbai, India 🇮🇳</option>
                  <option value="Goa">Goa, India 🇮🇳</option>
                </select>
              </div>
              <p className="text-[10px] text-neutral-400 leading-relaxed font-mono">
                Changes Maya's location immediately. The visual generator automatically anchors in this destination.
              </p>
            </div>
          </div>

          {/* Active Post Subtype Indicator (80/20 Engine) */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition duration-500" />
            <h2 className="text-xs uppercase tracking-widest text-neutral-500 mb-3 flex items-center gap-2 font-mono">
              <Tag size={14} className="text-purple-400" /> 80/20 Funnel State
            </h2>
            {lastPost ? (
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase ${
                    lastPost.subtype === 'style_drop' 
                      ? 'bg-purple-500/15 text-purple-400 border border-purple-500/25' 
                      : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                  }`}>
                    {lastPost.subtype === 'style_drop' ? '20% Style Drop' : '80% Pure Lifestyle'}
                  </span>
                </div>
                <div className="text-xs text-neutral-400 mt-3 font-mono line-clamp-1">
                  Active Links: {lastPost.products?.length > 0 ? `${lastPost.products.length} Products` : 'Curated Shop Bio'}
                </div>
              </div>
            ) : (
              <div>
                <span className="text-neutral-400 text-sm">No post state loaded.</span>
                <p className="text-xs text-neutral-500 mt-2">Trigger a new photo or reel draft to initialize state.</p>
              </div>
            )}
          </div>

          {/* Budget Governance Card */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-full blur-2xl group-hover:bg-teal-500/10 transition duration-500" />
            <h2 className="text-xs uppercase tracking-widest text-neutral-500 mb-3 flex items-center gap-2 font-mono">
              <Coins size={14} className="text-teal-400" /> Budget Governance
            </h2>
            {budget ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-neutral-400">Daily Spend:</span>
                  <span className={`font-bold ${budget.today_spend >= budget.daily_spend_limit ? 'text-red-400' : 'text-emerald-400'}`}>
                    ${budget.today_spend.toFixed(3)}
                  </span>
                </div>
                
                {/* Spend progress bar */}
                <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-500 ${budget.today_spend >= budget.daily_spend_limit ? 'bg-red-500' : 'bg-teal-500'}`}
                    style={{ width: `${Math.min(100, (budget.today_spend / budget.daily_spend_limit) * 100)}%` }}
                  />
                </div>

                <div className="flex justify-between items-center text-[10px] font-mono text-neutral-500 pt-1">
                  <span>Daily Cap: ${budget.daily_spend_limit.toFixed(2)}</span>
                  <span>Per-Action: ${budget.per_action_limit.toFixed(2)}</span>
                </div>
                
                <div className="text-[10px] font-mono text-neutral-450 pt-1 border-t border-neutral-900/60 flex justify-between items-center">
                  <span>Total Spent:</span>
                  <span className="text-white font-bold">${budget.total_spend.toFixed(2)}</span>
                </div>
              </div>
            ) : (
              <div>
                <span className="text-neutral-500 text-xs font-mono">Initializing Budget tracker...</span>
              </div>
            )}
          </div>

          {/* Trigger Suite */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl flex flex-col justify-between">
            <h2 className="text-xs uppercase tracking-widest text-neutral-500 mb-4 flex items-center gap-2 font-mono">
              <Play size={14} className="text-emerald-400" /> Dispatch Engines
            </h2>
            <div className="flex gap-4">
              <button
                onClick={() => triggerPost('photo')}
                disabled={loading}
                className="flex-1 bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 text-white font-mono text-xs py-3 rounded-xl transition duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Camera size={15} /> Photo Draft
              </button>
              <button
                onClick={() => triggerPost('reel')}
                disabled={loading}
                className="flex-1 bg-emerald-500 hover:bg-emerald-450 text-neutral-950 font-mono text-xs py-3 rounded-xl font-bold transition duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Film size={15} /> Reel Draft
              </button>
            </div>
          </div>
        </div>

        {/* Dynamic Agent Workflow Activity Console */}
        {activeRun && activeRun.status === 'processing' && (
          <div className="bg-neutral-950/80 backdrop-blur-xl p-6 rounded-2xl border border-purple-500/30 shadow-2xl relative overflow-hidden animate-fadeIn">
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-3xl" />
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-ping" />
                <h3 className="text-xs font-semibold text-white font-mono uppercase tracking-widest">
                  Agent Workflow Activity Console ({activeRun.post_type} mode)
                </h3>
              </div>
              <span className="text-[9px] font-mono uppercase bg-purple-500/10 border border-purple-500/20 text-purple-400 px-3 py-1 rounded">
                Generation Active
              </span>
            </div>

            {/* Step indicator */}
            <div className="mb-4 bg-[#14141b]/80 border border-neutral-900 p-4 rounded-xl">
              <div className="text-xs font-mono text-white mb-2 flex justify-between items-center">
                <span>Active Phase:</span>
                <span className="text-purple-400 font-bold">{activeRun.current_step}</span>
              </div>
              
              {/* Progress bar */}
              <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-700 ${
                    activeRun.current_step.includes('Step 1') ? 'w-1/5'
                      : activeRun.current_step.includes('Step 2') ? 'w-2/5'
                      : activeRun.current_step.includes('Step 3') ? 'w-3/5'
                      : activeRun.current_step.includes('Step 4') ? 'w-4/5'
                      : 'w-11/12'
                  }`} 
                />
              </div>
            </div>

            {/* Live Terminal logs */}
            <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-900 max-h-48 overflow-y-auto font-mono text-[10px] space-y-1.5 text-neutral-400 leading-normal scrollbar-thin">
              {activeRun.logs.map((log, index) => (
                <div key={index} className="flex gap-2 items-start border-l border-purple-500/30 pl-2">
                  <span className="text-purple-500/60 font-bold select-none">&gt;&gt;</span>
                  <span className="flex-1 whitespace-pre-wrap">{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agency Studio Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Storyboard Workspace */}
          <div className="lg:col-span-2 bg-[#14141b]/60 backdrop-blur-xl p-8 rounded-2xl border border-neutral-800/60 shadow-2xl space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium flex items-center gap-2 text-white">
                <Sparkles className="text-emerald-400" size={18} />
                The Visual Storyboard Chamber
              </h2>
              <button
                onClick={generateStoryboard}
                disabled={loading}
                className="bg-white hover:bg-neutral-200 text-black px-5 py-2 rounded-full font-mono text-xs font-semibold transition disabled:opacity-50 shadow-lg"
              >
                {loading ? "Debating..." : "Draft Storyboard"}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-neutral-950/80 p-5 rounded-xl border border-neutral-900">
                <h3 className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3 font-mono">Approved Visual Directive</h3>
                <div className="text-xs text-neutral-300 font-mono leading-relaxed max-h-72 overflow-y-auto whitespace-pre-wrap">
                  {storyboard || "No storyboard drafted yet. Click 'Draft Storyboard' to orchestrate the Creative Director, Researcher, and QA Critic."}
                </div>
              </div>
              <div className="bg-neutral-950/80 p-5 rounded-xl border border-neutral-900">
                <h3 className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3 font-mono">Operations & Alt-Text Metadata</h3>
                <div className="text-xs text-neutral-300 font-mono leading-relaxed max-h-72 overflow-y-auto whitespace-pre-wrap">
                  {metadata || "Waiting for Operations Manager keywords allocation..."}
                </div>
              </div>
              <div className="bg-neutral-950/80 p-5 rounded-xl border border-neutral-900 flex flex-col justify-between">
                <div>
                  <h3 className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3 font-mono">Drafted Visual Asset</h3>
                  {lastPost?.media_url ? (
                    <div className="space-y-3">
                      <div className="relative aspect-[9/16] w-full rounded-lg overflow-hidden border border-neutral-850 bg-black flex items-center justify-center">
                        {lastPost.post_type === 'reel' ? (
                          <video 
                            src={lastPost.media_url} 
                            controls 
                            loop 
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <img 
                            src={lastPost.media_url} 
                            alt="Maya Rossi Generated Draft" 
                            className="w-full h-full object-cover"
                          />
                        )}
                        <span className="absolute top-2 left-2 bg-black/60 text-emerald-400 text-[9px] font-mono px-2 py-0.5 rounded uppercase tracking-wider">
                          {lastPost.post_type}
                        </span>
                      </div>
                      <div className="text-[10px] text-neutral-400 font-mono text-center truncate">
                        Loc: {lastPost.location} | Sub: {lastPost.subtype}
                      </div>
                    </div>
                  ) : (
                    <div className="border border-dashed border-neutral-800 rounded-lg aspect-[9/16] flex flex-col items-center justify-center p-4 text-center">
                      <Sparkles className="text-neutral-600 mb-2 animate-pulse" size={24} />
                      <span className="text-[10px] text-neutral-500 font-mono">
                        No draft file generated yet.
                      </span>
                      <p className="text-[9px] text-neutral-600 mt-2 font-mono leading-relaxed">
                        Trigger a Photo or Reel draft above to generate and cache visual media.
                      </p>
                    </div>
                  )}
                </div>
                {lastPost?.media_url && (
                  <a 
                    href={lastPost.media_url} 
                    download={`maya_rossi_${lastPost.post_type}_draft.${lastPost.post_type === 'reel' ? 'mp4' : 'jpg'}`}
                    className="w-full text-center bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-450 hover:to-teal-450 text-neutral-950 font-mono text-[11px] font-bold py-2.5 rounded-lg mt-4 block transition duration-300 shadow-md animate-pulse"
                  >
                    Download Draft Media
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Webhook & Auto-DM Simulator */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl flex flex-col justify-between space-y-6">
            <div>
              <h2 className="text-sm uppercase tracking-widest text-neutral-400 flex items-center gap-2 font-mono">
                <MessageSquare size={16} className="text-emerald-400" /> Auto-DM Hook Simulator
              </h2>
              <p className="text-neutral-400 text-xs mt-2 leading-relaxed">
                Test your money-making comments hook locally! Type a comment with words like <span className="text-purple-400">style</span>, <span className="text-purple-400">link</span>, or <span className="text-purple-400">outfit</span> to see the auto-responder lookup your active affiliate catalog items.
              </p>

              {/* Simulated Fields */}
              <div className="mt-4 space-y-3">
                <div>
                  <label className="text-[10px] uppercase tracking-wider text-neutral-500 font-mono">Instagram Username</label>
                  <input
                    type="text"
                    value={simUsername}
                    onChange={(e) => setSimUsername(e.target.value)}
                    className="w-full mt-1 bg-neutral-950 border border-neutral-850 px-3.5 py-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-wider text-neutral-500 font-mono">User Comment</label>
                  <input
                    type="text"
                    value={simComment}
                    onChange={(e) => setSimComment(e.target.value)}
                    className="w-full mt-1 bg-neutral-950 border border-neutral-850 px-3.5 py-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <button
                onClick={runWebhookSimulation}
                disabled={simulating}
                className="w-full bg-purple-600 hover:bg-purple-550 text-white font-mono text-xs py-3 rounded-xl font-bold transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Send size={14} /> Send Webhook Comment
              </button>

              {/* Simulation Result display */}
              {webhookResult && (
                <div className="mt-4 p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl space-y-2 animate-fadeIn">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <span className="text-purple-400">Webhook Status: MATCHED</span>
                    <span className="text-neutral-500">Keyword: "{webhookResult.trigger_keyword}"</span>
                  </div>
                  <p className="text-xs text-neutral-200 leading-relaxed font-sans italic bg-neutral-950/70 p-3 rounded border border-neutral-900">
                    "{webhookResult.dm_sent}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Strategy Memory & Live Growth Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Live Strategy Optimization Engine Brief */}
          <div className="lg:col-span-2 bg-[#14141b]/60 backdrop-blur-xl p-8 rounded-2xl border border-neutral-800/60 shadow-2xl space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="text-purple-400 animate-pulse" size={20} />
              <h2 className="text-lg font-medium text-white">Algorithmic Performance Strategy Monitor</h2>
            </div>
            <p className="text-neutral-400 text-xs">
              Live feedback guidelines compiled dynamically from your professional Instagram metrics. Sourced directly by the Researcher agent during autopilot post generation cycles.
            </p>
            <div className="bg-neutral-950 p-5 rounded-xl border border-neutral-900 max-h-72 overflow-y-auto">
              <pre className="text-xs text-neutral-300 font-mono leading-relaxed whitespace-pre-wrap">
                {analyticsBrief || "Loading performance strategy directives..."}
              </pre>
            </div>
          </div>

          {/* Historical Memory Log Table */}
          <div className="bg-[#14141b]/60 backdrop-blur-xl p-6 rounded-2xl border border-neutral-800/60 shadow-2xl space-y-4">
            <h2 className="text-sm uppercase tracking-widest text-neutral-400 flex items-center gap-2 font-mono">
              <MessageSquare size={16} className="text-emerald-400" /> Algorithmic Memory Log
            </h2>
            <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
              <table className="w-full text-[11px] font-mono text-left">
                <thead>
                  <tr className="border-b border-neutral-850 text-neutral-500">
                    <th className="pb-2">ID</th>
                    <th className="pb-2">Location</th>
                    <th className="pb-2 text-right">Reach</th>
                    <th className="pb-2 text-right">ER %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/60 text-neutral-300">
                  {history.length > 0 ? (
                    history.slice().reverse().map((entry) => (
                      <tr key={entry.post_id} className="hover:bg-neutral-900/40">
                        <td className="py-2.5 font-bold">{entry.post_id.slice(-4)}</td>
                        <td className="py-2.5">{entry.location}</td>
                        <td className="py-2.5 text-right">{entry.metrics?.reach?.toLocaleString()}</td>
                        <td className="py-2.5 text-right text-emerald-400">{entry.engagement_rate}%</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-neutral-500">No logs stored yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Outfit Catalog Display */}
        <div className="bg-[#14141b]/60 backdrop-blur-xl p-8 rounded-2xl border border-neutral-800/60 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <ShoppingBag className="text-emerald-400" size={20} />
            <h2 className="text-lg font-medium text-white">Maya Rossi's Wardrobe & Affiliate Catalog</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {catalog.map((item) => (
              <div key={item.id} className="bg-neutral-950/60 p-5 rounded-xl border border-neutral-900 flex flex-col justify-between hover:border-neutral-800 transition duration-300">
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-neutral-900 border border-neutral-850 text-neutral-400">
                      {item.category}
                    </span>
                    <span className="text-xs font-bold text-emerald-400 font-mono">{item.price}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white mt-2">{item.name}</h3>
                  <p className="text-[11px] text-neutral-400 leading-relaxed italic">
                    "{item.visual_description}"
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-neutral-900/60 flex justify-between items-center text-xs">
                  <span className="text-[10px] text-neutral-500 font-mono">{item.brand}</span>
                  <a 
                    href={item.affiliate_link}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-400 hover:text-emerald-300 font-mono text-[11px] underline flex items-center gap-1"
                  >
                    View Affiliate Link
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
