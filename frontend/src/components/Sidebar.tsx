import React, { useState } from 'react';
import { Layers, Plus, Clapperboard, Folder, Users, MapPin, ChevronRight } from 'lucide-react';
import { Project, Scene } from '../types';

interface SidebarProps {
  projects: Project[];
  currentProject: Project | null;
  scenes: Scene[];
  currentScene: Scene | null;
  onSelectProject: (p: Project) => void;
  onCreateProject: (name: string, genre: string) => void;
  onSelectScene: (s: Scene) => void;
  onCreateScene: (title: string) => void;
  onOpenCharacters: () => void;
  onOpenLocations: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  projects,
  currentProject,
  scenes,
  currentScene,
  onSelectProject,
  onCreateProject,
  onSelectScene,
  onCreateScene,
  onOpenCharacters,
  onOpenLocations
}) => {
  const [showNewProjModal, setShowNewProjModal] = useState(false);
  const [newProjName, setNewProjName] = useState('');
  const [newProjGenre, setNewProjGenre] = useState('Cinematic');

  const handleCreateProj = (e: React.FormEvent) => {
    e.preventDefault();
    if (newProjName.trim()) {
      onCreateProject(newProjName.trim(), newProjGenre);
      setNewProjName('');
      setShowNewProjModal(false);
    }
  };

  return (
    <aside className="w-64 bg-studio-900 border-r border-studio-800 flex flex-col h-[calc(100vh-3.5rem)] select-none">
      {/* Projects Dropdown / Header */}
      <div className="p-3 border-b border-studio-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] uppercase tracking-wider text-studio-500 font-semibold flex items-center space-x-1.5">
            <Folder className="w-3.5 h-3.5" />
            <span>Projects</span>
          </span>
          <button
            onClick={() => setShowNewProjModal(true)}
            className="p-1 hover:bg-studio-800 text-studio-400 hover:text-white rounded transition"
            title="Create New Project"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <select
          value={currentProject?.id || ''}
          onChange={(e) => {
            const found = projects.find(p => p.id === e.target.value);
            if (found) onSelectProject(found);
          }}
          className="w-full bg-studio-850 border border-studio-700 text-xs text-white rounded px-2.5 py-1.5 focus:outline-none focus:border-studio-gold"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Libraries Quick Navigation */}
      <div className="p-3 border-b border-studio-800 grid grid-cols-2 gap-2">
        <button
          onClick={onOpenCharacters}
          className="flex items-center justify-center space-x-1.5 py-2 px-2 rounded bg-studio-850 hover:bg-studio-800 border border-studio-800 text-xs text-studio-300 hover:text-white transition"
        >
          <Users className="w-3.5 h-3.5 text-studio-accent" />
          <span>Characters</span>
        </button>
        <button
          onClick={onOpenLocations}
          className="flex items-center justify-center space-x-1.5 py-2 px-2 rounded bg-studio-850 hover:bg-studio-800 border border-studio-800 text-xs text-studio-300 hover:text-white transition"
        >
          <MapPin className="w-3.5 h-3.5 text-studio-gold" />
          <span>Locations</span>
        </button>
      </div>

      {/* Scenes Navigation Tree */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] uppercase tracking-wider text-studio-500 font-semibold flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5" />
            <span>Scenes ({scenes.length})</span>
          </span>
          <button
            onClick={() => onCreateScene(`Scene ${scenes.length + 1}`)}
            className="p-1 hover:bg-studio-800 text-studio-400 hover:text-white rounded transition"
            title="Add Scene"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-1">
          {scenes.length === 0 ? (
            <div className="text-center py-6 text-xs text-studio-500">
              No scenes yet.<br />Click AI Director to plan story or add a scene.
            </div>
          ) : (
            scenes.map((s) => {
              const isSelected = currentScene?.id === s.id;
              return (
                <div
                  key={s.id}
                  onClick={() => onSelectScene(s)}
                  className={`p-2 rounded text-xs cursor-pointer transition flex items-start justify-between ${
                    isSelected
                      ? 'bg-studio-800 border border-studio-gold/60 text-white font-medium'
                      : 'hover:bg-studio-850 text-studio-300 border border-transparent'
                  }`}
                >
                  <div className="flex items-start space-x-2 truncate">
                    <Clapperboard className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isSelected ? 'text-studio-gold' : 'text-studio-500'}`} />
                    <div className="truncate">
                      <div className="truncate font-medium">
                        Scene {s.scene_number}: {s.title}
                      </div>
                      {s.location_name && (
                        <div className="text-[10px] text-studio-500 truncate">
                          {s.location_name} • {s.time_of_day}
                        </div>
                      )}
                    </div>
                  </div>
                  {isSelected && <ChevronRight className="w-3.5 h-3.5 text-studio-gold shrink-0 mt-0.5" />}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* New Project Modal */}
      {showNewProjModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-studio-900 border border-studio-700 rounded-lg p-5 w-full max-w-sm shadow-2xl">
            <h3 className="text-sm font-semibold text-white mb-3">Create New Movie Project</h3>
            <form onSubmit={handleCreateProj} className="space-y-3">
              <div>
                <label className="text-xs text-studio-400 block mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. The Forgotten City"
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  className="w-full bg-studio-850 border border-studio-700 text-xs rounded px-2.5 py-2 text-white focus:outline-none focus:border-studio-gold"
                />
              </div>
              <div>
                <label className="text-xs text-studio-400 block mb-1">Genre</label>
                <input
                  type="text"
                  value={newProjGenre}
                  onChange={(e) => setNewProjGenre(e.target.value)}
                  className="w-full bg-studio-850 border border-studio-700 text-xs rounded px-2.5 py-2 text-white focus:outline-none focus:border-studio-gold"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewProjModal(false)}
                  className="px-3 py-1.5 text-xs text-studio-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 text-xs bg-studio-gold text-studio-950 font-semibold rounded hover:bg-amber-400"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
};
