import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, CheckCircle, XCircle, RefreshCw, Upload, Image as ImageIcon, Video, Film } from 'lucide-react';
import { Clip } from '../types';

interface PreviewPlayerProps {
  clip: Clip | null;
  onApprove: (clipId: string) => void;
  onReject: (clipId: string) => void;
  onRegenerate: (clipId: string) => void;
  onUploadReference: (clipId: string, file: File) => void;
}

export const PreviewPlayer: React.FC<PreviewPlayerProps> = ({
  clip,
  onApprove,
  onReject,
  onRegenerate,
  onUploadReference
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeMediaSource, setActiveMediaSource] = useState<'preview' | 'final'>('preview');

  useEffect(() => {
    setIsPlaying(false);
    if (clip?.final_file) {
      setActiveMediaSource('final');
    } else {
      setActiveMediaSource('preview');
    }
  }, [clip?.id, clip?.preview_file, clip?.final_file]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const normalizePath = (p?: string): string | null => {
    if (!p) return null;
    let clean = p.replace(/\\/g, '/');
    if (!clean.startsWith('/')) {
      clean = '/' + clean;
    }
    return clean;
  };

  const currentVideoSrc = activeMediaSource === 'final' && clip?.final_file
    ? normalizePath(clip.final_file)
    : clip?.preview_file ? normalizePath(clip.preview_file) : null;

  return (
    <div className="flex-1 flex flex-col bg-studio-950 p-4 h-[calc(100vh-3.5rem)] overflow-y-auto">
      {/* Player Header */}
      <div className="flex items-center justify-between pb-3 border-b border-studio-850">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold text-white">
              {clip ? `Clip #${clip.clip_number}` : 'No Clip Selected'}
            </span>
            {clip && (
              <span className={`px-2 py-0.5 text-[11px] font-semibold rounded uppercase tracking-wider ${
                clip.preview_status === 'Approved' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                clip.preview_status === 'Rejected' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                clip.preview_status === 'Ready' ? 'bg-blue-950 text-blue-400 border border-blue-800' :
                clip.preview_status === 'Generating' ? 'bg-amber-950 text-amber-400 border border-amber-800 animate-pulse' :
                'bg-studio-800 text-studio-400 border border-studio-700'
              }`}>
                {clip.preview_status}
              </span>
            )}
          </div>
          <p className="text-xs text-studio-400 mt-0.5 line-clamp-1">
            {clip?.description || 'Select or generate a clip to preview cinematic motion'}
          </p>
        </div>

        {/* Quality Mode Switcher */}
        {clip && (
          <div className="flex items-center space-x-2 bg-studio-900 p-1 rounded border border-studio-800 text-xs">
            <button
              onClick={() => setActiveMediaSource('preview')}
              className={`px-2.5 py-1 rounded transition font-medium ${
                activeMediaSource === 'preview'
                  ? 'bg-studio-700 text-white'
                  : 'text-studio-400 hover:text-white'
              }`}
            >
              Preview (2B)
            </button>
            <button
              onClick={() => setActiveMediaSource('final')}
              disabled={!clip.final_file}
              className={`px-2.5 py-1 rounded transition font-medium ${
                activeMediaSource === 'final'
                  ? 'bg-studio-cinema text-white'
                  : clip.final_file ? 'text-studio-400 hover:text-white' : 'text-studio-600 cursor-not-allowed'
              }`}
            >
              Final (5B-I2V)
            </button>
          </div>
        )}
      </div>

      {/* Main Cinema Viewport */}
      <div className="flex-1 flex items-center justify-center my-4 min-h-[360px] bg-studio-900 border border-studio-800 rounded-lg relative overflow-hidden group shadow-2xl">
        {currentVideoSrc ? (
          <div className="relative w-full h-full flex items-center justify-center bg-black">
            <video
              ref={videoRef}
              src={currentVideoSrc}
              className="max-h-full max-w-full rounded object-contain"
              loop
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onClick={togglePlay}
            />

            {/* Play Overlay Button */}
            {!isPlaying && (
              <button
                onClick={togglePlay}
                className="absolute inset-0 m-auto w-14 h-14 bg-studio-950/80 hover:bg-studio-cinema text-white rounded-full flex items-center justify-center transition shadow-lg backdrop-blur-sm"
              >
                <Play className="w-6 h-6 ml-1 fill-white" />
              </button>
            )}

            {/* Bottom Floating Playback Toolbar */}
            <div className="absolute bottom-3 inset-x-4 bg-studio-950/80 backdrop-blur border border-studio-800/80 rounded px-3 py-1.5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition">
              <div className="flex items-center space-x-2">
                <button onClick={togglePlay} className="p-1 text-white hover:text-studio-gold">
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = 0;
                      videoRef.current.play();
                    }
                  }}
                  className="p-1 text-studio-400 hover:text-white"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <span className="text-xs text-studio-400 font-mono">
                  {clip?.duration ? `${clip.duration.toFixed(1)}s` : '5.0s'}
                </span>
              </div>

              <div className="text-[11px] uppercase tracking-wider text-studio-400">
                {activeMediaSource === 'final' ? 'CogVideoX-5B-I2V Render' : 'CogVideoX-2B Preview'}
              </div>
            </div>
          </div>
        ) : clip?.reference_image ? (
          <div className="relative w-full h-full flex flex-col items-center justify-center p-6 bg-studio-950">
            <img
              src={`/${clip.reference_image}`}
              alt="Reference"
              className="max-h-64 object-contain rounded border border-studio-800 shadow"
            />
            <div className="mt-3 text-center">
              <span className="text-xs font-semibold text-studio-gold uppercase tracking-wider">
                Reference Frame Loaded
              </span>
              <p className="text-xs text-studio-400 mt-1 max-w-md">
                Click "Generate Preview" or "Generate Final" in the right panel to synthesize motion.
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center p-8 text-studio-500 max-w-md">
            <Film className="w-12 h-12 mx-auto mb-3 text-studio-700" />
            <h4 className="text-sm font-semibold text-studio-300">No Rendered Media Yet</h4>
            <p className="text-xs text-studio-400 mt-1">
              {clip
                ? 'Use the AI Generation Panel on the right to synthesize preview video with CogVideoX-2B.'
                : 'Choose a scene and shot to inspect or generate clips.'}
            </p>
            {clip && (
              <div className="mt-4 flex items-center justify-center space-x-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-3 py-1.5 rounded bg-studio-850 hover:bg-studio-800 border border-studio-700 text-xs text-studio-300 hover:text-white flex items-center space-x-1.5 transition"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload Reference Frame</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Hidden File Input for Reference Upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0] && clip) {
            onUploadReference(clip.id, e.target.files[0]);
          }
        }}
      />

      {/* Review & Approval Controls for Selected Clip */}
      {clip && (
        <div className="bg-studio-900 border border-studio-800 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs uppercase tracking-wider text-studio-500 font-semibold">CLIP REVIEW:</span>
            <button
              onClick={() => onApprove(clip.id)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-900/60 hover:bg-emerald-800 border border-emerald-700 text-emerald-300 text-xs font-medium transition"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Approve Clip</span>
            </button>
            <button
              onClick={() => onReject(clip.id)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-rose-900/60 hover:bg-rose-800 border border-rose-700 text-rose-300 text-xs font-medium transition"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Reject</span>
            </button>
            <button
              onClick={() => onRegenerate(clip.id)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-studio-800 hover:bg-studio-700 border border-studio-700 text-studio-200 text-xs font-medium transition"
              title="Regenerate only this clip"
            >
              <RefreshCw className="w-3.5 h-3.5 text-studio-gold" />
              <span>Regenerate Single Clip</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded bg-studio-850 hover:bg-studio-800 border border-studio-700 text-studio-300 text-xs transition"
            >
              <ImageIcon className="w-3.5 h-3.5" />
              <span>{clip.reference_image ? 'Change Reference' : 'Add Reference'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Continuity & Prompt Details Inspector */}
      {clip && (
        <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 bg-studio-900 border border-studio-850 rounded">
            <span className="text-[10px] uppercase tracking-wider text-studio-500 font-semibold block mb-1">
              IMAGE PROMPT (Composition & Appearance)
            </span>
            <p className="text-studio-300 line-clamp-3 font-mono text-[11px] leading-relaxed">
              {clip.image_prompt || 'No image prompt defined'}
            </p>
          </div>
          <div className="p-3 bg-studio-900 border border-studio-850 rounded">
            <span className="text-[10px] uppercase tracking-wider text-studio-500 font-semibold block mb-1">
              VIDEO PROMPT (Camera Dynamics & Motion)
            </span>
            <p className="text-studio-300 line-clamp-3 font-mono text-[11px] leading-relaxed">
              {clip.video_prompt || 'No video prompt defined'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
