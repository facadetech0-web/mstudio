export interface CharacterBibleItem {
  name: string;
  age?: string;
  gender?: string;
  physical_description?: string;
  face_description?: string;
  hair?: string;
  clothing?: string;
  body_type?: string;
  personality?: string;
  movement_style?: string;
  voice_description?: string;
  continuity_rules?: string;
}

export interface LocationBibleItem {
  name: string;
  description?: string;
  architecture?: string;
  interior_exterior?: string;
  lighting?: string;
  time?: string;
  weather?: string;
  color_mood?: string;
  important_objects?: string;
  continuity_rules?: string;
}

export interface MovieBible {
  title: string;
  genre: string;
  story: string;
  synopsis: string;
  visual_style: string;
  color_palette: string;
  mood: string;
  camera_style: string;
  lighting_style: string;
  time_period: string;
  weather: string;
  characters: CharacterBibleItem[];
  locations: LocationBibleItem[];
  props: string[];
  continuity_rules: string[];
  negative_rules: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  genre: string;
  visual_style: string;
  movie_bible: Partial<MovieBible>;
  created_at: string;
  updated_at: string;
}

export interface Scene {
  id: string;
  project_id: string;
  scene_number: number;
  title: string;
  description: string;
  location_id?: string;
  location_name?: string;
  characters: string[];
  time_of_day: string;
  weather: string;
  visual_style?: string;
  created_at: string;
}

export interface Shot {
  id: string;
  scene_id: string;
  shot_number: number;
  description: string;
  reference_image?: string;
  image_prompt?: string;
  video_prompt?: string;
  camera_motion: string;
  subject_motion: string;
  duration: number;
  clip_count: number;
  status: string;
}

export interface Clip {
  id: string;
  shot_id: string;
  scene_id: string;
  project_id: string;
  clip_number: number;
  timeline_order: number;
  description: string;
  reference_image?: string;
  image_prompt?: string;
  video_prompt?: string;
  negative_prompt?: string;
  lora_path?: string;
  camera_motion?: string;
  subject_motion?: string;
  duration: number;
  continuity_from_previous?: string;
  continuity_to_next?: string;
  preview_status: 'Draft' | 'Queued' | 'Generating' | 'Ready' | 'Approved' | 'Rejected' | 'Error';
  final_status: 'Draft' | 'Queued' | 'Generating' | 'Ready' | 'Error';
  preview_file?: string;
  final_file?: string;
  seed?: number;
  prompt_history: Array<{ version: number; video?: string; image?: string }>;
}

export interface Job {
  id: string;
  project_id: string;
  scene_id?: string;
  shot_id?: string;
  clip_id?: string;
  mode: 'preview' | 'final' | 'benchmark';
  model: string;
  status: 'Waiting' | 'Running' | 'Completed' | 'Failed' | 'Cancelled';
  progress: number;
  steps_completed: number;
  total_steps: number;
  seed?: number;
  resolution: string;
  frames: number;
  steps: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  generation_time?: number;
  peak_vram?: number;
  output_path?: string;
  error?: string;
}

export interface SystemDiagnostics {
  python_version: string;
  pytorch_version: string;
  cuda_available: boolean;
  gpu_name?: string;
  gpu_total_vram_gb?: number;
  gpu_free_vram_gb?: number;
  ffmpeg_available: boolean;
  sqlite_available: boolean;
  openrouter_configured: boolean;
  openrouter_model: string;
  models_status: Record<string, boolean>;
  t4_recommended_settings: Record<string, any>;
}

export interface BenchmarkRecord {
  id: string;
  model: string;
  resolution: string;
  frames: number;
  steps: number;
  generation_time: number;
  peak_vram: number;
  success: boolean;
  error?: string;
  created_at: string;
}
