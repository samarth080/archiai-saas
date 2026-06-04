import { Link } from 'react-router-dom'

import { Button } from '../../components/ui/Button'

export default function Landing() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-6 text-center">
      <h1 className="mb-2 text-4xl font-bold text-gray-900">ArchiAI</h1>
      <p className="mb-8 max-w-xl text-gray-600">
        Create, edit, save, export, and share rule-guided architectural concept layouts.
      </p>
      <div className="flex gap-4">
        <Link to="/register">
          <Button>Get Started</Button>
        </Link>
        <Link to="/login">
          <Button variant="secondary">Log In</Button>
        </Link>
      </div>
    </main>
  )
}
