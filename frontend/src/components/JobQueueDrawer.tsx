import React from 'react';
import { X, Play, Square, RotateCcw, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { Job } from '../types';

interface JobQueueDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  jobs: Job[];
  onCancelJob: (jobId: string) => void;
  onRetryJob: (jobId: string, lowVram?: boolean) => void;
}

export const JobQueueDrawer: React.FC<JobQueueDrawerProps> = ({
  isOpen,
  onClose,
  jobs,
  onCancelJob,
  onRetryJob
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-studio-900 border-l border-studio-800 shadow-2xl z-50 flex flex-col select-none">
      {/* Header */}
      <div className="h-14 px-4 border-b border-studio-800 flex items-center justify-between bg-studio-950">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-studio-accent" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Generation Job Queue
          </h3>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-studio-800 text-studio-400 hover:text-white rounded">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Jobs List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
        {jobs.length === 0 ? (
          <div className="text-center py-12 text-studio-500">
            No background generation jobs active or queued.
          </div>
        ) : (
          jobs.map((job) => {
            const isRunning = job.status === 'Running';
            const isWaiting = job.status === 'Waiting';
            const isFailed = job.status === 'Failed';
            const isCompleted = job.status === 'Completed';

            return (
              <div
                key={job.id}
                className="p-3 bg-studio-850 rounded-lg border border-studio-750 space-y-2"
              >
                {/* Job Header */}
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white uppercase tracking-wider text-[11px]">
                    {job.mode} Mode • {job.model}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    isRunning ? 'bg-amber-950 text-amber-400 border border-amber-800 animate-pulse' :
                    isWaiting ? 'bg-studio-800 text-studio-400' :
                    isCompleted ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                    'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}>
                    {job.status}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-studio-900 rounded-full h-2 overflow-hidden border border-studio-800">
                  <div
                    className={`h-full transition-all duration-300 ${
                      isCompleted ? 'bg-emerald-500' : isFailed ? 'bg-rose-500' : 'bg-studio-gold'
                    }`}
                    style={{ width: `${job.progress}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-studio-400 font-mono">
                  <span>
                    {isRunning
                      ? `Step ${job.steps_completed}/${job.total_steps} (${job.progress}%)`
                      : `${job.progress}%`}
                  </span>
                  {job.generation_time && (
                    <span>{job.generation_time}s</span>
                  )}
                </div>

                {/* Error Banner with Low VRAM Suggestion */}
                {isFailed && (
                  <div className="p-2 bg-rose-950/60 rounded border border-rose-800/80 text-[11px] text-rose-200">
                    <p className="font-semibold">Error: {job.error}</p>
                    <div className="mt-2 flex space-x-2">
                      <button
                        onClick={() => onRetryJob(job.id, false)}
                        className="px-2 py-1 bg-studio-800 hover:bg-studio-700 text-white rounded text-[10px] font-medium"
                      >
                        Retry
                      </button>
                      <button
                        onClick={() => onRetryJob(job.id, true)}
                        className="px-2 py-1 bg-amber-900 hover:bg-amber-800 text-amber-200 rounded text-[10px] font-bold"
                      >
                        Retry in Low VRAM Mode
                      </button>
                    </div>
                  </div>
                )}

                {/* Actions */}
                {(isRunning || isWaiting) && (
                  <div className="pt-1 flex justify-end">
                    <button
                      onClick={() => onCancelJob(job.id)}
                      className="px-2.5 py-1 bg-studio-800 hover:bg-studio-700 text-rose-300 rounded text-[11px] flex items-center space-x-1"
                    >
                      <Square className="w-3 h-3" />
                      <span>Cancel Job</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
