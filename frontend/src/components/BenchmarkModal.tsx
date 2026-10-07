import React, { useState, useEffect } from 'react';
import { X, Activity, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { BenchmarkRecord } from '../types';
import { apiClient } from '../api/client';

interface BenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({ isOpen, onClose }) => {
  const [model, setModel] = useState('cogvideox-2b');
  const [steps, setSteps] = useState(15);
  const [frames, setFrames] = useState(49);
  const [isRunning, setIsRunning] = useState(false);
  const [records, setRecords] = useState<BenchmarkRecord[]>([]);
  const [currentResult, setCurrentResult] = useState<BenchmarkRecord | null>(null);

  useEffect(() => {
    if (isOpen) {
      apiClient.getBenchmarks().then(setRecords).catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleRun = async () => {
    setIsRunning(true);
    setCurrentResult(null);
    try {
      const res = await apiClient.runBenchmark(model, '720x480', frames, steps);
      setCurrentResult(res);
      setRecords((prev) => [res, ...prev]);
    } catch (e: any) {
      alert(`Benchmark execution failed: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-6">
      <div className="bg-studio-900 border border-studio-700 rounded-xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col h-[75vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-studio-800 flex items-center justify-between bg-studio-950">
          <div className="flex items-center space-x-2.5">
            <Activity className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Hardware Benchmark Mode
              </h3>
              <p className="text-[11px] text-studio-400">
                Executes genuine generation passes to measure actual latency and peak VRAM.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-studio-800 text-studio-400 hover:text-white rounded">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 overflow-y-auto space-y-5 text-xs">
          {/* Config Controls */}
          <div className="p-4 bg-studio-850 rounded-lg border border-studio-750 flex items-end space-x-3">
            <div className="flex-1">
              <label className="text-studio-400 block mb-1">Model Target</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2.5 py-1.5"
              >
                <option value="cogvideox-2b">CogVideoX-2B (Preview)</option>
                <option value="cogvideox-5b-i2v">CogVideoX-5B-I2V (Final)</option>
              </select>
            </div>

            <div className="w-28">
              <label className="text-studio-400 block mb-1">Steps ({steps})</label>
              <input
                type="number"
                min={10}
                max={50}
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value, 10))}
                className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2.5 py-1.5"
              />
            </div>

            <div className="w-32">
              <label className="text-studio-400 block mb-1">Frames</label>
              <select
                value={frames}
                onChange={(e) => setFrames(parseInt(e.target.value, 10))}
                className="w-full bg-studio-900 border border-studio-700 text-white rounded px-2.5 py-1.5"
              >
                <option value={49}>49 frames</option>
                <option value={81}>81 frames</option>
              </select>
            </div>

            <button
              onClick={handleRun}
              disabled={isRunning}
              className="px-4 py-2 bg-studio-gold hover:bg-amber-400 disabled:opacity-50 text-studio-950 font-bold uppercase tracking-wider rounded flex items-center space-x-1.5 transition"
            >
              <Play className="w-3.5 h-3.5 fill-studio-950" />
              <span>{isRunning ? 'Measuring...' : 'Run Benchmark'}</span>
            </button>
          </div>

          {/* Current Run Highlight */}
          {currentResult && (
            <div className="p-4 bg-emerald-950/40 border border-emerald-800/80 rounded-lg">
              <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider block mb-1">
                Latest Benchmark Result
              </span>
              <div className="grid grid-cols-4 gap-3 text-white">
                <div>
                  <span className="text-studio-500 block">Model:</span>
                  <span className="font-medium">{currentResult.model}</span>
                </div>
                <div>
                  <span className="text-studio-500 block">Generation Time:</span>
                  <span className="font-mono text-emerald-400 font-bold">{currentResult.generation_time}s</span>
                </div>
                <div>
                  <span className="text-studio-500 block">Peak VRAM:</span>
                  <span className="font-mono text-emerald-400 font-bold">{currentResult.peak_vram} MB</span>
                </div>
                <div>
                  <span className="text-studio-500 block">Status:</span>
                  <span className={currentResult.success ? 'text-emerald-400' : 'text-rose-400'}>
                    {currentResult.success ? 'Success' : 'Failed'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Historical Benchmarks Table */}
          <div>
            <h4 className="text-xs font-semibold text-studio-400 uppercase tracking-wider mb-2">
              Measured Performance History (Real Runs Only)
            </h4>
            <div className="border border-studio-800 rounded-lg overflow-hidden bg-studio-850">
              <table className="w-full text-left text-xs">
                <thead className="bg-studio-900 text-studio-500 border-b border-studio-800">
                  <tr>
                    <th className="p-2.5">Model</th>
                    <th className="p-2.5">Steps</th>
                    <th className="p-2.5">Frames</th>
                    <th className="p-2.5">Gen Time</th>
                    <th className="p-2.5">Peak VRAM</th>
                    <th className="p-2.5">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-studio-800 text-studio-300">
                  {records.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-studio-500">
                        No benchmark runs recorded yet. Click "Run Benchmark" above.
                      </td>
                    </tr>
                  ) : (
                    records.map((r) => (
                      <tr key={r.id} className="hover:bg-studio-800/50">
                        <td className="p-2.5 font-medium text-white">{r.model}</td>
                        <td className="p-2.5 font-mono">{r.steps}</td>
                        <td className="p-2.5 font-mono">{r.frames}</td>
                        <td className="p-2.5 font-mono text-amber-400">{r.generation_time}s</td>
                        <td className="p-2.5 font-mono">{r.peak_vram ? `${r.peak_vram} MB` : 'N/A'}</td>
                        <td className="p-2.5">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                            r.success ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
                          }`}>
                            {r.success ? 'OK' : 'FAIL'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
