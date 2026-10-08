import React, { useState, useEffect, useRef } from 'react';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { PreviewPlayer } from './components/PreviewPlayer';
import { GenerationPanel } from './components/GenerationPanel';
import { Timeline } from './components/Timeline';
import { AIDirectorModal } from './components/AIDirectorModal';
import { DiagnosticsModal } from './components/DiagnosticsModal';
import { BenchmarkModal } from './components/BenchmarkModal';
import { JobQueueDrawer } from './components/JobQueueDrawer';
import { apiClient } from './api/client';
import { Project, Scene, Shot, Clip, Job, SystemDiagnostics } from './types';

export function App() {
  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [currentScene, setCurrentScene] = useState<Scene | null>(null);
  const [shots, setShots] = useState<Shot[]>([]);
  const [currentShot, setCurrentShot] = useState<Shot | null>(null);
  const [timelineClips, setTimelineClips] = useState<Clip[]>([]);
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [aiStatus, setAiStatus] = useState<{ ok: boolean; configured: boolean; model?: string; latency_ms?: number; error?: string } | null>(null);
  const [isCheckingAI, setIsCheckingAI] = useState<boolean>(false);

  // Use refs to avoid stale closure in SSE callbacks
  const currentProjectRef = useRef<Project | null>(null);
  const selectedClipRef = useRef<Clip | null>(null);

  useEffect(() => {
    currentProjectRef.current = currentProject;
  }, [currentProject]);

  useEffect(() => {
    selectedClipRef.current = selectedClip;
  }, [selectedClip]);

  // Modals & Drawers
  const [isAIDirectorOpen, setIsAIDirectorOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState(false);
  const [isJobQueueOpen, setIsJobQueueOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const checkAIStatus = async () => {
    setIsCheckingAI(true);
    try {
      const res = await apiClient.getAIStatus();
      setAiStatus(res);
    } catch (e: any) {
      setAiStatus({ ok: false, configured: false, error: e.message });
    } finally {
      setIsCheckingAI(false);
    }
  };

  // 1. Initial Load: Diagnostics, Projects & AI Status Signal
  useEffect(() => {
    loadDiagnostics();
    checkAIStatus();
    loadProjects();
    loadJobs();

    // SSE connection for real-time generation progress (Requirement #41)
    const eventSource = new EventSource('/api/jobs/events/stream');
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'job_progress' || payload.type === 'job_started' || payload.type === 'job_completed' || payload.type === 'job_failed') {
          loadJobs();
          if (currentProjectRef.current) {
            loadTimeline(currentProjectRef.current.id);
          }
        }
      } catch (e) {
        // Ping or format error
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // 2. Project Selection Effect
  useEffect(() => {
    if (currentProject) {
      loadScenes(currentProject.id);
      loadTimeline(currentProject.id);
    }
  }, [currentProject?.id]);

  // 3. Scene Selection Effect
  useEffect(() => {
    if (currentScene) {
      loadShots(currentScene.id);
    }
  }, [currentScene?.id]);

  const loadDiagnostics = async () => {
    try {
      const d = await apiClient.getDiagnostics();
      setDiagnostics(d);
    } catch (e) {
      console.error(e);
    }
  };

  const loadProjects = async () => {
    try {
      const projs = await apiClient.getProjects();
      setProjects(projs);
      if (projs.length > 0 && !currentProject) {
        setCurrentProject(projs[0]);
      } else if (projs.length === 0) {
        // Create initial default project
        const initial = await apiClient.createProject(
          'The Abandoned Factory',
          'A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.',
          'Sci-Fi Mystery'
        );
        setProjects([initial]);
        setCurrentProject(initial);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadScenes = async (projectId: string) => {
    try {
      const scs = await apiClient.getScenes(projectId);
      setScenes(scs);
      if (scs.length > 0) {
        setCurrentScene(scs[0]);
      } else {
        setCurrentScene(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadShots = async (sceneId: string) => {
    try {
      const shts = await apiClient.getShots(sceneId);
      setShots(shts);
      if (shts.length > 0) {
        setCurrentShot(shts[0]);
      } else {
        // Automatically create initial master shot for scene
        await apiClient.breakSceneIntoShots(sceneId);
        const refreshed = await apiClient.getShots(sceneId);
        setShots(refreshed);
        setCurrentShot(refreshed[0] || null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadTimeline = async (projectId: string) => {
    try {
      const clips = await apiClient.getProjectTimeline(projectId);
      setTimelineClips(clips);
      const currentSelectedId = selectedClipRef.current?.id;
      if (clips.length > 0) {
        if (!currentSelectedId) {
          setSelectedClip(clips[0]);
        } else {
          const found = clips.find((c) => c.id === currentSelectedId);
          if (found) setSelectedClip(found);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadJobs = async () => {
    try {
      const jList = await apiClient.getJobs();
      setJobs(jList);
    } catch (e) {
      console.error(e);
    }
  };

  // Handlers
  const handleCreateProject = async (name: string, genre: string) => {
    try {
      const p = await apiClient.createProject(name, '', genre);
      setProjects([p, ...projects]);
      setCurrentProject(p);
    } catch (e: any) {
      alert(`Error creating project: ${e.message}`);
    }
  };

  const handleCreateScene = async (title: string) => {
    if (!currentProject) return;
    try {
      const s = await apiClient.createScene(currentProject.id, title, '');
      setScenes([...scenes, s]);
      setCurrentScene(s);
    } catch (e: any) {
      alert(`Error creating scene: ${e.message}`);
    }
  };

  const handlePlanMovie = async (idea: string, genre: string, numScenes: number = 3) => {
    if (!currentProject) {
      try {
        const newP = await apiClient.createProject(`Movie ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`, idea, genre);
        setCurrentProject(newP);
        await apiClient.planProject(newP.id, idea, genre, numScenes);
        const updatedP = await apiClient.getProject(newP.id);
        setCurrentProject(updatedP);
        await loadScenes(newP.id);
        const freshClips = await apiClient.getProjectTimeline(newP.id);
        setTimelineClips(freshClips);
        if (freshClips.length > 0) setSelectedClip(freshClips[0]);
      } catch (e: any) {
        alert(`AI Director Planning error: ${e.message}`);
      }
      return;
    }
    try {
      await apiClient.planProject(currentProject.id, idea, genre, numScenes);
      const updatedP = await apiClient.getProject(currentProject.id);
      setCurrentProject(updatedP);
      await loadScenes(currentProject.id);
      const freshClips = await apiClient.getProjectTimeline(currentProject.id);
      setTimelineClips(freshClips);
      if (freshClips.length > 0) setSelectedClip(freshClips[0]);
    } catch (e: any) {
      alert(`AI Director Planning error: ${e.message}`);
    }
  };

  const handleEnhancePrompt = async (raw: string) => {
    try {
      const res = await apiClient.enhancePrompt(raw);
      return {
        image: res.enhanced_image_prompt,
        video: res.enhanced_video_prompt
      };
    } catch (e: any) {
      alert(`Prompt enhancement error: ${e.message}`);
      return null;
    }
  };

  // UNIFIED COGVIDEOX-5B VIDEO GENERATOR (Simple Movie Studio)
  const handleGenerateVideo = async (
    clipId?: string,
    steps: number = 25,
    frames: number = 49,
    seed?: number,
    negativePrompt?: string,
    loraPath?: string
  ) => {
    let targetClipId = clipId || selectedClip?.id || (timelineClips.length > 0 ? timelineClips[0].id : undefined);

    if (!targetClipId) {
      alert('Please plan scenes or write a story prompt first to create timeline scenes.');
      return;
    }
    try {
      await apiClient.generateVideo(targetClipId, steps, frames, seed, negativePrompt, loraPath);
      loadJobs();
      setIsJobQueueOpen(true);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Video generation error: ${e.message}`);
    }
  };

  // Clip Approval Workflow (Requirements #29, #30)
  const handleApproveClip = async (clipId: string) => {
    try {
      await apiClient.approveClip(clipId);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Approve error: ${e.message}`);
    }
  };

  const handleRejectClip = async (clipId: string) => {
    try {
      await apiClient.rejectClip(clipId);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Reject error: ${e.message}`);
    }
  };

  const handleRegenerateClip = async (clipId: string) => {
    try {
      await apiClient.regenerateClip(clipId);
      loadJobs();
      setIsJobQueueOpen(true);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Regenerate error: ${e.message}`);
    }
  };

  const handleDeleteClip = async (clipId: string) => {
    try {
      await apiClient.deleteClip(clipId);
      if (selectedClip?.id === clipId) setSelectedClip(null);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Delete error: ${e.message}`);
    }
  };

  const handleMoveClip = async (index: number, direction: 'left' | 'right') => {
    const targetIndex = direction === 'left' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= timelineClips.length) return;

    const reordered = [...timelineClips];
    const [moved] = reordered.splice(index, 1);
    reordered.splice(targetIndex, 0, moved);

    setTimelineClips(reordered);
    try {
      await apiClient.reorderTimeline(reordered.map((c) => c.id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleUploadReference = async (clipId: string, file: File) => {
    try {
      await apiClient.uploadReferenceImage(clipId, file);
      if (currentProject) loadTimeline(currentProject.id);
    } catch (e: any) {
      alert(`Reference upload error: ${e.message}`);
    }
  };

  const handleExportMovie = async () => {
    if (!currentProject) return;
    setIsExporting(true);
    try {
      const res = await apiClient.exportMovie(currentProject.id, '720p', 24);
      alert(`Movie successfully assembled with FFmpeg!\nSaved to: ${res.output_path}\nClips combined: ${res.clips_count}`);
    } catch (e: any) {
      alert(`Export error: ${e.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const activeJobsCount = jobs.filter((j) => j.status === 'Running' || j.status === 'Waiting').length;

  return (
    <div className="min-h-screen bg-studio-950 text-white flex flex-col font-sans select-none">
      {/* Top Bar */}
      <TopBar
        currentProject={currentProject}
        diagnostics={diagnostics}
        activeJobsCount={activeJobsCount}
        aiStatus={aiStatus}
        onCheckAIStatus={checkAIStatus}
        isCheckingAI={isCheckingAI}
        onOpenAIDirector={() => setIsAIDirectorOpen(true)}
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
        onOpenBenchmark={() => setIsBenchmarkOpen(true)}
        onOpenJobQueue={() => setIsJobQueueOpen(true)}
        onExportMovie={handleExportMovie}
        isExporting={isExporting}
      />

      {/* Main Studio Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          projects={projects}
          currentProject={currentProject}
          scenes={scenes}
          currentScene={currentScene}
          onSelectProject={setCurrentProject}
          onCreateProject={handleCreateProject}
          onSelectScene={setCurrentScene}
          onCreateScene={handleCreateScene}
          onOpenCharacters={() => setIsAIDirectorOpen(true)}
          onOpenLocations={() => setIsAIDirectorOpen(true)}
        />

        {/* Center Cinema Viewport */}
        <PreviewPlayer
          clip={selectedClip}
          onApprove={handleApproveClip}
          onReject={handleRejectClip}
          onRegenerate={handleRegenerateClip}
          onUploadReference={handleUploadReference}
        />

        {/* Right AI Prompt & CogVideoX-5B Generation Panel */}
        <GenerationPanel
          currentScene={currentScene}
          currentShot={currentShot}
          selectedClip={selectedClip}
          timelineClips={timelineClips}
          aiStatus={aiStatus}
          onCheckAIStatus={checkAIStatus}
          isCheckingAI={isCheckingAI}
          onPlanMovieStory={(prompt, numScenes) => handlePlanMovie(prompt, currentProject?.genre || 'Cinematic', numScenes)}
          onGenerateVideo={handleGenerateVideo}
          onEnhancePrompt={handleEnhancePrompt}
          isGenerating={activeJobsCount > 0}
        />
      </div>

      {/* Bottom Timeline */}
      <Timeline
        clips={timelineClips}
        selectedClip={selectedClip}
        onSelectClip={setSelectedClip}
        onMoveClip={handleMoveClip}
        onDeleteClip={handleDeleteClip}
        onApproveClip={handleApproveClip}
        onRejectClip={handleRejectClip}
        onRegenerateClip={handleRegenerateClip}
      />

      {/* Modals & Drawers */}
      <AIDirectorModal
        isOpen={isAIDirectorOpen}
        onClose={() => setIsAIDirectorOpen(false)}
        project={currentProject}
        currentScene={currentScene}
        aiStatus={aiStatus}
        onCheckAIStatus={checkAIStatus}
        isCheckingAI={isCheckingAI}
        onPlanMovie={handlePlanMovie}
        onCheckContinuity={(sId) => apiClient.checkContinuity(sId)}
      />

      <DiagnosticsModal
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
        diagnostics={diagnostics}
        onUnloadModels={async () => {
          await apiClient.unloadModels();
          loadDiagnostics();
        }}
      />

      <BenchmarkModal
        isOpen={isBenchmarkOpen}
        onClose={() => setIsBenchmarkOpen(false)}
      />

      <JobQueueDrawer
        isOpen={isJobQueueOpen}
        onClose={() => setIsJobQueueOpen(false)}
        jobs={jobs}
        onCancelJob={async (jId) => {
          await apiClient.cancelJob(jId);
          loadJobs();
        }}
        onRetryJob={async (jId, lowVram) => {
          await apiClient.retryJob(jId, lowVram);
          loadJobs();
        }}
      />
    </div>
  );
}

export default App;
