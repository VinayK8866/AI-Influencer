"use client";

import { useState, useEffect } from "react";
import { Camera, Film, MapPin, Play, Settings, Sparkles } from "lucide-react";

export default function Home() {
  const [status, setStatus] = useState("Offline");
  const [location, setLocation] = useState("Loading...");
  const [loading, setLoading] = useState(false);
  const [storyboard, setStoryboard] = useState("");
  const [metadata, setMetadata] = useState("");

  useEffect(() => {
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        if (data.status) {
          setStatus("Online");
          setLocation(data.state?.current_location || "Mumbai");
        } else if (data.error) {
          // If the API is technically online but missing keys (e.g. GEMINI_API_KEY)
          setStatus("Online (Keys Missing)");
          setLocation("Error loading state");
          console.warn(data.error);
        }
      })
      .catch((err) => {
        console.error("API not available", err);
        setStatus("Offline");
      });
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
      } else {
        alert("Error: " + data.error);
      }
    } catch (err) {
      alert("Failed to connect to backend");
    }
    setLoading(false);
  };

  const triggerPost = async (type: string) => {
    alert(`Triggering ${type} cycle... Note: On Vercel this might timeout because Muapi takes minutes to render video.`);
    try {
      await fetch("/api/trigger-cycle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_type: type }),
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-900 text-neutral-100 font-sans p-8 md:p-16">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex justify-between items-center border-b border-neutral-800 pb-8">
          <div>
            <h1 className="text-3xl font-light tracking-wide text-white">
              MAYA <span className="font-semibold text-emerald-400">AUTOPILOT</span>
            </h1>
            <p className="text-neutral-400 mt-2 text-sm tracking-widest uppercase">
              Virtual Influencer Command Center
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm bg-neutral-800 px-4 py-2 rounded-full border border-neutral-700">
            <span className={`w-2 h-2 rounded-full ${status === 'Online' ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`}></span>
            System {status}
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* System State Card */}
          <div className="bg-neutral-800/50 p-6 rounded-2xl border border-neutral-800 shadow-xl">
            <h2 className="text-sm uppercase tracking-widest text-neutral-500 mb-4 flex items-center gap-2">
              <MapPin size={16} /> Current State
            </h2>
            <div className="text-2xl font-light">
              Location: <span className="text-emerald-400 font-medium">{location}</span>
            </div>
            <p className="text-neutral-400 text-sm mt-4">
              The AI will generate content matching the local aesthetic of {location}.
            </p>
          </div>

          {/* Quick Actions */}
          <div className="md:col-span-2 bg-neutral-800/50 p-6 rounded-2xl border border-neutral-800 shadow-xl flex flex-col justify-center">
            <h2 className="text-sm uppercase tracking-widest text-neutral-500 mb-4 flex items-center gap-2">
              <Play size={16} /> Manual Overrides
            </h2>
            <div className="flex gap-4">
              <button
                onClick={() => triggerPost('photo')}
                className="flex-1 bg-neutral-700 hover:bg-neutral-600 transition-colors py-4 rounded-xl flex items-center justify-center gap-2 font-medium"
              >
                <Camera size={18} /> Generate Photo
              </button>
              <button
                onClick={() => triggerPost('reel')}
                className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-neutral-900 transition-colors py-4 rounded-xl flex items-center justify-center gap-2 font-bold"
              >
                <Film size={18} /> Generate Reel (Muapi)
              </button>
            </div>
          </div>
        </div>

        {/* Agency Studio Section */}
        <div className="bg-neutral-800/50 p-8 rounded-2xl border border-neutral-800 shadow-xl">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-medium flex items-center gap-2">
              <Sparkles className="text-emerald-400" size={20} />
              The AI Agency Studio
            </h2>
            <button
              onClick={generateStoryboard}
              disabled={loading}
              className="bg-white text-black px-6 py-2 rounded-full font-medium text-sm hover:bg-neutral-200 transition disabled:opacity-50"
            >
              {loading ? "Agents Debating..." : "Draft New Storyboard"}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-neutral-900 p-6 rounded-xl border border-neutral-800">
              <h3 className="text-xs uppercase tracking-widest text-neutral-500 mb-4">Approved Storyboard</h3>
              <pre className="whitespace-pre-wrap text-sm text-neutral-300 font-mono">
                {storyboard || "Waiting for Creative Director..."}
              </pre>
            </div>
            <div className="bg-neutral-900 p-6 rounded-xl border border-neutral-800">
              <h3 className="text-xs uppercase tracking-widest text-neutral-500 mb-4">SEO & Metadata</h3>
              <pre className="whitespace-pre-wrap text-sm text-neutral-300 font-mono">
                {metadata || "Waiting for Operations Manager..."}
              </pre>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
