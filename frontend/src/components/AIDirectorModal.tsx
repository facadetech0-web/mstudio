import React, { useState } from 'react';
import { X, Sparkles, BookOpen, Users, MapPin, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { Project, Scene } from '../types';

interface AIDirectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project | null;
  currentScene: Scene | null;
  onPlanMovie: (idea: string, genre: string) => Promise<void>;
  onCheckContinuity: (sceneId: string) => Promise<any>;
}

export const AIDirectorModal: React.FC<AIDirectorModalProps> = ({
  isOpen,
  onClose,
  project,
  currentScene,
  onPlanMovie,
  onCheckContinuity
}) => {
  const [activeTab, setActiveTab] = useState<'plan' | 'bible' | 'characters' | 'locations' | 'continuity'>('plan');
  const [movieIdea, setMovieIdea] = useState(
    project?.description ||
    'A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.'
  );
  const [genre, setGenre] = useState(project?.genre || 'Sci-Fi Mystery');
  const [isPlanning, setIsPlanning] = useState(false);
  const [continuityReport, setContinuityReport] = useState<any>(null);
  const [isCheckingContinuity, setIsCheckingContinuity] = useState(false);

  if (!isOpen) return null;

  const bible = project?.movie_bible || {};

  const handlePlan = async () => {
    if (!movieIdea.trim()) return;
    setIsPlanning(true);
    try {
      await onPlanMovie(movieIdea, genre);
      setActiveTab('bible');
    } finally {
      setIsPlanning(false);
    }
  };

  const handleCheck = async () => {
    if (!currentScene) return;
    setIsCheckingContinuity(true);
    try {
      const res = await onCheckContinuity(currentScene.id);
      setContinuityReport(res);
    } finally {
      setIsCheckingContinuity(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-6">
      <div className="bg-studio-900 border border-studio-700 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-studio-800 flex items-center justify-between bg-studio-950">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-studio-gold">
              <Sparkles className="w-5 h-5 fill-studio-gold" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white uppercase tracking-wider">
                AI DIRECTOR CONTROL HUB
              </h2>
              <p className="text-xs text-studio-400">
                OpenRouter Intelligence • Movie Bible • Continuity Engine
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-studio-800 text-studio-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 border-b border-studio-800 flex space-x-6 text-xs bg-studio-900">
          <button
            onClick={() => setActiveTab('plan')}
            className={`py-3 font-semibold transition border-b-2 ${
              activeTab === 'plan' ? 'border-studio-gold text-white' : 'border-transparent text-studio-400 hover:text-white'
            }`}
          >
            Story Planning
          </button>
          <button
            onClick={() => setActiveTab('bible')}
            className={`py-3 font-semibold transition border-b-2 ${
              activeTab === 'bible' ? 'border-studio-gold text-white' : 'border-transparent text-studio-400 hover:text-white'
            }`}
          >
            Movie Bible
          </button>
          <button
            onClick={() => setActiveTab('characters')}
            className={`py-3 font-semibold transition border-b-2 ${
              activeTab === 'characters' ? 'border-studio-gold text-white' : 'border-transparent text-studio-400 hover:text-white'
            }`}
          >
            Characters ({bible.characters?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('locations')}
            className={`py-3 font-semibold transition border-b-2 ${
              activeTab === 'locations' ? 'border-studio-gold text-white' : 'border-transparent text-studio-400 hover:text-white'
            }`}
          >
            Locations ({bible.locations?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('continuity')}
            className={`py-3 font-semibold transition border-b-2 ${
              activeTab === 'continuity' ? 'border-studio-gold text-white' : 'border-transparent text-studio-400 hover:text-white'
            }`}
          >
            Continuity Checker
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 text-xs text-studio-200">
          {/* TAB 1: Plan Story */}
          {activeTab === 'plan' && (
            <div className="max-w-2xl mx-auto space-y-4 py-4">
              <div className="p-4 bg-studio-850 rounded-lg border border-studio-750">
                <h3 className="text-sm font-bold text-white mb-1">High-Level Movie Premise</h3>
                <p className="text-studio-400 mb-3 text-xs leading-relaxed">
                  Enter your core movie idea. The AI Director will construct a professional Movie Bible,
                  establish visual continuity rules, create character designs, and break the story into scenes.
                </p>
                <textarea
                  rows={5}
                  value={movieIdea}
                  onChange={(e) => setMovieIdea(e.target.value)}
                  placeholder="e.g. A man enters an abandoned factory, walks through it, discovers an old machine and turns it on."
                  className="w-full bg-studio-900 border border-studio-700 text-xs text-white rounded p-3 focus:outline-none focus:border-studio-gold leading-relaxed"
                />

                <div className="mt-3 flex items-center space-x-3">
                  <div className="w-1/2">
                    <label className="text-studio-400 block mb-1">Genre</label>
                    <input
                      type="text"
                      value={genre}
                      onChange={(e) => setGenre(e.target.value)}
                      className="w-full bg-studio-900 border border-studio-700 text-xs text-white rounded p-2"
                    />
                  </div>
                </div>

                <div className="mt-5">
                  <button
                    onClick={handlePlan}
                    disabled={isPlanning || !movieIdea.trim()}
                    className="w-full py-2.5 bg-gradient-to-r from-amber-600 to-studio-gold hover:from-amber-500 hover:to-amber-400 disabled:opacity-50 text-studio-950 font-bold uppercase tracking-wider rounded shadow transition flex items-center justify-center space-x-2"
                  >
                    <Sparkles className="w-4 h-4 fill-studio-950" />
                    <span>{isPlanning ? 'AI Director Constructing Movie...' : 'Generate Full Movie Plan'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Movie Bible */}
          {activeTab === 'bible' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-studio-850 rounded-lg border border-studio-750 space-y-2">
                  <h4 className="text-xs font-bold text-studio-gold uppercase tracking-wider">Cinematic Style</h4>
                  <div>
                    <span className="text-studio-500 block">Visual Style:</span>
                    <span className="text-white">{bible.visual_style || 'Photorealistic 35mm film'}</span>
                  </div>
                  <div>
                    <span className="text-studio-500 block">Color Palette:</span>
                    <span className="text-white">{bible.color_palette || 'Muted industrial tones'}</span>
                  </div>
                  <div>
                    <span className="text-studio-500 block">Lighting:</span>
                    <span className="text-white">{bible.lighting_style || 'Volumetric natural key'}</span>
                  </div>
                </div>

                <div className="p-4 bg-studio-850 rounded-lg border border-studio-750 space-y-2">
                  <h4 className="text-xs font-bold text-studio-gold uppercase tracking-wider">Story Synopsis</h4>
                  <p className="text-studio-300 leading-relaxed">{bible.synopsis || project?.description}</p>
                </div>
              </div>

              {/* Continuity Rules */}
              <div className="p-4 bg-studio-850 rounded-lg border border-studio-750">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                  Global Continuity Rules
                </h4>
                <ul className="list-disc list-inside space-y-1 text-studio-300">
                  {bible.continuity_rules && bible.continuity_rules.length > 0 ? (
                    bible.continuity_rules.map((rule, idx) => <li key={idx}>{rule}</li>)
                  ) : (
                    <li>Maintain persistent wardrobe and environment lighting across all scenes.</li>
                  )}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 3: Characters */}
          {activeTab === 'characters' && (
            <div className="space-y-4">
              {bible.characters && bible.characters.length > 0 ? (
                bible.characters.map((char, i) => (
                  <div key={i} className="p-4 bg-studio-850 rounded-lg border border-studio-750 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{char.name}</span>
                      <span className="text-studio-500">{char.gender} • {char.age} yrs</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs pt-1">
                      <div>
                        <span className="text-studio-500 block">Clothing (Strict Continuity):</span>
                        <span className="text-amber-300">{char.clothing || 'Worn black leather jacket'}</span>
                      </div>
                      <div>
                        <span className="text-studio-500 block">Physical Description:</span>
                        <span className="text-white">{char.physical_description}</span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-studio-500">
                  No characters defined. Plan your story first.
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Locations */}
          {activeTab === 'locations' && (
            <div className="space-y-4">
              {bible.locations && bible.locations.length > 0 ? (
                bible.locations.map((loc, i) => (
                  <div key={i} className="p-4 bg-studio-850 rounded-lg border border-studio-750 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{loc.name}</span>
                      <span className="text-studio-500">{loc.interior_exterior} • {loc.time}</span>
                    </div>
                    <p className="text-studio-300">{loc.description}</p>
                    <div className="text-xs text-studio-400">
                      Architecture: <span className="text-white">{loc.architecture}</span> • Lighting: <span className="text-white">{loc.lighting}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-studio-500">
                  No locations defined. Plan your story first.
                </div>
              )}
            </div>
          )}

          {/* TAB 5: Continuity Checker (Requirement #56) */}
          {activeTab === 'continuity' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-studio-850 p-4 rounded-lg border border-studio-750">
                <div>
                  <h4 className="font-bold text-white">Scene Continuity Inspection</h4>
                  <p className="text-xs text-studio-400">
                    Runs AI inspection across character clothing, locations, and time-of-day.
                  </p>
                </div>
                <button
                  onClick={handleCheck}
                  disabled={isCheckingContinuity || !currentScene}
                  className="px-3.5 py-2 bg-studio-800 hover:bg-studio-750 border border-studio-700 text-white rounded font-medium flex items-center space-x-1.5 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 text-studio-gold ${isCheckingContinuity ? 'animate-spin' : ''}`} />
                  <span>Check Scene Continuity</span>
                </button>
              </div>

              {continuityReport && (
                <div className="p-4 bg-studio-850 rounded-lg border border-studio-750 space-y-3">
                  <div className="flex items-center space-x-2">
                    {continuityReport.is_consistent ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    )}
                    <span className="font-bold text-white">
                      {continuityReport.is_consistent ? 'All Continuity Checks Passed' : 'Continuity Inconsistencies Detected'}
                    </span>
                  </div>

                  {continuityReport.warnings?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider block">
                        Warnings:
                      </span>
                      {continuityReport.warnings.map((w: string, i: number) => (
                        <div key={i} className="text-amber-200/90 text-xs flex items-center space-x-1.5">
                          <span>⚠</span>
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                      Verified Checks:
                    </span>
                    {(continuityReport.character_checks || []).map((c: string, i: number) => (
                      <div key={i} className="text-emerald-200/90 text-xs flex items-center space-x-1.5">
                        <span>✓</span>
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
