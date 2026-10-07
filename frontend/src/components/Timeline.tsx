import React from 'react';
import { Play, Pause, ArrowLeft, ArrowRight, Trash2, CheckCircle2, XCircle, RefreshCw, Film, Plus } from 'lucide-react';
import { Clip } from '../types';

interface TimelineProps {
  clips: Clip[];
  selectedClip: Clip | null;
  onSelectClip: (clip: Clip) => void;
  onMoveClip: (clipIndex: number, direction: 'left' | 'right') => void;
  onDeleteClip: (clipId: string) => void;
  onApproveClip: (clipId: string) => void;
  onRejectClip: (clipId: string) => void;
  onRegenerateClip: (clipId: string) => void;
}

export const Timeline: React.FC<TimelineProps> = ({
  clips,
  selectedClip,
  onSelectClip,
  onMoveClip,
  onDeleteClip,
  onApproveClip,
  onRejectClip,
  onRegenerateClip
}) => {
  const totalTimelineDuration = clips.reduce((acc, c) => acc + (c.duration || 5.0), 0);

  return (
    <footer className="h-44 bg-studio-900 border-t border-studio-800 flex flex-col z-10 select-none">
      {/* Timeline Controls Header */}
      <div className="h-8 px-4 bg-studio-850 border-b border-studio-800 flex items-center justify-between text-xs text-studio-400">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-white uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
            <Film className="w-3.5 h-3.5 text-studio-gold" />
            <span>Timeline</span>
          </span>
          <span className="text-studio-500">•</span>
          <span>{clips.length} Clips</span>
          <span className="text-studio-500">•</span>
          <span className="font-mono text-white">Total: {totalTimelineDuration.toFixed(1)}s</span>
        </div>

        <div className="flex items-center space-x-2 text-[11px]">
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Approved</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            <span>Preview Ready</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-studio-cinema" />
            <span>Final Ready</span>
          </span>
        </div>
      </div>

      {/* Horizontal Clips Track */}
      <div className="flex-1 overflow-x-auto p-3 flex items-center space-x-3">
        {clips.length === 0 ? (
          <div className="flex-1 text-center text-xs text-studio-500 py-4">
            No clips in timeline. Plan scenes or break prompts into clips using AI Director.
          </div>
        ) : (
          clips.map((clip, index) => {
            const isSelected = selectedClip?.id === clip.id;
            return (
              <div
                key={clip.id}
                onClick={() => onSelectClip(clip)}
                className={`min-w-[170px] w-44 h-28 bg-studio-850 rounded-lg border transition flex flex-col justify-between p-2 cursor-pointer relative group ${
                  isSelected
                    ? 'border-studio-gold ring-1 ring-studio-gold shadow-lg shadow-studio-gold/10'
                    : 'border-studio-750 hover:border-studio-600'
                }`}
              >
                {/* Clip Card Top Bar */}
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-white font-mono">
                    #{index + 1} Clip
                  </span>

                  {/* Status Indicator */}
                  <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    clip.final_status === 'Ready' ? 'bg-studio-cinema text-white' :
                    clip.preview_status === 'Approved' ? 'bg-emerald-900 text-emerald-300' :
                    clip.preview_status === 'Ready' ? 'bg-blue-900 text-blue-300' :
                    clip.preview_status === 'Generating' ? 'bg-amber-900 text-amber-300 animate-pulse' :
                    clip.preview_status === 'Rejected' ? 'bg-rose-900 text-rose-300' :
                    'bg-studio-800 text-studio-400'
                  }`}>
                    {clip.final_status === 'Ready' ? 'Final' : clip.preview_status}
                  </span>
                </div>

                {/* Thumbnail / Description Preview */}
                <div className="my-1 flex-1 flex items-center justify-center bg-studio-900 rounded overflow-hidden relative">
                  {clip.reference_image ? (
                    <img
                      src={`/${clip.reference_image}`}
                      alt="Ref"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-[10px] text-studio-400 text-center line-clamp-2 px-1">
                      {clip.description || clip.video_prompt?.slice(0, 40) || 'Clip Prompt'}
                    </div>
                  )}

                  {/* Duration Tag */}
                  <span className="absolute bottom-1 right-1 bg-black/80 px-1 rounded text-[9px] font-mono text-studio-300">
                    {clip.duration ? `${clip.duration.toFixed(0)}s` : '5s'}
                  </span>
                </div>

                {/* Reordering & Action Buttons */}
                <div className="flex items-center justify-between pt-1 border-t border-studio-800 text-studio-400">
                  <div className="flex items-center space-x-1">
                    <button
                      disabled={index === 0}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveClip(index, 'left');
                      }}
                      className="p-0.5 hover:text-white disabled:opacity-30 disabled:hover:text-studio-400"
                      title="Move Left"
                    >
                      <ArrowLeft className="w-3 h-3" />
                    </button>
                    <button
                      disabled={index === clips.length - 1}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveClip(index, 'right');
                      }}
                      className="p-0.5 hover:text-white disabled:opacity-30 disabled:hover:text-studio-400"
                      title="Move Right"
                    >
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>

                  <div className="flex items-center space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onApproveClip(clip.id);
                      }}
                      className="p-0.5 hover:text-emerald-400"
                      title="Approve Clip"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRegenerateClip(clip.id);
                      }}
                      className="p-0.5 hover:text-studio-gold"
                      title="Regenerate only this clip"
                    >
                      <RefreshCw className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteClip(clip.id);
                      }}
                      className="p-0.5 hover:text-rose-400"
                      title="Delete Clip"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </footer>
  );
};
