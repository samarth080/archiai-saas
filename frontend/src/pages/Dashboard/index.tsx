import { Button } from '../../components/ui/Button'
import { useAuth } from '../../hooks/useAuth'

export default function Dashboard() {
  const { user, logOut } = useAuth()

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">ArchiAI</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
          <Button variant="secondary" onClick={logOut}>
            Logout
          </Button>
        </div>
      </header>
      <section className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Projects</h2>
        <p className="text-gray-500">
          No projects yet. Start a new design brief to get started.
        </p>
      </section>
    </main>
  )
}
