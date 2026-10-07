import { Project, Scene, Shot, Clip, Job, SystemDiagnostics, BenchmarkRecord } from '../types';

const API_BASE = '/api';

export const apiClient = {
  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async createProject(name: string, description: string = '', genre: string = 'Cinematic'): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, genre })
    });
    if (!res.ok) throw new Error('Failed to create project');
    return res.json();
  },

  async getProject(id: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  async planProject(id: string, idea: string, genre: string = 'Cinematic'): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${id}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idea, genre })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to plan project');
    }
    return res.json();
  },

  async exportMovie(projectId: string, resolution: string = '720p', fps: number = 24): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution, fps, include_only_approved: true })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Export failed');
    }
    return res.json();
  },

  // Scenes & Shots
  async getScenes(projectId: string): Promise<Scene[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/scenes`);
    if (!res.ok) throw new Error('Failed to fetch scenes');
    return res.json();
  },

  async createScene(projectId: string, title: string, description: string): Promise<Scene> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/scenes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, scene_number: 1 })
    });
    if (!res.ok) throw new Error('Failed to create scene');
    return res.json();
  },

  async breakSceneIntoShots(sceneId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/scenes/${sceneId}/break-into-shots`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to break scene into shots');
    return res.json();
  },

  async getShots(sceneId: string): Promise<Shot[]> {
    const res = await fetch(`${API_BASE}/scenes/${sceneId}/shots`);
    if (!res.ok) throw new Error('Failed to fetch shots');
    return res.json();
  },

  async breakShotIntoClips(shotId: string, prompt: string, clipCount: number, duration: number = 5.0): Promise<any> {
    const res = await fetch(`${API_BASE}/shots/${shotId}/break-into-clips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, clip_count: clipCount, duration_per_clip: duration })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to break into clips');
    }
    return res.json();
  },

  // Clips & Timeline
  async getProjectTimeline(projectId: string): Promise<Clip[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  },

  async generatePreview(
    clipId: string,
    steps: number = 25,
    frames: number = 49,
    seed?: number,
    negative_prompt?: string,
    lora_path?: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps, frames, seed, negative_prompt, lora_path })
    });
    if (!res.ok) throw new Error('Failed to queue preview generation');
    return res.json();
  },

  async generateFinal(
    clipId: string,
    steps: number = 30,
    frames: number = 49,
    seed?: number,
    negative_prompt?: string,
    lora_path?: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/final`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps, frames, seed, negative_prompt, lora_path })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to queue final generation');
    }
    return res.json();
  },

  async approveClip(clipId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/approve`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to approve clip');
    return res.json();
  },

  async rejectClip(clipId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/reject`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reject clip');
    return res.json();
  },

  async regenerateClip(clipId: string, instructions?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instructions })
    });
    if (!res.ok) throw new Error('Failed to regenerate clip');
    return res.json();
  },

  async updateClip(clipId: string, data: Partial<Clip>): Promise<Clip> {
    const res = await fetch(`${API_BASE}/clips/${clipId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to update clip');
    return res.json();
  },

  async deleteClip(clipId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/${clipId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete clip');
    return res.json();
  },

  async reorderTimeline(clipIds: string[]): Promise<any> {
    const res = await fetch(`${API_BASE}/clips/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: clipIds })
    });
    if (!res.ok) throw new Error('Failed to reorder timeline');
    return res.json();
  },

  async uploadReferenceImage(clipId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/clips/${clipId}/upload-reference`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload reference image');
    return res.json();
  },

  // AI tools
  async enhancePrompt(prompt: string, promptType: string = 'both', sceneContext: string = ''): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/enhance-prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, prompt_type: promptType, scene_context: sceneContext })
    });
    if (!res.ok) throw new Error('Failed to enhance prompt');
    return res.json();
  },

  async checkContinuity(sceneId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/scenes/${sceneId}/check-continuity`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to check continuity');
    return res.json();
  },

  // Jobs
  async getJobs(projectId?: string): Promise<Job[]> {
    const url = projectId ? `${API_BASE}/jobs?project_id=${projectId}` : `${API_BASE}/jobs`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch jobs');
    return res.json();
  },

  async cancelJob(jobId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to cancel job');
    return res.json();
  },

  async retryJob(jobId: string, lowVram: boolean = false): Promise<any> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/retry?low_vram=${lowVram}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to retry job');
    return res.json();
  },

  // System Diagnostics & Benchmark
  async getDiagnostics(): Promise<SystemDiagnostics> {
    const res = await fetch(`${API_BASE}/system/diagnostics`);
    if (!res.ok) throw new Error('Failed to fetch system diagnostics');
    return res.json();
  },

  async getModelStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/system/models`);
    if (!res.ok) throw new Error('Failed to fetch model status');
    return res.json();
  },

  async unloadModels(): Promise<any> {
    const res = await fetch(`${API_BASE}/system/models/unload`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to unload models');
    return res.json();
  },

  async runBenchmark(model: string, resolution: string, frames: number, steps: number): Promise<BenchmarkRecord> {
    const res = await fetch(`${API_BASE}/system/benchmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, resolution, frames, steps })
    });
    if (!res.ok) throw new Error('Failed to execute benchmark');
    return res.json();
  },

  async getBenchmarks(): Promise<BenchmarkRecord[]> {
    const res = await fetch(`${API_BASE}/system/benchmarks`);
    if (!res.ok) throw new Error('Failed to fetch benchmarks');
    return res.json();
  }
};
