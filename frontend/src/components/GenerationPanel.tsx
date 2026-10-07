import React, { useState } from 'react';
import { Sparkles, Play, Video, Settings, ChevronDown, ChevronUp, Wand2, ShieldCheck } from 'lucide-react';
import { Scene, Shot, Clip } from '../types';

interface GenerationPanelProps {
  currentScene: Scene | null;
  currentShot: Shot | null;
  selectedClip: Clip | null;
  onBreakIntoClips: (prompt: string, count: number, duration: number) => void;
  onGeneratePreview: (
    clipId?: string,
    steps?: number,
    frames?: number,
    seed?: number,
    negativePrompt?: string,
    loraPath?: string
  ) => void;
  onGenerateFinal: (
    clipId?: string,
    steps?: number,
    frames?: number,
    seed?: number,
    negativePrompt?: string,
    loraPath?: string
  ) => void;
  onEnhancePrompt: (raw: string) => Promise<{ image: string; video: string } | null>;
  isGenerating: boolean;
}

export const GenerationPanel: React.FC<GenerationPanelProps> = ({
  currentScene,
  currentShot,
  selectedClip,
  onBreakIntoClips,
  onGeneratePreview,
  onGenerateFinal,
  onEnhancePrompt,
  isGenerating
}) => {
  const [prompt, setPrompt] = useState(
    currentShot?.description ||
    'A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.'
  );
  // CORE FEATURE: Number of Clips Slider (Requirement #14)
  const [clipCount, setClipCount] = useState<number>(1);
  const [clipDuration, setClipDuration] = useState<number>(5.0);

  // Advanced settings state (Requirement #53)
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [steps, setSteps] = useState<number>(15);
  const [frames, setFrames] = useState<number>(49);
  const [seed, setSeed] = useState<string>('');
  const [negativePrompt, setNegativePrompt] = useState<string>(
    'blurry, low quality, distorted, deformed, artifacts, watermark'
  );
  const [loraPath, setLoraPath] = useState<string>('');
  const [lowVramMode, setLowVramMode] = useState<boolean>(true);
  const [isEnhancing, setIsEnhancing] = useState<boolean>(false);

  const estimatedTotalDuration = clipCount * clipDuration;

  const handleEnhance = async () => {
    if (!prompt.trim()) return;
    setIsEnhancing(true);
    try {
      const res = await onEnhancePrompt(prompt);
      if (res && res.video) {
        setPrompt(res.video);
      }
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleBreakOrPlan = () => {
    if (prompt.trim()) {
      onBreakIntoClips(prompt.trim(), clipCount, clipDuration);
    }
  };

  return (
    <div className="w-80 bg-studio-900 border-l border-studio-800 flex flex-col h-[calc(100vh-3.5rem)] select-none">
      {/* Panel Header */}
      <div className="p-3 border-b border-studio-800 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-studio-400 font-semibold flex items-center space-x-1.5">
          <Wand2 className="w-3.5 h-3.5 text-studio-gold" />
          <span>AI & Generation</span>
        </span>
        <span className="text-[10px] text-studio-500 font-mono">T4 16GB Profile</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Main User Prompt Input */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-studio-300">Movie / Scene Prompt</label>
            <button
              onClick={handleEnhance}
              disabled={isEnhancing || !prompt.trim()}
              className="text-[11px] text-amber-400 hover:text-amber-300 flex items-center space-x-1 disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3" />
              <span>{isEnhancing ? 'Enhancing...' : 'Enhance Prompt'}</span>
            </button>
          </div>
          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your scene action or story progression..."
            className="w-full bg-studio-850 border border-studio-700 text-xs text-white rounded p-2.5 focus:outline-none focus:border-studio-gold resize-none leading-relaxed"
          />
        </div>

        {/* CORE FEATURE: Number of Clips Slider (Requirements #14, #15, #16) */}
        <div className="bg-studio-850 p-3 rounded-lg border border-studio-750">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-white">Number of Clips</span>
            <span className="text-xs font-bold text-studio-gold font-mono px-2 py-0.5 bg-studio-900 rounded border border-studio-700">
              {clipCount} {clipCount === 1 ? 'Clip' : 'Clips'}
            </span>
          </div>

          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={clipCount}
            onChange={(e) => setClipCount(parseInt(e.target.value, 10))}
            className="w-full h-1.5 bg-studio-700 rounded-lg cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-studio-500 mt-1 font-mono">
            <span>1</span>
            <span>5</span>
            <span>10</span>
          </div>

          {/* Clip Duration Selector */}
          <div className="mt-3 flex items-center justify-between text-xs">
            <span className="text-studio-400">Clip Duration:</span>
            <select
              value={clipDuration}
              onChange={(e) => setClipDuration(parseFloat(e.target.value))}
              className="bg-studio-900 border border-studio-700 text-white rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value={3.0}>3 seconds</option>
              <option value={5.0}>5 seconds</option>
              <option value={8.0}>8 seconds</option>
            </select>
          </div>

          {/* Estimated Total Duration calculation */}
          <div className="mt-2.5 pt-2 border-t border-studio-700/60 flex items-center justify-between text-xs">
            <span className="text-studio-400 font-medium">Estimated Total:</span>
            <span className="text-white font-mono font-semibold">
              ≈ {estimatedTotalDuration.toFixed(0)} seconds
            </span>
          </div>
        </div>

        {/* Multi-Clip Breakdown Action */}
        <button
          onClick={handleBreakOrPlan}
          className="w-full py-2 bg-studio-800 hover:bg-studio-700 border border-studio-700 text-studio-200 hover:text-white rounded text-xs font-semibold uppercase tracking-wider flex items-center justify-center space-x-1.5 transition"
        >
          <Sparkles className="w-3.5 h-3.5 text-studio-gold" />
          <span>
            {clipCount > 1 ? `AI Decompose into ${clipCount} Sequential Clips` : 'AI Plan Single Clip'}
          </span>
        </button>

        {/* Primary Generation Buttons */}
        <div className="space-y-2 pt-1">
          {/* Generate Preview (CogVideoX-2B) */}
          <button
            onClick={() => onGeneratePreview(
              selectedClip?.id,
              steps,
              frames,
              seed ? parseInt(seed, 10) : undefined,
              negativePrompt.trim() || undefined,
              loraPath.trim() || undefined
            )}
            disabled={isGenerating}
            className="w-full py-2.5 bg-studio-gold hover:bg-amber-400 disabled:opacity-50 text-studio-950 font-bold text-xs uppercase tracking-wider rounded shadow flex items-center justify-center space-x-2 transition"
          >
            <Play className="w-3.5 h-3.5 fill-studio-950" />
            <span>Generate Preview (CogVideoX-2B)</span>
          </button>

          {/* Generate Final (CogVideoX-5B-I2V) */}
          <button
            onClick={() => onGenerateFinal(
              selectedClip?.id,
              steps + 5,
              frames,
              seed ? parseInt(seed, 10) : undefined,
              negativePrompt.trim() || undefined,
              loraPath.trim() || undefined
            )}
            disabled={isGenerating}
            className="w-full py-2.5 bg-studio-cinema hover:bg-rose-600 disabled:opacity-50 text-white font-bold text-xs uppercase tracking-wider rounded shadow flex items-center justify-center space-x-2 transition"
          >
            <Video className="w-3.5 h-3.5" />
            <span>Generate Final (CogVideoX-5B-I2V)</span>
          </button>
        </div>

        {/* Collapsible Advanced Settings (Requirement #53) */}
        <div className="border border-studio-800 rounded-lg overflow-hidden bg-studio-850">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-3 py-2 flex items-center justify-between text-xs text-studio-400 hover:text-white font-medium"
          >
            <span className="flex items-center space-x-1.5">
              <Settings className="w-3.5 h-3.5" />
              <span>Advanced Settings</span>
            </span>
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showAdvanced && (
            <div className="p-3 border-t border-studio-800 space-y-3 text-xs">
              <div>
                <label className="text-studio-400 block mb-1">Negative Prompt (Quality & Artifact Suppression)</label>
                <textarea
                  rows={2}
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="blurry, distorted, low quality, artifacts, watermark"
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded p-1.5 text-[11px] focus:outline-none resize-none"
                />
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Custom LoRA Weights (Optional Path)</label>
                <input
                  type="text"
                  placeholder="e.g. models/loras/film_grain.safetensors"
                  value={loraPath}
                  onChange={(e) => setLoraPath(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2 py-1 text-[11px] focus:outline-none"
                />
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Inference Steps ({steps})</label>
                <input
                  type="range"
                  min={10}
                  max={50}
                  value={steps}
                  onChange={(e) => setSteps(parseInt(e.target.value, 10))}
                  className="w-full h-1 bg-studio-700 rounded"
                />
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Frames</label>
                <select
                  value={frames}
                  onChange={(e) => setFrames(parseInt(e.target.value, 10))}
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2 py-1"
                >
                  <option value={49}>49 frames (~6s @ 8fps)</option>
                  <option value={81}>81 frames (~10s @ 8fps)</option>
                </select>
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Seed (Optional)</label>
                <input
                  type="number"
                  placeholder="Random"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2 py-1"
                />
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-studio-400">T4 Low VRAM Mode:</span>
                <input
                  type="checkbox"
                  checked={lowVramMode}
                  onChange={(e) => setLowVramMode(e.target.checked)}
                  className="rounded text-studio-gold"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
