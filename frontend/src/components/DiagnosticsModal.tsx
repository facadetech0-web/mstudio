import React from 'react';
import { X, Cpu, CheckCircle2, AlertCircle, Trash2, HardDrive, Key, Layers } from 'lucide-react';
import { SystemDiagnostics } from '../types';

interface DiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  diagnostics: SystemDiagnostics | null;
  onUnloadModels: () => void;
}

export const DiagnosticsModal: React.FC<DiagnosticsModalProps> = ({
  isOpen,
  onClose,
  diagnostics,
  onUnloadModels
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-6">
      <div className="bg-studio-900 border border-studio-700 rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-studio-800 flex items-center justify-between bg-studio-950">
          <div className="flex items-center space-x-2.5">
            <Cpu className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              System Diagnostics & T4 Hardware Status
            </h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-studio-800 text-studio-400 hover:text-white rounded">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs">
          {/* Hardware & GPU */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-studio-850 rounded border border-studio-750">
              <span className="text-studio-500 uppercase tracking-wider text-[10px] block mb-1">
                GPU Accelerator
              </span>
              <div className="flex items-center space-x-2">
                {diagnostics?.cuda_available ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                )}
                <span className="text-white font-medium">
                  {diagnostics?.gpu_name || (diagnostics?.cuda_available ? 'CUDA Device' : 'CPU Mode (No GPU)')}
                </span>
              </div>
              <div className="mt-1 text-[11px] text-studio-400">
                VRAM: {diagnostics?.gpu_total_vram_gb ? `${diagnostics.gpu_total_vram_gb} GB Total` : 'N/A'}
              </div>
            </div>

            <div className="p-3 bg-studio-850 rounded border border-studio-750">
              <span className="text-studio-500 uppercase tracking-wider text-[10px] block mb-1">
                Video Tools (FFmpeg)
              </span>
              <div className="flex items-center space-x-2">
                {diagnostics?.ffmpeg_available ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                )}
                <span className="text-white font-medium">
                  {diagnostics?.ffmpeg_available ? 'FFmpeg Installed & Ready' : 'FFmpeg Not Detected'}
                </span>
              </div>
              <div className="mt-1 text-[11px] text-studio-400">
                Used for movie assembly & normalization
              </div>
            </div>
          </div>

          {/* AI Intelligence & Models */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-studio-850 rounded border border-studio-750">
              <span className="text-studio-500 uppercase tracking-wider text-[10px] block mb-1">
                OpenRouter AI Director
              </span>
              <div className="flex items-center space-x-2">
                {diagnostics?.openrouter_configured ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                )}
                <span className="text-white font-medium">
                  {diagnostics?.openrouter_configured ? 'API Key Configured' : 'Offline Mode (No Key)'}
                </span>
              </div>
              <div className="mt-1 text-[11px] text-studio-400 truncate">
                Model: {diagnostics?.openrouter_model}
              </div>
            </div>

            <div className="p-3 bg-studio-850 rounded border border-studio-750">
              <span className="text-studio-500 uppercase tracking-wider text-[10px] block mb-1">
                Generation Models
              </span>
              <div className="space-y-1 text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="text-studio-300">CogVideoX-2B (Preview):</span>
                  <span className="text-emerald-400">Configured</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-studio-300">CogVideoX-5B-I2V (Final):</span>
                  <span className="text-emerald-400">Configured</span>
                </div>
              </div>
            </div>
          </div>

          {/* T4 Optimizations Summary */}
          <div className="p-3 bg-studio-850 rounded border border-studio-750 space-y-1.5">
            <span className="text-studio-500 uppercase tracking-wider text-[10px] block mb-1 font-semibold">
              T4 16GB Memory Optimizations
            </span>
            <div className="grid grid-cols-2 gap-2 text-studio-300 text-[11px]">
              <div>• FP16 Half-Precision: <span className="text-emerald-400 font-semibold">Active</span></div>
              <div>• Sequential CPU Offloading: <span className="text-emerald-400 font-semibold">Active</span></div>
              <div>• VAE Tiling: <span className="text-emerald-400 font-semibold">Active</span></div>
              <div>• VAE Slicing: <span className="text-emerald-400 font-semibold">Active</span></div>
            </div>
          </div>

          {/* VRAM Clear Action */}
          <div className="pt-2 flex justify-between items-center">
            <span className="text-studio-500 text-[11px]">
              Python {diagnostics?.python_version} • PyTorch {diagnostics?.pytorch_version}
            </span>
            <button
              onClick={onUnloadModels}
              className="px-3 py-1.5 rounded bg-studio-800 hover:bg-studio-700 text-rose-300 border border-studio-700 flex items-center space-x-1.5 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Unload Active Model & Clear VRAM</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
