import React from 'react';
import { Film, Sparkles, Download, Cpu, Activity, ListOrdered, CheckCircle2 } from 'lucide-react';
import { Project, SystemDiagnostics } from '../types';

interface TopBarProps {
  currentProject: Project | null;
  diagnostics: SystemDiagnostics | null;
  activeJobsCount: number;
  onOpenAIDirector: () => void;
  onOpenDiagnostics: () => void;
  onOpenBenchmark: () => void;
  onOpenJobQueue: () => void;
  onExportMovie: () => void;
  isExporting: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentProject,
  diagnostics,
  activeJobsCount,
  onOpenAIDirector,
  onOpenDiagnostics,
  onOpenBenchmark,
  onOpenJobQueue,
  onExportMovie,
  isExporting
}) => {
  return (
    <header className="h-14 bg-studio-900 border-b border-studio-800 px-4 flex items-center justify-between z-20">
      {/* Brand & Project Info */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-studio-gold font-bold tracking-wider text-base">
          <Film className="w-5 h-5 text-studio-gold" />
          <span>AI MOVIE STUDIO</span>
        </div>

        <div className="h-4 w-px bg-studio-700 mx-2" />

        <div className="flex items-center space-x-2">
          <span className="text-xs text-studio-500 uppercase tracking-wider font-semibold">PROJECT</span>
          <span className="text-sm font-medium text-white px-2 py-0.5 bg-studio-850 rounded border border-studio-700">
            {currentProject ? currentProject.name : 'No Project Selected'}
          </span>
          {currentProject?.genre && (
            <span className="text-xs text-studio-400 bg-studio-800 px-2 py-0.5 rounded">
              {currentProject.genre}
            </span>
          )}
        </div>
      </div>

      {/* Primary Actions & Hardware Indicators */}
      <div className="flex items-center space-x-3">
        {/* Hardware Status Tag */}
        <button
          onClick={onOpenDiagnostics}
          className="flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded bg-studio-850 hover:bg-studio-800 border border-studio-700 text-studio-400 transition"
          title="Hardware Diagnostics & T4 Status"
        >
          <Cpu className="w-3.5 h-3.5 text-emerald-400" />
          <span>
            {diagnostics?.gpu_name ? diagnostics.gpu_name.replace('NVIDIA ', '') : (diagnostics?.cuda_available ? 'CUDA Active' : 'CPU Mode')}
          </span>
          {diagnostics?.gpu_total_vram_gb && (
            <span className="text-emerald-400 font-mono text-[11px]">
              {diagnostics.gpu_total_vram_gb} GB
            </span>
          )}
        </button>

        {/* Real Benchmark Mode */}
        <button
          onClick={onOpenBenchmark}
          className="flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded bg-studio-850 hover:bg-studio-800 border border-studio-700 text-studio-400 transition"
          title="GPU Benchmark Tool"
        >
          <Activity className="w-3.5 h-3.5 text-amber-400" />
          <span>Benchmark</span>
        </button>

        {/* Job Queue Drawer Button */}
        <button
          onClick={onOpenJobQueue}
          className="relative flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded bg-studio-850 hover:bg-studio-800 border border-studio-700 text-studio-400 transition"
        >
          <ListOrdered className="w-3.5 h-3.5 text-studio-accent" />
          <span>Queue</span>
          {activeJobsCount > 0 && (
            <span className="w-4 h-4 text-[10px] bg-studio-cinema text-white font-bold rounded-full flex items-center justify-center animate-pulse">
              {activeJobsCount}
            </span>
          )}
        </button>

        {/* PROMINENT AI DIRECTOR BUTTON (Requirement #55) */}
        <button
          onClick={onOpenAIDirector}
          className="flex items-center space-x-2 px-3.5 py-1.5 bg-gradient-to-r from-amber-600 to-studio-gold hover:from-amber-500 hover:to-amber-400 text-studio-950 font-semibold text-xs uppercase tracking-wider rounded shadow-md transition transform hover:-translate-y-0.5 active:translate-y-0"
        >
          <Sparkles className="w-4 h-4 fill-studio-950" />
          <span>AI DIRECTOR</span>
        </button>

        {/* Export Final Movie Button */}
        <button
          onClick={onExportMovie}
          disabled={isExporting}
          className="flex items-center space-x-2 px-3.5 py-1.5 bg-studio-cinema hover:bg-rose-600 disabled:opacity-50 text-white font-semibold text-xs uppercase tracking-wider rounded shadow transition"
        >
          <Download className="w-4 h-4" />
          <span>{isExporting ? 'Exporting...' : 'Export Movie'}</span>
        </button>
      </div>
    </header>
  );
};
