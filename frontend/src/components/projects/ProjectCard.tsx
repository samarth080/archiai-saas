import { Project } from '../../services/project.service'

interface ProjectCardProps {
  project: Project
  onClick: () => void
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  return (
    <button
      onClick={onClick}
      className="text-left w-full bg-white border border-gray-200 rounded-lg p-4 hover:border-indigo-400 hover:shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      <h3 className="font-semibold text-gray-900 truncate mb-1">{project.title}</h3>
      <p className="text-sm text-gray-500 truncate mb-3">
        {project.description ?? 'No description'}
      </p>
      <p className="text-xs text-gray-400">Created {formatDate(project.created_at)}</p>
    </button>
  )
}
