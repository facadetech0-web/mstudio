import React, { useState } from 'react';
import { Sparkles, Video, Settings, ChevronDown, ChevronUp, RefreshCw, Wand2, Layers, Film } from 'lucide-react';
import { Scene, Shot, Clip } from '../types';

interface GenerationPanelProps {
  currentScene: Scene | null;
  currentShot: Shot | null;
  selectedClip: Clip | null;
  timelineClips: Clip[];
  aiStatus: { ok: boolean; configured: boolean; model?: string; latency_ms?: number; error?: string } | null;
  onCheckAIStatus: () => void;
  isCheckingAI: boolean;
  onPlanMovieStory: (prompt: string, numScenes: number) => Promise<void>;
  onGenerateVideo: (
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
  timelineClips,
  aiStatus,
  onCheckAIStatus,
  isCheckingAI,
  onPlanMovieStory,
  onGenerateVideo,
  onEnhancePrompt,
  isGenerating
}) => {
  // Story premise & AI Director Prompt state
  const [storyPrompt, setStoryPrompt] = useState(
    currentShot?.description ||
    selectedClip?.description ||
    'A lone explorer navigates through a misty ancient ruin, discovering an illuminated celestial artifact.'
  );
  const [numScenes, setNumScenes] = useState<number>(3);
  const [isWritingStory, setIsWritingStory] = useState<boolean>(false);

  // Active scene video prompt state
  const [activeClipPrompt, setActiveClipPrompt] = useState<string>(
    selectedClip?.video_prompt || selectedClip?.description || storyPrompt
  );

  // Sync active clip prompt when selection changes
  React.useEffect(() => {
    if (selectedClip) {
      setActiveClipPrompt(selectedClip.video_prompt || selectedClip.description || '');
    }
  }, [selectedClip?.id]);

  // Advanced generation parameters for CogVideoX-5B
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [steps, setSteps] = useState<number>(25);
  const [frames, setFrames] = useState<number>(49);
  const [seed, setSeed] = useState<string>('');
  const [negativePrompt, setNegativePrompt] = useState<string>(
    'blurry, low quality, distorted, deformed, artifacts, watermark'
  );
  const [loraPath, setLoraPath] = useState<string>('');
  const [isEnhancing, setIsEnhancing] = useState<boolean>(false);

  const handleEnhance = async () => {
    if (!activeClipPrompt.trim()) return;
    setIsEnhancing(true);
    try {
      const res = await onEnhancePrompt(activeClipPrompt);
      if (res && res.video) {
        setActiveClipPrompt(res.video);
      }
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleWriteStory = async () => {
    if (!storyPrompt.trim()) return;
    setIsWritingStory(true);
    try {
      await onPlanMovieStory(storyPrompt.trim(), numScenes);
    } finally {
      setIsWritingStory(false);
    }
  };

  const handleGenerateCurrent = () => {
    onGenerateVideo(
      selectedClip?.id,
      steps,
      frames,
      seed ? parseInt(seed, 10) : undefined,
      negativePrompt.trim() || undefined,
      loraPath.trim() || undefined
    );
  };

  return (
    <div className="w-84 bg-studio-900 border-l border-studio-800 flex flex-col h-[calc(100vh-3.5rem)] select-none">
      {/* Panel Header */}
      <div className="p-3 border-b border-studio-800 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-studio-400 font-semibold flex items-center space-x-1.5">
          <Wand2 className="w-3.5 h-3.5 text-studio-gold" />
          <span>Prompt & Story Director</span>
        </span>
        <span className="text-[10px] text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30 font-semibold font-mono">
          CogVideoX-5B
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-studio-200">
        {/* OpenRouter AI Connection Status Signal Box */}
        <div className={`p-2.5 rounded-lg border flex items-center justify-between transition ${
          aiStatus?.ok
            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${aiStatus?.ok ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <span className="font-semibold block text-[11px]">
                {aiStatus?.ok ? `OpenRouter AI Active (${aiStatus.model || 'Qwen 3.5'})` : 'OpenRouter AI Disconnected'}
              </span>
              <span className="text-[10px] opacity-75">
                {aiStatus?.ok ? `Latency: ${aiStatus.latency_ms || 120}ms • Ready` : (aiStatus?.error || 'Check API Key')}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onCheckAIStatus}
            disabled={isCheckingAI}
            className="px-2 py-1 bg-studio-800 hover:bg-studio-700 text-[10px] font-semibold text-white rounded border border-studio-700 flex items-center space-x-1 transition"
            title="Check OpenRouter AI prompt connection"
          >
            <RefreshCw className={`w-3 h-3 ${isCheckingAI ? 'animate-spin' : ''}`} />
            <span>{isCheckingAI ? '...' : 'Signal'}</span>
          </button>
        </div>

        {/* SECTION 1: Story Premise & Multi-Scene AI Writer */}
        <div className="bg-studio-850 p-3 rounded-lg border border-studio-750 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-white flex items-center space-x-1.5">
              <Film className="w-3.5 h-3.5 text-studio-gold" />
              <span>Story Premise</span>
            </label>
            <span className="text-[10px] text-studio-400 font-mono">Qwen 3.5 AI</span>
          </div>

          <textarea
            rows={3}
            value={storyPrompt}
            onChange={(e) => setStoryPrompt(e.target.value)}
            placeholder="Type your movie premise or story idea..."
            className="w-full bg-studio-900 border border-studio-700 text-xs text-white rounded p-2.5 focus:outline-none focus:border-studio-gold resize-none leading-relaxed"
          />

          {/* Option to choose how many scenes (1-10) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-studio-300 font-medium text-[11px]">Number of Scenes to Write</span>
              <span className="text-studio-gold font-bold font-mono text-xs px-2 py-0.5 bg-studio-900 rounded border border-studio-700">
                {numScenes} {numScenes === 1 ? 'Scene' : 'Scenes'}
              </span>
            </div>

            <div className="grid grid-cols-5 gap-1 pt-1">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setNumScenes(n)}
                  className={`py-1 rounded text-[11px] font-bold transition ${
                    numScenes === n
                      ? 'bg-studio-gold text-studio-950 shadow-sm'
                      : 'bg-studio-800 hover:bg-studio-750 text-studio-300'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Write Story Button */}
          <button
            onClick={handleWriteStory}
            disabled={isWritingStory || !storyPrompt.trim()}
            className="w-full py-2 bg-gradient-to-r from-amber-600 to-studio-gold hover:from-amber-500 hover:to-amber-400 disabled:opacity-50 text-studio-950 font-bold text-xs uppercase tracking-wider rounded shadow flex items-center justify-center space-x-1.5 transition"
          >
            <Sparkles className="w-3.5 h-3.5 fill-studio-950" />
            <span>{isWritingStory ? `AI Writing ${numScenes} Scenes...` : `Write Story (${numScenes} Scenes)`}</span>
          </button>
        </div>

        {/* SECTION 2: Active Scene Video Prompt & CogVideoX-5B Render */}
        <div className="space-y-3 pt-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-studio-gold" />
              <span>Active Scene Prompt</span>
            </span>
            <button
              onClick={handleEnhance}
              disabled={isEnhancing || !activeClipPrompt.trim()}
              className="text-[11px] text-amber-400 hover:text-amber-300 flex items-center space-x-1 disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3" />
              <span>{isEnhancing ? 'Enhancing...' : 'Enhance'}</span>
            </button>
          </div>

          <textarea
            rows={3}
            value={activeClipPrompt}
            onChange={(e) => setActiveClipPrompt(e.target.value)}
            placeholder="Scene video prompt for CogVideoX-5B..."
            className="w-full bg-studio-850 border border-studio-700 text-xs text-white rounded p-2.5 focus:outline-none focus:border-studio-gold resize-none leading-relaxed"
          />

          {/* SINGLE UNIFIED PRIMARY ACTION: Generate Video (CogVideoX-5B) */}
          <button
            onClick={handleGenerateCurrent}
            disabled={isGenerating}
            className="w-full py-3 bg-studio-cinema hover:bg-rose-600 disabled:opacity-50 text-white font-bold text-xs uppercase tracking-wider rounded-lg shadow-lg flex items-center justify-center space-x-2 transition transform active:scale-98"
          >
            <Video className="w-4 h-4" />
            <span>{isGenerating ? 'Generating Video...' : '🎬 Generate Video (CogVideoX-5B)'}</span>
          </button>
        </div>

        {/* SECTION 3: Collapsible Advanced Settings */}
        <div className="border border-studio-800 rounded-lg overflow-hidden bg-studio-850">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-3 py-2 flex items-center justify-between text-xs text-studio-400 hover:text-white font-medium"
          >
            <span className="flex items-center space-x-1.5">
              <Settings className="w-3.5 h-3.5" />
              <span>Model & Quality Settings</span>
            </span>
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showAdvanced && (
            <div className="p-3 border-t border-studio-800 space-y-3 text-xs">
              <div>
                <label className="text-studio-400 block mb-1">Negative Prompt</label>
                <textarea
                  rows={2}
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="blurry, distorted, low quality, artifacts"
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded p-1.5 text-[11px] focus:outline-none resize-none"
                />
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Custom LoRA Weights (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. models/loras/cinematic.safetensors"
                  value={loraPath}
                  onChange={(e) => setLoraPath(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2 py-1 text-[11px] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-studio-400 block mb-1">Steps ({steps})</label>
                  <input
                    type="range"
                    min={15}
                    max={50}
                    value={steps}
                    onChange={(e) => setSteps(parseInt(e.target.value, 10))}
                    className="w-full accent-rose-500 h-1 bg-studio-700 rounded"
                  />
                </div>
                <div>
                  <label className="text-studio-400 block mb-1">Frames ({frames})</label>
                  <input
                    type="range"
                    min={25}
                    max={49}
                    step={8}
                    value={frames}
                    onChange={(e) => setFrames(parseInt(e.target.value, 10))}
                    className="w-full accent-rose-500 h-1 bg-studio-700 rounded"
                  />
                </div>
              </div>

              <div>
                <label className="text-studio-400 block mb-1">Random Seed (Optional)</label>
                <input
                  type="number"
                  placeholder="Random"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2 py-1 text-[11px] focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
